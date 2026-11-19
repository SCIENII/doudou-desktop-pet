from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class ExampleFrame:
    path: Path
    ms: int


@dataclass(frozen=True)
class ExampleSkin:
    id: str
    name: str
    idle: Path
    interact: tuple[ExampleFrame, ...]
    bubble: str


@pytest.fixture(scope="session")
def app():
    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    return application


@pytest.fixture
def skins(tmp_path, app):
    examples = {}
    for key, rgb in (("plain", 0xAA5432), ("alternate", 0x228877)):
        paths = []
        for index in range(3):
            path = tmp_path / f"{key}-{index}.png"
            image = QImage(16, 16, QImage.Format.Format_ARGB32)
            image.fill(0)
            for y in range(2, 14):
                for x in range(2, 14):
                    image.setPixel(x, y, 0xFF000000 | (rgb if x < 8 else rgb + index + 1))
            assert image.save(str(path))
            paths.append(path)
        examples[key] = ExampleSkin(key, key.title(), paths[0], (
            ExampleFrame(paths[1], 120), ExampleFrame(paths[2], 180),
        ), f"Hello {key}!")
    return examples


@pytest.fixture
def make_window(skins):
    windows = []

    def make(settings=None, on_change=None):
        assert importlib.util.find_spec("doudou_pet.window"), "PetWindow is not implemented"
        from doudou_pet.window import PetWindow

        window = PetWindow(skins, settings or {}, on_change=on_change)
        windows.append(window)
        window.show()
        QApplication.processEvents()
        return window

    yield make

    for window in windows:
        window.close()
        window.deleteLater()
    QApplication.processEvents()


def test_window_flags_and_nearest_neighbor_rendering(make_window):
    window = make_window()
    flags = window.windowFlags()
    assert flags & Qt.WindowType.FramelessWindowHint
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert window.windowType() == Qt.WindowType.Tool
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    image = window.grab().toImage()
    assert image.pixelColor(0, 0).alpha() == 0
    row = {image.pixelColor(x, image.height() // 2).rgba() for x in range(image.width())}
    assert row == {0, 0xFFAA5432, 0xFFAA5433}


def wait_for(predicate, timeout=800):
    for _ in range(timeout // 10):
        if predicate():
            return True
        QTest.qWait(10)
    return predicate()


def test_click_plays_ordered_frames_and_clears_bubble(make_window):
    window = make_window()
    first, second = window.skin.interact
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=window.rect().center())
    assert window.frame_path == first.path
    assert window.bubble.isVisible()
    assert window.bubble.text() == window.skin.bubble
    assert wait_for(lambda: window.frame_path == second.path, 800)
    assert wait_for(lambda: window.frame_path == window.skin.idle, 800)
    assert window.bubble.isVisible(), "The bubble should remain long enough to read"
    assert wait_for(lambda: not window.bubble.isVisible(), 2000)


def test_drag_moves_without_click_and_persists(make_window):
    changes = []
    window = make_window({"position": [40, 40]}, changes.append)
    start = window.pos()
    center = window.rect().center()
    offset = QPoint(26, 19)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=center)
    QTest.mouseMove(window, center + offset)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=center)
    assert window.pos() == start + offset
    assert changes[-1]["position"] == [window.x(), window.y()]
    assert window.frame_path == window.skin.idle
    assert not window.bubble.isVisible()


def test_restored_position_is_clamped_to_available_screen(make_window, app):
    window = make_window({"position": [999999, -999999]})
    assert app.primaryScreen().availableGeometry().contains(window.frameGeometry())


def test_right_click_wardrobe_selects_and_persists_skin(make_window):
    changes = []
    window = make_window({"skin": "plain"}, changes.append)
    QTest.mouseClick(window, Qt.MouseButton.RightButton, pos=window.rect().center())
    assert window.pet_menu.isVisible()
    actions = window.wardrobe.actions()
    assert [action.text() for action in actions] == ["Plain", "Alternate"]
    assert actions[0].isChecked()
    actions[1].trigger()
    assert window.skin.id == "alternate"
    assert window.frame_path == window.skin.idle
    assert changes[-1]["skin"] == "alternate"
    window.pet_menu.hide()


def test_switch_skin_during_interaction_stops_old_frames(make_window):
    window = make_window({"skin": "plain"})
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=window.rect().center())
    window.wardrobe.actions()[1].trigger()
    QTest.qWait(320)
    assert window.skin.id == "alternate"
    assert window.frame_path == window.skin.idle
    assert not window.bubble.isVisible()


def test_tray_actions_hide_show_relocate_and_toggle_top(make_window, app):
    changes = []
    window = make_window({"position": [20, 20]}, changes.append)
    window.visibility_action.trigger()
    assert not window.isVisible()
    window.visibility_action.trigger()
    assert window.isVisible()
    start = window.pos()
    window.relocate_action.trigger()
    assert window.pos() != start
    assert app.primaryScreen().availableGeometry().contains(window.frameGeometry())
    window.top_action.trigger()
    assert not window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    assert window.isVisible()
    assert changes[-1]["always_on_top"] is False


def test_hidden_pet_stays_hidden_when_top_setting_changes(make_window):
    window = make_window()
    window.visibility_action.trigger()
    window.top_action.trigger()
    assert not window.isVisible()


def test_tray_exit_closes_pet(make_window):
    window = make_window()
    window.exit_action.trigger()
    assert not window.isVisible()
    assert not window.tray.isVisible()


def test_smoke_reports_invalid_skin_count(tmp_path):
    output = tmp_path / "smoke.json"
    result = subprocess.run(
        [sys.executable, "-m", "doudou_pet", "--smoke-test", "--smoke-output",
         str(output), "--assets-dir", str(tmp_path)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True, text=True, timeout=15,
    )
    assert output.exists(), f"Smoke mode did not produce JSON: {result.stderr}"
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert data["ok"] is False
    assert data["skin_count"] == 0
    assert data["window_visible"] is False


def test_smoke_loads_and_shows_bundled_skins(tmp_path):
    root = Path(__file__).resolve().parents[1] / "doudou_pet" / "assets" / "skins"
    if not root.is_dir():
        pytest.skip("Bundled skins have not been generated")
    output = tmp_path / "smoke.json"
    result = subprocess.run(
        [sys.executable, "-m", "doudou_pet", "--smoke-test", "--smoke-output", str(output)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True, text=True, timeout=15,
    )
    assert output.exists(), f"Smoke mode did not produce JSON: {result.stderr}"
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 0, data
    assert data["ok"] is True
    assert data["skin_count"] == len(set(data["skin_ids"])) == 4
    assert data["window_visible"] is True

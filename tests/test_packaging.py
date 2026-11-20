"""Contracts for the portable-bundle filter used by packaging/doudou-pet.spec."""
import importlib.util
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
FILTER = PROJECT / "packaging" / "binary_filter.py"


def load_filter():
    spec = importlib.util.spec_from_file_location("doudou_binary_filter", FILTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def keep():
    assert FILTER.is_file(), "The bundle filter moved; update packaging/doudou-pet.spec too"
    return load_filter().keep


@pytest.mark.parametrize("name", ["MSVCP140.dll", "msvcp140_1.dll", "VCRUNTIME140.dll",
                                  "vcruntime140_1.dll", "MSVCP140_codecvt_ids.dll"])
def test_msvc_runtime_is_always_bundled(keep, name):
    # Qt6 and PySide6 link against these; Windows does not ship them.
    assert keep(f"DoudouPet/_internal/PySide6/{name}") is True
    assert keep(f"DoudouPet/_internal/shiboken6/{name}".replace("/", "\\")) is True


@pytest.mark.parametrize("name", ["ucrtbase.dll", "api-ms-win-crt-runtime-l1-1-0.dll",
                                  "libcrypto-3-x64.dll", "libssl-3-x64.dll"])
def test_os_components_and_tls_are_dropped(keep, name):
    assert keep(f"DoudouPet/_internal/{name}") is False


@pytest.mark.parametrize("name", ["opengl32sw.dll", "Qt6Network.dll", "Qt6Svg.dll"])
def test_unused_qt_modules_are_dropped(keep, name):
    assert keep(f"DoudouPet/_internal/PySide6/{name}") is False


def test_only_the_needed_qt_plugins_survive(keep):
    assert keep("DoudouPet/_internal/PySide6/plugins/platforms/qwindows.dll") is True
    assert keep("DoudouPet/_internal/PySide6/plugins/styles/qmodernwindowsstyle.dll") is True
    assert keep("DoudouPet/_internal/PySide6/plugins/imageformats/qgif.dll") is False
    assert keep("DoudouPet/_internal/PySide6/plugins/platforms/qminimal.dll") is False


def test_application_binaries_are_kept(keep):
    assert keep("DoudouPet/_internal/Qt6Core.dll") is True
    assert keep("DoudouPet/_internal/python312.dll") is True

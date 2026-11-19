from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Frame:
    path: Path
    ms: int


@dataclass(frozen=True)
class Skin:
    id: str
    name: str
    idle: Path
    interact: tuple[Frame, ...]
    bubble: str


def _asset(folder: Path, value: object) -> Path:
    if (not isinstance(value, str) or Path(value).name != value
            or not value.lower().endswith('.png') or ':' in value):
        raise ValueError('Invalid PNG filename')
    path = folder / value
    if path.resolve().parent != folder.resolve() or not path.is_file():
        raise ValueError('Missing or external PNG')
    return path


def _read_skin(folder: Path) -> Skin:
    data = json.loads((folder / 'skin.json').read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Expected a skin object')
    ident, name, frames = data['id'], data['name'], data['interact']
    bubble = data.get('bubble', '')
    if (ident != folder.name or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,39}', folder.name)
            or not isinstance(name, str) or not name.strip() or len(name) > 32
            or not isinstance(bubble, str) or len(bubble) > 60
            or not isinstance(frames, list) or not 1 <= len(frames) <= 48):
        raise ValueError('Invalid skin metadata')
    result = []
    for frame in frames:
        if not isinstance(frame, dict) or type(frame.get('ms')) is not int:
            raise ValueError('Invalid frame duration')
        duration = frame['ms']
        if not 20 <= duration <= 5_000:
            raise ValueError('Frame duration outside supported range')
        result.append(Frame(_asset(folder, frame['file']), duration))
    return Skin(ident, name, _asset(folder, data['idle']), tuple(result), bubble)


def load_skins(root: Path) -> dict[str, Skin]:
    if not root.is_dir():
        return {}
    skins = {}
    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.resolve().parent != root.resolve():
            continue
        try:
            skin = _read_skin(folder)
        except (OSError, ValueError, KeyError):
            continue
        skins[skin.id] = skin
    return skins


def load_settings(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    result = {}
    if isinstance(data.get('skin'), str):
        result['skin'] = data['skin']
    position = data.get('position')
    if (isinstance(position, list) and len(position) == 2
            and all(type(value) is int and -100_000 <= value <= 100_000 for value in position)):
        result['position'] = position
    if type(data.get('always_on_top')) is bool:
        result['always_on_top'] = data['always_on_top']
    return result


def save_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.name + '.', delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            json.dump(settings, temp, ensure_ascii=False, indent=2)
        except Exception:
            temp.close()
            temp_path.unlink(missing_ok=True)
            raise
    try:
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)

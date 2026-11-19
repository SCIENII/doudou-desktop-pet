import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CoreTests(unittest.TestCase):
    def setUp(self):
        from doudou_pet import core

        self.core = core
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def skin(self, name, **changes):
        folder = self.root / name
        folder.mkdir()
        (folder / 'idle.png').write_bytes(b'fixture')
        (folder / 'wave.png').write_bytes(b'fixture')
        data = dict(id=name, name='豆豆', idle='idle.png', bubble='你好',
                    interact=[dict(file='wave.png', ms=180)])
        data.update(changes)
        (folder / 'skin.json').write_text(json.dumps(data), encoding='utf-8')

    def test_loads_named_skin_and_frame_paths(self):
        self.skin('classic')
        skin = self.core.load_skins(self.root)['classic']
        self.assertEqual(skin.name, '豆豆')
        self.assertEqual(skin.idle, self.root / 'classic' / 'idle.png')
        self.assertEqual(skin.interact[0].path.name, 'wave.png')
        self.assertEqual(skin.interact[0].ms, 180)
        self.assertEqual(skin.bubble, '你好')

    def test_rejects_invalid_manifest_and_keeps_valid_skin(self):
        self.skin('classic')
        self.skin('missing', idle='nothing.png')
        self.skin('badtime', interact=[dict(file='wave.png', ms=True)])
        self.skin('escape', idle='../classic/idle.png')
        self.skin('duplicate', id='classic')
        (self.root / 'classic' / 'notes.txt').touch()
        self.assertEqual(set(self.core.load_skins(self.root)), {'classic'})

    def test_missing_skins_directory_returns_empty(self):
        self.assertEqual(self.core.load_skins(self.root / 'missing'), {})

    def test_settings_roundtrip_creates_parent_directory(self):
        file = self.root / 'settings' / 'prefs.json'
        expected = dict(skin='doctor', position=[100, -200], always_on_top=False)
        self.core.save_settings(file, expected)
        self.assertEqual(self.core.load_settings(file), expected)

    def test_absent_and_corrupt_settings_use_empty_defaults(self):
        file = self.root / 'prefs.json'
        self.assertEqual(self.core.load_settings(file), {})
        file.write_bytes(b'\xff')
        self.assertEqual(self.core.load_settings(file), {})

    def test_ignores_unusable_setting_values(self):
        file = self.root / 'prefs.json'
        file.write_text('{"skin":false,"position":[true,2],"always_on_top":1,"extra":"x"}')
        self.assertEqual(self.core.load_settings(file), {})

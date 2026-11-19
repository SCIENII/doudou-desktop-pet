import argparse
import json
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QApplication, QMessageBox

from doudou_pet import __file__ as package_file
from doudou_pet.core import load_settings, load_skins, save_settings
from doudou_pet.window import PetWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--smoke-output', type=Path)
    parser.add_argument('--assets-dir', type=Path, default=Path(package_file).parent / 'assets' / 'skins')
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    app.setApplicationName('DoudouDesktopPet')
    app.setQuitOnLastWindowClosed(False)
    skins = {key: skin for key, skin in load_skins(args.assets_dir).items()
             if all(not QImageReader(str(path)).read().isNull()
                    for path in (skin.idle, *(frame.path for frame in skin.interact)))}
    if args.smoke_test:
        window = PetWindow(skins, {}) if skins else None
        if window:
            window.show()
            app.processEvents()
        visible = bool(window and window.isVisible())
        result = dict(ok=visible and len(skins) == 4, skin_count=len(skins),
                      skin_ids=list(skins), window_visible=visible)
        text = json.dumps(result, ensure_ascii=False)
        if args.smoke_output:
            args.smoke_output.write_text(text, encoding='utf-8')
        elif sys.stdout:
            print(text)
        if window:
            window.close()
        return 0 if result['ok'] else 1
    if not skins:
        QMessageBox.critical(None, '豆豆桌宠', '找不到可用的豆豆立绘，请重新解压完整便携包。')
        return 1
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / 'settings.json'

    def persist(settings):
        try:
            save_settings(path, settings)
        except OSError as error:
            if sys.stderr:
                print(f'Could not save settings: {error}', file=sys.stderr)

    window = PetWindow(skins, load_settings(path), on_change=persist)
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())

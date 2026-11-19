# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH).resolve().parent
package = root / 'doudou_pet'
a = Analysis(
    [str(package / '__main__.py')],
    pathex=[str(root)],
    datas=[(str(package / 'assets' / 'skins'), 'doudou_pet/assets/skins')],
    excludes=['matplotlib', 'numpy', 'PIL', 'tkinter', 'ssl', '_ssl', '_hashlib',
              'PySide6.QtNetwork', 'PySide6.QtSvg'],
)

# PNG skins and the native Windows platform need no optional codecs or TLS plugins.
def keep_binary(destination):
    path = destination.replace('\\', '/').lower()
    name = path.rsplit('/', 1)[-1]
    if '/plugins/' in path:
        return path.endswith(('/platforms/qwindows.dll', '/styles/qmodernwindowsstyle.dll'))
    if name.startswith(('api-ms-win-', 'libcrypto-', 'libssl-', 'msvcp140', 'vcruntime140')):
        return False
    return name not in {'ucrtbase.dll', 'opengl32sw.dll', 'qt6network.dll', 'qt6svg.dll'}


a.binaries = [entry for entry in a.binaries if keep_binary(entry[0])]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='DoudouPet',
          console=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='DoudouPet')

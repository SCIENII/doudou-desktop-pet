# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

root = Path(SPECPATH).resolve().parent
package = root / 'doudou_pet'

# The bundle filter lives outside this file so tests can import it directly.
sys.path.insert(0, str(root / 'packaging'))
from binary_filter import keep as keep_binary  # noqa: E402

a = Analysis(
    [str(package / '__main__.py')],
    pathex=[str(root)],
    datas=[(str(package / 'assets' / 'skins'), 'doudou_pet/assets/skins')],
    excludes=['matplotlib', 'numpy', 'PIL', 'tkinter', 'ssl', '_ssl', '_hashlib',
              'PySide6.QtNetwork', 'PySide6.QtSvg'],
)

# Keep the shell plugin, the native style and the MSVC runtime; drop what this app
# never loads. See packaging/binary_filter.py for the rules and the reasons.
a.binaries = [entry for entry in a.binaries if keep_binary(entry[0])]

pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='DoudouPet',
          console=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='DoudouPet')

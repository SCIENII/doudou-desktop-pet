"""Which files from PyInstaller's analysis end up in the portable bundle.

Kept out of the spec file so the release filter can be unit-tested: PyInstaller
exec's the spec, which makes its helpers hard to import.
"""
import re

# Vulkan/software OpenGL fallbacks, TLS and SVG are unused by this app.
DROP_NAMES = {
    'opengl32sw.dll',
    'qt6network.dll',
    'qt6svg.dll',
}

# Windows 10+ ships these; bundling them breaks older machines and bloats the zip.
DROP_PREFIXES = (
    'api-ms-win-',
    'libcrypto-',
    'libssl-',
    'ucrtbase',
)

# Qt6 and the Python bindings link against the MSVC runtime, which is NOT part of
# Windows itself. Without these the exe dies with "MSVCP140.dll was not found".
KEEP_PLUGINS = (
    '/platforms/qwindows.dll',
    '/styles/qmodernwindowsstyle.dll',
)


def keep(destination):
    """True when `destination` (a path inside the bundle) should ship."""
    path = str(destination).replace('\\', '/').lower()
    name = re.split(r'/', path)[-1]
    if '/plugins/' in path:
        return path.endswith(KEEP_PLUGINS)
    if name.startswith(DROP_PREFIXES):
        return False
    return name not in DROP_NAMES

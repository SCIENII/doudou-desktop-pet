# 第三方运行组件 / Third-party runtime notices

- **Qt Base 6.12.0** 与 **PySide6 Essentials / Shiboken6 6.12.0**：本发布使用 LGPL-3.0，未修改上游动态库。随发行包附 GPL-3.0 和 LGPL-3.0 全文。可在 `_internal/PySide6/` 和 `_internal/shiboken6/` 下用兼容的修改版本替换相应 DLL/PYD；请保留原目录结构。本项目的条款不限制为调试这些修改而进行的逆向工程。原始上游源码见下，也可从本项目同一 Release 下载相应源码归档。
- **CPython 3.14.3**：PSF License 及其随附第三方许可，便携包内提供安装版自带的完整许可证。
- **PyInstaller 6.21.0**：引导程序按 GPL 与 PyInstaller 打包例外分发，例外不改变应用自身的 MIT 许可。便携包内附 COPYING 文本。
- **Microsoft Visual C++ Runtime**：由微软单独提供，便携包不附带。Pillow、pytest 仅用于生成素材与测试。

| 组件 | 对应源码 |
| --- | --- |
| Qt Base 6.12.0 | [Qt 官方源码归档](https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/qtbase-everywhere-src-6.12.0.tar.xz) |
| PySide6 / Shiboken6 6.12.0 | [Qt 官方源码归档](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/pyside-setup-everywhere-src-6.12.0.tar.xz) |
| CPython 3.14.3 | [Python 官方源码归档](https://www.python.org/ftp/python/3.14.3/Python-3.14.3.tar.xz) |
| PyInstaller 6.21.0 | [PyInstaller 源码标签](https://github.com/pyinstaller/pyinstaller/tree/v6.21.0)，[许可与打包例外](https://raw.githubusercontent.com/pyinstaller/pyinstaller/v6.21.0/COPYING.txt) |

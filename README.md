# 豆豆桌宠 · Doudou Desktop Pet

把《AI小知识》和《豆豆博士讲文人》里的像素仓鼠放到 Windows 桌面。离线运行，不需要账号。

[下载 v0.1.0 · Windows x64](https://github.com/SCIENII/doudou-desktop-pet/releases/tag/v0.1.0)

| 造型 | 招牌动作 |
| --- | --- |
| 原版豆豆 | 挥爪打招呼 |
| 豆豆博士 | 划重点 |
| 程序员豆豆 | 敲键盘 |
| 厨师豆豆 | 颠锅弹瓜子 |

## 使用

适用于 Windows 10/11 x64。完整解压便携包后，双击 `DoudouPet.exe`，与 `_internal` 目录一起保留。便携包已自带 `msvcp140.dll` / `vcruntime140.dll`，无需预装 Visual C++ 运行库；若系统仍提示缺少某个 VC 组件，安装微软官方 [Visual C++ x64 运行库](https://aka.ms/vc14/vc_redist.x64.exe) 后重试。左键点击触发动作，按住拖动；右键打开衣柜。系统托盘可切换造型、隐藏、找回或退出。可用托盘退出后再删除程序目录。

## 从源码运行和构建

建议在 Windows x64 上用官方 Python 3.14。以下为 PowerShell 命令：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m doudou_pet
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm packaging/doudou-pet.spec
```

构建产物在 `dist/DoudouPet/`。如需打包或验证发行版，见[发行说明](docs/release.md)。便携指免安装，设置仍保存在 Windows 用户的应用数据目录。

## 模块

- `doudou_pet/`：窗口、应用入口、素材配置与设置读取。
- `doudou_pet/assets/skins/`：四套角色资产；新增造型参见 [素材清单格式](docs/skins.md)。
- `packaging/`：Windows 构建配置。
- `tests/`：清单、设置、素材、桌宠交互的测试。

程序源码使用 [MIT](LICENSE)。四套豆豆形象及动画不适用代码许可，见[素材说明](ASSET-LICENSE.md)。第三方依赖保留各自许可证，见[第三方说明](THIRD-PARTY-NOTICES.md)。

# Windows 发行流程

建议用官方 CPython 3.14.3 x64，从只装有项目依赖的虚拟环境构建。`packaging/make-release.ps1` 运行测试、构建程序、收集第三方许可证并生成便携包；需要联网下载许可证。

```powershell
.\packaging\make-release.ps1 -Python .\.venv\Scripts\python.exe
.\packaging\test-portable.ps1
```

发布时上传 `release/doudou-pet-v0.1.0-windows-x64.zip` 与 `release/SHA256SUMS.txt`。另附 [第三方说明](../THIRD-PARTY-NOTICES.md) 中的 Qt Base 和 PySide6 官方对应源码归档。仓库源码由 GitHub 按标签自动提供，不上传本地源码包、构建缓存或视频项目。

便携包应在新目录解压并从另一工作目录运行 `--smoke-test`，确认窗口出现、四套皮肤可用。检查 SHA-256；正式发布前确认 ZIP 中只有预期的应用、素材、运行库和许可证文件。

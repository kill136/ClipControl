# SafeClip for macOS

SafeClip 是一个剪贴板保护工具，用于监控和拦截敏感内容（如身份证号、手机号等）在特定应用程序（如微信、QQ等）中的粘贴，同时阻止在这些应用中粘贴图片内容。

## macOS 安装说明

### 方法一：使用 py2app 构建应用程序

1. 确保您的 Mac 上已安装 Python 3.6 或更高版本
2. 打开终端，进入 SafeClip 目录
3. 安装必要的依赖：
   ```bash
   pip3 install pyobjc psutil pyperclip py2app
   ```
4. 运行构建脚本：
   ```bash
   chmod +x build_mac.sh
   ./build_mac.sh
   ```
5. 构建完成后，应用程序将位于 `dist/SafeClip.app`
6. 将 `SafeClip.app` 复制到 Applications 文件夹中

### 方法二：使用 PyInstaller 构建应用程序

1. 确保您的 Mac 上已安装 Python 3.6 或更高版本
2. 打开终端，进入 SafeClip 目录
3. 运行 PyInstaller 构建脚本：
   ```bash
   python3 build_mac_pyinstaller.py
   ```
4. 构建完成后，应用程序将位于 `dist/SafeClip.app`
5. 将 `SafeClip.app` 复制到 Applications 文件夹中

## 首次运行

首次运行 SafeClip 时，macOS 可能会提示安全警告，因为应用程序不是从 App Store 下载的。您需要：

1. 打开系统偏好设置 > 安全性与隐私
2. 在"通用"选项卡中，点击"仍要打开"按钮允许 SafeClip 运行
3. 您可能还需要授予 SafeClip 访问辅助功能的权限，以便它能够监控键盘输入和窗口切换

## 使用说明

1. 启动 SafeClip 后，它将在后台运行，不会在 Dock 中显示图标
2. 程序会自动监控剪贴板内容和键盘操作
3. 当检测到在黑名单应用（如微信、QQ）中尝试粘贴敏感内容或图片时，会自动清空剪贴板并显示警告消息
4. 日志文件保存在应用程序同一目录下的 `safeclip_log.txt` 中

## 配置

您可以通过编辑 `safeclip.py` 文件来自定义以下配置：

- `SENSITIVE_PATTERNS`: 敏感数据的正则表达式模式
- `BLOCKED_APPS`: 黑名单应用窗口标题关键词
- `BLOCKED_PROCESSES`: 黑名单应用进程名称

## 退出程序

在终端中按 Ctrl+C 可以退出程序，或者使用活动监视器强制退出。

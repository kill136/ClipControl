# 使用 GitHub Actions 构建 SafeClip macOS 版本

本指南将帮助您使用 GitHub Actions 在云端构建 macOS 版本的 SafeClip 应用程序，无需 Mac 电脑。

## 步骤 1: 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com) 并登录您的账户
2. 点击右上角的 "+" 图标，选择 "New repository"
3. 填写仓库名称，例如 "SafeClip"
4. 选择仓库可见性（公开或私有）
5. 点击 "Create repository"

## 步骤 2: 将代码上传到 GitHub

在您的 Windows 电脑上，使用 Git 将 SafeClip 代码上传到 GitHub：

```bash
# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "初始提交 SafeClip 代码"

# 添加远程仓库（替换 YOUR_USERNAME 为您的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/SafeClip.git

# 推送代码到 GitHub
git push -u origin master
```

## 步骤 3: GitHub Actions 工作流

我们已经为您创建了 GitHub Actions 工作流文件 (`.github/workflows/build_macos.yml`)，它会在 macOS 环境中构建应用程序。

工作流程会：
1. 在 macOS 虚拟机上设置 Python 环境
2. 安装必要的依赖
3. 使用 PyInstaller 构建 macOS 应用
4. 将打包好的应用上传为工作流构建产物

## 步骤 4: 触发构建

将代码推送到 GitHub 后，工作流将自动触发。您也可以手动触发：

1. 在 GitHub 仓库页面，点击 "Actions" 选项卡
2. 在左侧找到 "Build macOS App" 工作流
3. 点击 "Run workflow" 按钮，选择分支，然后点击绿色的 "Run workflow" 按钮

## 步骤 5: 下载构建好的应用

构建完成后（约 5-10 分钟）：

1. 在 "Actions" 选项卡中找到最新的成功运行
2. 点击该运行记录
3. 在页面底部的 "Artifacts" 部分，您会看到 "SafeClip-macOS" 文件
4. 点击下载 zip 文件
5. 解压后，您将获得 `SafeClip.app` 文件，这就是 macOS 应用程序

## 注意事项

1. GitHub Actions 对免费账户有一定的使用限制（每月 2000 分钟）
2. 构建的应用未经过 Apple 签名，macOS 用户首次运行时需要在"安全性与隐私"设置中允许运行
3. 如果您的代码包含敏感信息，请确保使用私有仓库

## 故障排除

如果构建失败：

1. 检查 Actions 日志以了解错误原因
2. 确保所有依赖都已正确列出
3. 检查 Python 代码是否有语法错误
4. 修复问题后重新提交代码或手动触发工作流

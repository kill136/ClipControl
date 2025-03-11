#!/bin/bash

# 确保必要的依赖已安装
pip3 install pyobjc psutil pyperclip py2app

# 清理之前的构建
rm -rf build dist

# 使用py2app构建应用程序
python3 setup.py py2app

echo "构建完成！应用程序位于 dist/SafeClip.app"
echo "您可以将此应用程序复制到 Applications 文件夹中"

#!/usr/bin/env python3
"""
macOS 打包脚本 - 使用 PyInstaller 创建独立的应用程序
"""

import os
import sys
import subprocess

# 确保必要的依赖已安装
print("安装必要的依赖...")
subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller", "pyobjc", "psutil", "pyperclip"])

# 创建 spec 文件内容
spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['safeclip.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['AppKit', 'Quartz', 'Foundation', 'objc', 'psutil', 'PyObjCTools.AppHelper'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SafeClip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SafeClip',
)
app = BUNDLE(
    coll,
    name='SafeClip.app',
    icon=None,
    bundle_identifier='com.safeclip.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'LSUIElement': True,  # 使应用程序在后台运行，不显示在Dock中
        'CFBundleName': 'SafeClip',
        'CFBundleDisplayName': 'SafeClip',
        'CFBundleIdentifier': 'com.safeclip.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 SafeClip. All rights reserved.',
    }
)
"""

# 写入 spec 文件
with open("SafeClip.spec", "w") as f:
    f.write(spec_content)

# 使用 PyInstaller 构建应用程序
print("开始构建 macOS 应用程序...")
subprocess.call(["pyinstaller", "SafeClip.spec"])

print("构建完成！应用程序位于 dist/SafeClip.app")
print("您可以将此应用程序复制到 Applications 文件夹中")

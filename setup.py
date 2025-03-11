from setuptools import setup

APP = ['safeclip.py']
DATA_FILES = ['safeclip_log.txt']
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,  # 使应用程序在后台运行，不显示在Dock中
        'CFBundleName': 'SafeClip',
        'CFBundleDisplayName': 'SafeClip',
        'CFBundleIdentifier': 'com.safeclip.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 SafeClip. All rights reserved.',
    },
    'packages': ['pyperclip', 'psutil'],
    'includes': ['re', 'time', 'threading', 'sys', 'os', 'subprocess', 'traceback', 'datetime', 'platform'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

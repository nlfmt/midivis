# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../assets/icons/icon.ico', '.'),  # Include the icon file
    ],
    hiddenimports=[
        'sounddevice',
        'numpy',
        'scipy',
        'scipy.fft',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AudioInputStreamer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/icons/icon.ico',  # Application icon
)

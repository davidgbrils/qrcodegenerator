# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['generate_qr_code_tele.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ttkbootstrap',
        'ttkbootstrap.themes',
        'ttkbootstrap.themes.standard',
        'ttkbootstrap.icons',
        'ttkbootstrap.localization',
        'PIL',
        'PIL._tkinter_finder',
        'qrcode',
        'qrcode.image.pil',
        'telebot',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='QRCodeGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

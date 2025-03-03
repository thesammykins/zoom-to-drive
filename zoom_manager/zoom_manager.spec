# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/*.py', 'src'),
        ('config/*', 'config'),
    ],
    hiddenimports=[
        'PyQt6',
        'cryptography',
        'aiohttp',
        'aiofiles',
        'google.auth',
        'google.auth.transport.requests',
        'google.auth.transport.urllib3',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'googleapiclient.http',
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
    name='Zoom to Drive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='config/icon.icns'
)

app = BUNDLE(
    exe,
    name='Zoom to Drive.app',
    icon='config/icon.icns',
    bundle_identifier='com.zoomdrive.app',
    info_plist={
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
    }
) 
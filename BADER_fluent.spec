# -*- mode: python ; coding: utf-8 -*-
# BADER macOS Build - Fluent UI Version

block_cipher = None

a = Analysis(
    ['main_fluent_new.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('qt.conf', '.'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
        'PyQt6.QtNetwork',
        # QFluentWidgets
        'qfluentwidgets',
        'qfluentwidgets.common',
        'qfluentwidgets.components',
        'qfluentwidgets.window',
        # Matplotlib
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        # Diğer
        'numpy',
        'sqlite3',
        'PIL',
        'PIL.Image',
        # Tüm UI modülleri
        'database',
        'ui_dashboard',
        'ui_uyeler',
        'ui_aidat',
        'ui_gelir',
        'ui_gider',
        'ui_kasa',
        'ui_virman',
        'ui_devir',
        'ui_export',
        'ui_uye_detay',
        'ui_uye_aidat',
        'ui_uyeler_ayrilan',
        'ui_raporlar',
        'ui_etkinlik',
        'ui_toplanti',
        'ui_butce',
        'ui_kullanicilar',
        'ui_belgeler',
        'ui_mali_tablolar',
        'ui_alacak_verecek',
        'ui_tahakkuk_rapor',
        'ui_koy_dashboard',
        'ui_koy_islemler',
        'ui_ayarlar',
        'ui_drawer',
        'ui_helpers',
        'ui_styles',
        'models',
        'pdf_generator',
        'email_service',
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
    [],
    exclude_binaries=True,
    name='BADER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS için önemli
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
    name='BADER',
)

app = BUNDLE(
    coll,
    name='BADER.app',
    icon=None,
    bundle_identifier='com.baderdernegi.bader',
    info_plist={
        'CFBundleName': 'BADER',
        'CFBundleDisplayName': 'BADER Dernek Yönetimi',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15',
    },
)

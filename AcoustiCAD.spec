# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for AcoustiCAD (macOS)
# Version is read from the VERSION file at build time — single source of truth.

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

project_root = os.path.abspath('.')

# Read VERSION once — used in BUNDLE info_plist below. Apple's CFBundleVersion
# requires plain numeric (no prerelease suffix), so we strip "-beta" etc.
VERSION_STR = open(os.path.join(project_root, 'VERSION')).read().strip()
BUNDLE_VERSION = VERSION_STR.split('-')[0]

block_cipher = None

# Collect all local package submodules so PyInstaller doesn't miss any
local_hidden = (
    collect_submodules('utils') +
    collect_submodules('ui') +
    collect_submodules('core')
)

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('ui/resources', 'ui/resources'),
        ('data/default_speaker_profiles', 'data/default_speaker_profiles'),
        # Bundle VERSION at the bundle root so __version__.py can read it via sys._MEIPASS
        ('VERSION', '.'),
    ],
    hiddenimports=local_hidden + [
        'shiboken6',
        'PySide6.QtPrintSupport',
        'fitz',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas'],
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
    name='AcoustiCAD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
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
    name='AcoustiCAD',
)

app = BUNDLE(
    coll,
    name='AcoustiCAD.app',
    icon='ui/resources/AppIcon.icns',
    bundle_identifier='com.freeforgelabs.acousticad',
    version=BUNDLE_VERSION,
    info_plist={
        'CFBundleName': 'AcoustiCAD',
        'CFBundleDisplayName': 'AcoustiCAD',
        'CFBundleShortVersionString': VERSION_STR,
        'CFBundleVersion': BUNDLE_VERSION,
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.13.0',
    },
)

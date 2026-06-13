# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for AcoustiCAD (Windows)
# Version is read from the VERSION file at build time — single source of truth.

import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath('.')
block_cipher = None

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
        # Bundle VERSION so __version__.py can read it via sys._MEIPASS when frozen
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
    console=False,                  # No terminal window
    icon='ui/resources/AppIcon.ico',
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='installer/version_info.txt',
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

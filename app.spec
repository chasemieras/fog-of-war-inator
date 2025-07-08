# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'numpy',
        'cv2',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.widgets',
        'queue',
        'threading',
        'json',
        'datetime',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'tornado',
        'zmq',
        'pytest',
        'setuptools',
        'distutils'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

try:
    pdict = Tree('venv/Lib/site-packages/customtkinter', prefix='customtkinter', excludes=["*.pyc", "*.pyo", "__pycache__"])
    a.datas += pdict
except:
    import customtkinter
    import os
    ctk_path = os.path.dirname(customtkinter.__file__)
    pdict = Tree(ctk_path, prefix='customtkinter', excludes=["*.pyc", "*.pyo", "__pycache__"])
    a.datas += pdict

try:
    pdict = Tree('venv/Lib/site-packages/PIL', prefix='PIL', excludes=["*.pyc", "*.pyo", "__pycache__"])
    a.datas += pdict
except:
    import PIL
    import os
    pil_path = os.path.dirname(PIL.__file__)
    pdict = Tree(pil_path, prefix='PIL', excludes=["*.pyc", "*.pyo", "__pycache__"])
    a.datas += pdict

try:
    import numpy
    numpy_path = os.path.dirname(numpy.__file__)
    numpy_tree = Tree(numpy_path, prefix='numpy', excludes=["*.pyc", "*.pyo", "__pycache__", "tests"])
    a.datas += numpy_tree
except:
    pass

try:
    import cv2
    cv2_path = os.path.dirname(cv2.__file__)
    cv2_tree = Tree(cv2_path, prefix='cv2', excludes=["*.pyc", "*.pyo", "__pycache__"])
    a.datas += cv2_tree
except:
    pass

a.datas = list(set(a.datas))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FogOfWar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'msvcp140.dll',
        'python*.dll',
        'tk*.dll',
        'tcl*.dll'
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None, 
)
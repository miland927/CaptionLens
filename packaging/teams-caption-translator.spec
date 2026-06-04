# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path
import os


block_cipher = None
project_root = Path(SPECPATH).parent

datas = []
datas += collect_data_files("easyocr")

easyocr_model_dir = Path(os.environ.get("TCT_EASYOCR_MODEL_DIR", Path.home() / ".EasyOCR" / "model"))
for model_name in ("craft_mlt_25k.pth", "japanese_g2.pth"):
    model_path = easyocr_model_dir / model_name
    if model_path.exists():
        datas.append((str(model_path), "easyocr_model"))

hiddenimports = []
hiddenimports += collect_submodules("easyocr")
hiddenimports += collect_submodules("torch")
hiddenimports += collect_submodules("torchvision")
hiddenimports += collect_submodules("skimage")

a = Analysis(
    [str(project_root / "scripts" / "frozen_app.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="TeamsCaptionTranslator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name="TeamsCaptionTranslator",
)

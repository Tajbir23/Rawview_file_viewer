import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
INSTALLER_OUT = BASE_DIR / "dist_installer"

def find_iscc() -> str:
    """Locates Inno Setup Compiler ISCC.exe."""
    possible_paths = [
        shutil.which("iscc"),
        r"C:\Users\Zim\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for p in possible_paths:
        if p and os.path.exists(p):
            return p
    return ""

def build():
    from src.core.config import APP_VERSION, APP_PUBLISHER
    version_clean = APP_VERSION.lstrip("v")
    print("=" * 60)
    print(f" RawView {APP_VERSION} - Release & Installer Build Pipeline")
    print(f" Publisher: {APP_PUBLISHER}")
    print("=" * 60)

    # 1. Clean previous build artifacts
    for d in [DIST_DIR, BUILD_DIR, INSTALLER_OUT]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)

    # 2. Compile with PyInstaller
    icon_path = BASE_DIR / "assets" / "app_icon.ico"
    print("\n[1/2] Compiling RawView.exe with PyInstaller...")
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--noconfirm",
        "--clean",
        f"--name=RawView",
        f"--icon={icon_path}",
        "--onedir",
        "--add-data=assets;assets",
        "--collect-all=pypdfium2",
        "--collect-all=pymupdf",
        "--collect-all=psd_tools",
        "--collect-all=PyQt6",
        "--collect-all=PyQt6.QtMultimedia",
        "--collect-all=PyQt6.QtMultimediaWidgets",
        "--collect-all=reportlab",
        "--collect-all=rawpy",
        "--hidden-import=rawpy",
        "--hidden-import=PyQt6.QtSvg",
        "--hidden-import=PyQt6.QtMultimedia",
        "--hidden-import=PyQt6.QtMultimediaWidgets",
        "--hidden-import=pypdfium2",
        "--hidden-import=pymupdf",
        "--hidden-import=fitz",
        "--hidden-import=psd_tools",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.TiffImagePlugin",
        "--hidden-import=PIL.PsdImagePlugin",
        "--hidden-import=uiautomation",
        "--hidden-import=comtypes",
        "--hidden-import=win32gui",
        "--hidden-import=win32process",
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "--hidden-import=striprtf",
        "--hidden-import=src.core.bijoy_converter",
        str(BASE_DIR / "src" / "app.py")
    ]

    res = subprocess.run(pyinstaller_cmd, cwd=str(BASE_DIR))
    if res.returncode != 0:
        print("ERROR: PyInstaller compilation failed.")
        sys.exit(1)

    print("PyInstaller build complete: dist/RawView/RawView.exe exists!")

    # Copy assets into dist/RawView/assets
    shutil.copytree(BASE_DIR / "assets", DIST_DIR / "RawView" / "assets", dirs_exist_ok=True)

    # 3. Compile Installer with Inno Setup
    print(f"\n[2/2] Generating RawView_{APP_VERSION}_Setup.exe with Inno Setup...")
    iscc_exe = find_iscc()
    if not iscc_exe:
        print("ERROR: ISCC.exe not found.")
        sys.exit(1)

    iss_path = BASE_DIR / "installer" / "RawView.iss"
    iscc_cmd = [iscc_exe, str(iss_path)]
    res_iss = subprocess.run(iscc_cmd, cwd=str(BASE_DIR / "installer"))
    if res_iss.returncode == 0:
        setup_exe = INSTALLER_OUT / f"RawView_{APP_VERSION}_Setup.exe"
        print("\n" + "=" * 60)
        print(f" SUCCESS! Installer created successfully:")
        print(f" -> {setup_exe}")
        if setup_exe.exists():
            size_mb = setup_exe.stat().st_size / (1024.0 * 1024.0)
            print(f" -> Size: {size_mb:.2f} MB")
            print(f" -> Publisher: {APP_PUBLISHER}")
        print("=" * 60)
    else:
        print("ERROR: Inno Setup compilation failed.")

if __name__ == "__main__":
    build()

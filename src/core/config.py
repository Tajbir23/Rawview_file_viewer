import os
import json
from pathlib import Path

APP_NAME = "RawView"
APP_VERSION = "v3.9.5"
APP_PUBLISHER = "BlackBox THC"
APP_MUTEX_NAME = "RawView_SingleInstance_Mutex_v3.9.5"

# Standard Web & Raster Images (Disabled by default in settings)
STANDARD_IMAGE_EXTENSIONS = {
    ".jpg":  "JPEG Image",
    ".jpeg": "JPEG Image",
    ".png":  "Portable Network Graphics",
    ".webp": "WebP Image",
    ".gif":  "Graphics Interchange Format",
    ".ico":  "Windows Icon",
    ".bmp":  "Bitmap Image",
}

# Supported extensions
SUPPORTED_EXTENSIONS = {
    # Adobe Photoshop
    ".psd": "Photoshop Document",
    ".psb": "Photoshop Large Document",
    # Adobe Illustrator & Vectors
    ".ai":  "Adobe Illustrator Artwork",
    ".eps": "Encapsulated PostScript",
    ".svg": "Scalable Vector Graphics",
    ".svgz":"Compressed SVG",
    # Documents & Publishing
    ".pdf": "Portable Document Format",
    ".docx": "Microsoft Word",
    ".doc": "Microsoft Word Legacy",
    ".xlsx": "Microsoft Excel",
    ".xls": "Microsoft Excel Legacy",
    ".pptx": "Microsoft PowerPoint",
    ".ppt": "Microsoft PowerPoint Legacy",
    ".rtf": "Rich Text Format",
    ".csv": "Comma Separated Values",
    # Adobe Projects
    ".aep": "After Effects Project",
    ".aet": "After Effects Template",
    ".aepx": "After Effects XML Project",
    ".prproj": "Premiere Pro Project",
    ".prset": "Premiere Pro Preset",
    # Raster Images
    ".tif": "TIFF Image",
    ".tiff":"TIFF Image",
    # Standard & Web Raster Images
    **STANDARD_IMAGE_EXTENSIONS,
    # Video Formats
    ".mp4": "MPEG-4 Video",
    ".mkv": "Matroska Video",
    ".mov": "QuickTime Video",
    ".avi": "AVI Video",
    ".wmv": "Windows Media Video",
    ".webm":"WebM Video",
    ".m4v": "iTunes Video",
    ".flv": "Flash Video",
    ".ts":  "MPEG Transport Stream",
    ".3gp": "3GPP Video",
    ".mpg": "MPEG Video",
    ".mpeg":"MPEG Video",
    # Adobe / Universal Digital Negative
    ".dng": "Digital Negative RAW",
    # Canon Camera RAW
    ".cr2": "Canon RAW 2",
    ".cr3": "Canon RAW 3",
    ".crw": "Canon RAW",
    # Nikon Camera RAW
    ".nef": "Nikon Electronic Format",
    ".nrw": "Nikon RAW",
    # Sony Camera RAW
    ".arw": "Sony Alpha RAW",
    ".srf": "Sony RAW",
    ".sr2": "Sony RAW 2",
    # Fujifilm RAW
    ".raf": "Fujifilm RAW",
    # Olympus RAW
    ".orf": "Olympus RAW",
    ".ori": "Olympus RAW",
    # Panasonic Lumix RAW
    ".rw2": "Panasonic Lumix RAW",
    # Pentax RAW
    ".pef": "Pentax Electronic File",
    ".ptx": "Pentax RAW",
    # Hasselblad & Phase One
    ".3fr": "Hasselblad 3FR RAW",
    ".fff": "Hasselblad FFF RAW",
    ".iiq": "Phase One RAW",
    ".raw": "Camera RAW Image",
    ".x3f": "Sigma RAW"
}

# Payment & Support Information
PAYMENT_INFO = {
    "price_bdt": "50 TK",
    "bkash_number": "01756678087",
    "bkash_type": "Personal (Send Money)",
    "support_handle": "@chatGptPlusAIbot",
    "support_link": "https://t.me/chatGptPlusAIbot",
}

# Directories
APPDATA_DIR = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "RawView"
CACHE_DIR = APPDATA_DIR / "cache"
CONFIG_FILE = APPDATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "enabled": True,
    "hover_delay_ms": 120,       # Settle dwell time in milliseconds
    "preview_max_size": 640,     # Max width/height of preview window in px
    "autostart": True,           # Start with Windows boot
    "show_metadata": True,       # Show format badge, dimensions, size
    "enable_animations": True,   # Smooth fade/scale animations
    "cache_max_mb": 500,         # Max disk cache size
    # Standard raster images (jpg, png, webp, gif, ico, bmp) are disabled by default
    "supported_formats": [k for k in SUPPORTED_EXTENSIONS.keys() if k not in STANDARD_IMAGE_EXTENSIONS]
}

def load_config() -> dict:
    os.makedirs(APPDATA_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    os.makedirs(APPDATA_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")

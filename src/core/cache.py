import os
import hashlib
import json
import collections
from pathlib import Path
from PIL import Image
from .config import CACHE_DIR

class MemoryCache:
    """L1 In-Memory LRU Cache for ready-to-render QPixmap/QImage/PIL objects."""
    def __init__(self, max_items: int = 64):
        self.max_items = max_items
        self._cache = collections.OrderedDict()

    def _make_key(self, file_path: str, mtime: float, size: int) -> str:
        return f"{file_path}|{mtime}|{size}"

    def get(self, file_path: str, mtime: float, size: int):
        key = self._make_key(file_path, mtime, size)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, file_path: str, mtime: float, size: int, data: tuple):
        key = self._make_key(file_path, mtime, size)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = data
        if len(self._cache) > self.max_items:
            self._cache.popitem(last=False)

    def clear(self):
        self._cache.clear()

class DiskCache:
    """L2 Persistent Disk Cache for fast cold-start loading of heavy files."""
    def __init__(self, cache_dir: Path = CACHE_DIR, max_size_mb: int = 500):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_hash(self, file_path: str, mtime: float, size: int) -> str:
        data = f"{file_path}:{mtime}:{size}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()[:24]

    def get(self, file_path: str, mtime: float, size: int):
        h = self._get_hash(file_path, mtime, size)
        img_path = self.cache_dir / f"{h}.webp"
        meta_path = self.cache_dir / f"{h}.json"

        if img_path.exists() and meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                with Image.open(img_path) as img_f:
                    img = img_f.copy()
                return img, meta
            except Exception:
                pass
        return None

    def put(self, file_path: str, mtime: float, size: int, img: Image.Image, meta: dict):
        try:
            h = self._get_hash(file_path, mtime, size)
            img_path = self.cache_dir / f"{h}.webp"
            meta_path = self.cache_dir / f"{h}.json"

            # Save optimized thumbnail
            # Keep reasonable max preview resolution (e.g. 1440px)
            thumb = img.copy()
            thumb.thumbnail((1440, 1440), Image.Resampling.LANCZOS)
            if thumb.mode in ("RGBA", "LA") or (thumb.mode == "P" and "transparency" in thumb.info):
                thumb.save(img_path, format="WEBP", lossless=False, quality=90)
            else:
                thumb.convert("RGB").save(img_path, format="WEBP", lossless=False, quality=90)

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f)
        except Exception as e:
            print(f"DiskCache save error: {e}")

    def clear(self):
        try:
            for item in self.cache_dir.glob("*"):
                if item.is_file():
                    item.unlink(missing_ok=True)
        except Exception as e:
            print(f"Clear cache error: {e}")

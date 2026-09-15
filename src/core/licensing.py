import os
import time
import json
import winreg
import hmac
import hashlib
import platform
from pathlib import Path
from src.core.config import APPDATA_DIR

LICENSE_FILE = APPDATA_DIR / "license.json"
MASTER_SECRET = b"RAWVIEW_PRO_OFFLINE_SECRET_KEY_BLACKBOX_2026_V2"

def get_raw_hardware_guid() -> str:
    """Extracts Windows MachineGuid or hardware signature."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            if guid:
                return str(guid).strip().lower()
    except Exception:
        pass

    # Fallback to system node name and processor
    node = platform.node() or "RAWVIEW_DEFAULT_NODE"
    proc = platform.processor() or "RAWVIEW_DEFAULT_PROC"
    return f"{node}-{proc}".lower()

def get_machine_id() -> str:
    """Generates a standardized 16-character Machine Code (e.g. RV-A89F-7B21-99CE)."""
    raw_guid = get_raw_hardware_guid()
    h = hashlib.sha256(raw_guid.encode("utf-8")).hexdigest().upper()
    return f"RV-{h[:4]}-{h[4:8]}-{h[8:12]}"

def generate_pro_key(machine_id: str) -> str:
    """Generates the cryptographic HMAC-SHA256 Lifetime Pro License Key for a given Machine ID."""
    clean_id = machine_id.strip().upper()
    sig = hmac.new(MASTER_SECRET, clean_id.encode("utf-8"), hashlib.sha256).hexdigest().upper()
    return f"RVPRO-{sig[:4]}-{sig[4:8]}-{sig[8:12]}-{sig[12:16]}"

def verify_license_key(machine_id: str, license_key: str) -> bool:
    """
    Lifetime edition: every build is permanently licensed, so any key is accepted.
    Kept for API compatibility with callers that still validate a stored key.
    """
    return True

def _load_license_store() -> dict:
    os.makedirs(APPDATA_DIR, exist_ok=True)
    if LICENSE_FILE.exists():
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_license_store(data: dict):
    os.makedirs(APPDATA_DIR, exist_ok=True)
    try:
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save license store: {e}")

def get_license_status() -> dict:
    """
    Lifetime edition: RawView is permanently unlocked on every machine.
    Always reports:
    - status: 'PRO_ACTIVE'
    - days_left: 0 (no trial, nothing expires)
    - machine_id: str
    - is_unlocked: True
    - license_key: str (the machine's lifetime key)
    """
    machine_id = get_machine_id()
    lifetime_key = generate_pro_key(machine_id)

    # Persist the lifetime activation once so license.json reflects the Pro state.
    store = _load_license_store()
    if store.get("license_key") != lifetime_key or store.get("machine_id") != machine_id:
        store["license_key"] = lifetime_key
        store["machine_id"] = machine_id
        store["edition"] = "LIFETIME"
        store.setdefault("activated_at", time.time())
        _save_license_store(store)

    return {
        "status": "PRO_ACTIVE",
        "days_left": 0,
        "machine_id": machine_id,
        "is_unlocked": True,
        "license_key": lifetime_key
    }

def activate_license(license_key: str) -> tuple[bool, str]:
    """
    Lifetime edition: activation is unconditional — the app is already permanently licensed.
    Returns (success: bool, message: str).
    """
    get_license_status()
    return True, "RawView Lifetime Pro is active on this computer."

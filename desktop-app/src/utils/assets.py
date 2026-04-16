"""
desktop-app/src/utils/assets.py

Central helper for loading SENTINEL image assets.
UPDATED: Handles PyInstaller frozen exe (_MEIPASS) path correctly.

Usage:
    from utils.assets import set_window_icon, get_logo_32, get_logo_64
    set_window_icon(my_window)
    label = ctk.CTkLabel(parent, image=get_logo_32(), text="")
"""
from pathlib import Path
from typing import Optional
import sys
import os
import customtkinter as ctk
from PIL import Image
from dotenv import load_dotenv


# ── App root detection ────────────────────────────────────────────────────────
# Priority order:
#   1. PyInstaller frozen  → sys._MEIPASS  (bundled data temp dir)
#   2. Nuitka compiled     → exe parent dir
#   3. Dev mode            → 3 levels up from this file

def get_app_root() -> Path:
    # PyInstaller: bundled data extracted to _MEIPASS
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    # PyInstaller fallback / Nuitka
    if getattr(sys, 'frozen', False) or "__compiled__" in globals():
        return Path(sys.executable).parent
    # Dev: this file is at src/utils/assets.py → go 3 levels up
    return Path(__file__).resolve().parent.parent.parent


def get_exe_dir() -> Path:
    """
    Directory containing the .exe (or the script in dev mode).
    Used for loading .env next to the exe.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


# ── Load .env ─────────────────────────────────────────────────────────────────
# Try next to exe first, then fallback to project root
_env_path = get_exe_dir() / ".env"
if not _env_path.exists():
    _env_path = get_app_root() / ".env"
load_dotenv(dotenv_path=_env_path)

# ── Asset paths ───────────────────────────────────────────────────────────────
_BASE_DIR  = get_app_root()
_ASSET_DIR = _BASE_DIR / "assets" / "iso"

# If running from _MEIPASS and assets aren't found there,
# fall back to exe directory (user placed assets/ next to exe)
if not _ASSET_DIR.exists():
    _ASSET_DIR = get_exe_dir() / "assets" / "iso"

ICO_PATH       = _ASSET_DIR / "sentinel.ico"
SENTINEL_LOGO  = _ASSET_DIR / "sentinel_logo_nobg.png"
SHIELD_PNG_256 = _ASSET_DIR / "sentinel_shield.png"
SHIELD_PNG_32  = _ASSET_DIR / "sentinel_32.png"
SHIELD_PNG_64  = _ASSET_DIR / "sentinel_64.png"


def _ctk_image(path: Path, size: tuple) -> Optional[ctk.CTkImage]:
    """Load a PNG as a HiDPI-aware CTkImage, or return None if missing."""
    if not path.exists():
        print(f"[assets] WARNING: {path} not found")
        return None
    try:
        pil = Image.open(path).convert("RGBA")
        return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
    except Exception as e:
        print(f"[assets] ERROR loading {path}: {e}")
        return None


def set_window_icon(window) -> None:
    """
    Set the SENTINEL .ico on any Tk/CTk window (title bar + taskbar).
    Safe to call even if the .ico file is missing.
    """
    if ICO_PATH.exists():
        try:
            window.iconbitmap(str(ICO_PATH))
        except Exception as e:
            print(f"[assets] iconbitmap failed: {e}")


# ── Per-root image cache ──────────────────────────────────────────────────────
# Images MUST be created after a Tk root exists, and MUST be re-created
# if the root is destroyed and a new one made (login → logout → login).
# Call clear_cache() in SentinelApp._on_login_success() before opening
# MainWindow (already done in your code).

_cache: dict = {}


def clear_cache():
    """Clear the image cache. Call when switching between Tk roots."""
    _cache.clear()
    print("[assets] Image cache cleared")


def _get(key: str, path: Path, size: tuple) -> Optional[ctk.CTkImage]:
    if key not in _cache:
        _cache[key] = _ctk_image(path, size)
    return _cache[key]


# ── Public accessors ──────────────────────────────────────────────────────────

def get_logo_64() -> Optional[ctk.CTkImage]:
    """64×64 SENTINEL logo (used on login screen)"""
    return _get("logo64", SENTINEL_LOGO, (64, 64))


def get_logo_32() -> Optional[ctk.CTkImage]:
    """32×32 SENTINEL logo (used in sidebar brand)"""
    return _get("logo32", SENTINEL_LOGO, (32, 32))


def get_shield_32() -> Optional[ctk.CTkImage]:
    return _get("s32", SHIELD_PNG_32, (32, 32))


def get_shield_48() -> Optional[ctk.CTkImage]:
    return _get("s48", SHIELD_PNG_256, (48, 48))


def get_shield_64() -> Optional[ctk.CTkImage]:
    return _get("s64", SHIELD_PNG_64, (64, 64))


def get_shield_80() -> Optional[ctk.CTkImage]:
    return _get("s80", SHIELD_PNG_256, (80, 80))


def get_shield_96() -> Optional[ctk.CTkImage]:
    return _get("s96", SHIELD_PNG_256, (96, 96))
    
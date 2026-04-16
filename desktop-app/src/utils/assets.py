"""
desktop-app/src/utils/assets.py

Central helper for loading SENTINEL image assets.
Import this everywhere instead of duplicating path logic.

Usage:
    from utils.assets import set_window_icon, load_ctk_image, SHIELD_32, SHIELD_64

    set_window_icon(my_window)
    label = ctk.CTkLabel(parent, image=SHIELD_32, text="")
"""
from pathlib import Path
from typing import Optional
import sys
import customtkinter as ctk
from PIL import Image

# ── Asset root detection ──────────────────────────────────
import sys
import os

def get_app_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    if "__compiled__" in globals():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent

_BASE_DIR = get_app_root()
_env_path = _BASE_DIR / ".env"
load_dotenv(dotenv_path=_env_path)
_ASSET_DIR = _BASE_DIR / "assets" / "iso"

ICO_PATH          = _ASSET_DIR / "sentinel.ico"
SENTINEL_LOGO     = _ASSET_DIR / "sentinel_logo_nobg.png"
SHIELD_PNG_256    = _ASSET_DIR / "sentinel_shield.png"
SHIELD_PNG_32     = _ASSET_DIR / "sentinel_32.png"
SHIELD_PNG_64     = _ASSET_DIR / "sentinel_64.png"


def _ctk_image(path: Path, size: tuple) -> Optional[ctk.CTkImage]:
    """Load a PNG as a HiDPI-aware CTkImage, or return None if missing."""
    if not path.exists():
        print(f"[assets] WARNING: {path} not found")
        return None
    pil = Image.open(path).convert("RGBA")
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)


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


# ── Pre-built CTkImage sizes (created lazily on first import) ─
# Call get_shield_XX() to access; avoids Tk being initialised at module level.

_cache: dict = {}

def _get(key: str, path: Path, size: tuple) -> Optional[ctk.CTkImage]:
    if key not in _cache:
        _cache[key] = _ctk_image(path, size)
    return _cache[key]

def get_logo_64() -> Optional[ctk.CTkImage]:
    return _get("logo64", SENTINEL_LOGO, (64, 64))

def get_logo_32() -> Optional[ctk.CTkImage]:
    return _get("logo32", SENTINEL_LOGO, (32, 32))

def get_shield_32()  -> Optional[ctk.CTkImage]:
    return _get("s32",  SHIELD_PNG_32,  (32, 32))

def get_shield_48()  -> Optional[ctk.CTkImage]:
    return _get("s48",  SHIELD_PNG_256, (48, 48))

def get_shield_64()  -> Optional[ctk.CTkImage]:
    return _get("s64",  SHIELD_PNG_64,  (64, 64))

def get_shield_80()  -> Optional[ctk.CTkImage]:
    return _get("s80",  SHIELD_PNG_256, (80, 80))

def get_shield_96()  -> Optional[ctk.CTkImage]:
    return _get("s96",  SHIELD_PNG_256, (96, 96))
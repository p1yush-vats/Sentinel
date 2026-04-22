# -*- mode: python ; coding: utf-8 -*-
#
# sentinel.spec — PyInstaller build spec for SENTINEL Desktop App
#
# Place this file in desktop-app/ (same level as src/ and assets/)
# Run: pyinstaller sentinel.spec --clean
#
# Output: desktop-app/dist/SENTINEL.exe

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Paths (relative to this spec file, which lives in desktop-app/) ──────────
SPEC_DIR   = Path(SPECPATH)          # desktop-app/
SRC_DIR    = SPEC_DIR / "src"        # desktop-app/src/
ASSET_DIR  = SPEC_DIR / "assets"     # desktop-app/assets/
ENV_FILE   = SPEC_DIR / ".env"       # desktop-app/.env

# ── Data files to bundle ──────────────────────────────────────────────────────
#
# Format: (source_path, destination_folder_inside_bundle)
# At runtime (frozen), these land in sys._MEIPASS/<destination_folder>
# The runtime hook (below) patches sys.path so assets.py finds them.
#
datas = []

# CustomTkinter needs its theme JSON files
datas += collect_data_files("customtkinter")

# pystray needs its platform backend resources
datas += collect_data_files("pystray", includes=["*.png", "*.ico"])

# Your asset images — bundled into assets/iso/ inside the exe
if ASSET_DIR.exists():
    datas += [(str(ASSET_DIR / "iso"), "assets/iso")]
else:
    print(f"WARNING: assets/iso not found at {ASSET_DIR}")

# Bundle the .env so the app can find its config without an external file
# (users can still override by placing a .env next to the .exe)
if ENV_FILE.exists():
    datas += [(str(ENV_FILE), ".")]
else:
    print("WARNING: .env not found — it will not be bundled")

# ── Hidden imports ────────────────────────────────────────────────────────────
# Modules that PyInstaller's static analysis misses because they are
# imported dynamically (e.g. via importlib, __import__, or inside try/except)
#
hiddenimports = [
    # pynput platform backends
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "pynput._util.win32",
    "pynput._util.win32_vk",

    # Windows system DLLs accessed via ctypes
    "ctypes.wintypes",
    "win32api",
    "win32con",
    "win32clipboard",
    "win32gui",
    "win32process",
    "win32security",
    "pywintypes",
    "winerror",

    # pystray Windows backend
    "pystray._win32",

    # winotify (optional toast notifications)
    "winotify",

    # websocket-client
    "websocket",
    "websocket._app",
    "websocket._core",
    "websocket._exceptions",
    "websocket._handshake",
    "websocket._http",
    "websocket._logging",
    "websocket._socket",
    "websocket._ssl_compat",
    "websocket._utils",

    # httpx internals sometimes missed
    "httpx._transports.default",
    "httpcore",
    "h11",
    "h2",

    # cryptography (used by JWTHandler)
    "cryptography.hazmat.primitives.ciphers.algorithms",
    "cryptography.hazmat.backends.openssl",
    "cryptography.hazmat.bindings.openssl.binding",

    # pytz timezone data
    "pytz",
    "pytz.tzinfo",

    # PIL/Pillow submodules
    "PIL._tkinter_finder",
    "PIL.ImageTk",
    "PIL.ImageDraw",

    # tkinter
    "tkinter",
    "tkinter.ttk",
    "_tkinter",

    # dotenv
    "dotenv",
    "python_dotenv",

    # SQLite (stdlib, usually included, but be explicit)
    "sqlite3",

    # Your own packages (PyInstaller may miss relative imports)
    "core.config",
    "core.time_engine",
    "core.session_manager",
    "auth.jwt_handler",
    "detection.abnormality_detector",
    "detection.abnormality_aggregator",
    "detection.input_collector",
    "storage.local_db",
    "sync.sync_client",
    "ui.login_window",
    "ui.main_window",
    "utils.assets",
    "utils.timezone_utils",
]

# ── Collect all submodules for packages with dynamic loading ──────────────────
hiddenimports += collect_submodules("customtkinter")
hiddenimports += collect_submodules("pynput")

# ── Modules to exclude (reduces .exe size) ───────────────────────────────────
excludes = [
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "tensorflow",
    "torch",
    "pytest",
    "IPython",
    "jupyter",
    "notebook",
    "sphinx",
    "docutils",
    "setuptools",
    "pkg_resources._vendor",
    "xml.etree.cElementTree",    # replaced by xml.etree.ElementTree in 3.9+
    "email.mime",
    "html.parser",
    "unittest",
    "test",
    "tkinter.test",
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(SRC_DIR / "main.py")],          # entry point
    pathex=[str(SRC_DIR)],               # add src/ to sys.path so imports work
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(SPEC_DIR / "runtime_hook_assets.py")],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)

# ── PYZ — compressed bytecode archive ────────────────────────────────────────
pyz = PYZ(a.pure)

# ── EXE — single-file executable ─────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SENTINEL_DEMO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # set False if UPX is not installed
    upx_exclude=[
        # These DLLs are known to break when UPX-compressed
        "vcruntime140.dll",
        "python3*.dll",
        "tk*.dll",
        "tcl*.dll",
        "_tkinter.pyd",
        "select.pyd",
    ],
    runtime_tmpdir=None,
    console=False,          # no black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSET_DIR / "iso" / "sentinel.ico") if (ASSET_DIR / "iso" / "sentinel.ico").exists() else None,
    version=str(SPEC_DIR / "version_info.txt") if (SPEC_DIR / "version_info.txt").exists() else None,
)

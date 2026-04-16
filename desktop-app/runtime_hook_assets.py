# runtime_hook_assets.py
#
# Place this file in desktop-app/ (same level as sentinel.spec)
#
# PyInstaller runs this script BEFORE your app starts when the exe launches.
# It patches sys.path so that your src/ packages are importable, and sets
# up the asset path so utils/assets.py finds images correctly.
#
# HOW ASSET LOADING WORKS in the frozen exe:
#
#   When PyInstaller bundles with --onefile, all data files are extracted
#   to a temporary directory at sys._MEIPASS on launch.
#
#   Your assets.py uses get_app_root() which returns Path(sys.executable).parent
#   when sys.frozen is True. This is the FOLDER CONTAINING the .exe.
#
#   This means:
#     - The user must either have assets/ next to the .exe, OR
#     - We copy assets into the exe (via datas in spec) and patch the path here
#       to point to sys._MEIPASS/assets/iso instead.
#
#   This hook does the latter — it sets an env variable that assets.py
#   can read as a fallback, ensuring images always load even if the user
#   has no assets/ folder next to the exe.

import sys
import os
from pathlib import Path

# Mark as frozen (PyInstaller does this automatically, but be explicit)
sys.frozen = True

# Add src/ directory to sys.path so all your packages are importable
# PyInstaller normally handles this, but being explicit prevents edge cases
if hasattr(sys, '_MEIPASS'):
    meipass = Path(sys._MEIPASS)
    src_path = str(meipass / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    # Also add _MEIPASS itself (for top-level imports)
    if str(meipass) not in sys.path:
        sys.path.insert(0, str(meipass))

    # Tell assets.py where to find the bundled assets
    # assets.py calls get_app_root() → Path(sys.executable).parent
    # But bundled files land in _MEIPASS, so we set this env var as fallback
    os.environ.setdefault(
        "SENTINEL_ASSET_ROOT",
        str(meipass)
    )

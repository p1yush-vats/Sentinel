"""
Main Window — SENTINEL Desktop App
Fully fixed CustomTkinter UI

Layout:
  Left sidebar  : nav links + user card + logout
  Top bar       : session/alert badges + sync label
  Centre-left   : timer hero, progress, stat cards, token dots, action buttons
  Centre-right  : scrollable detection feed + risk score meter + status bar

FIXES:
  - grid_remove() wrapped in try/except so it's safe before first render
  - _work_btns/_resume_btn are idempotent — safe to call in any order
  - FeedItem icon label centering fixed (place instead of grid)
  - update_state_ui only calls grid ops on already-initialized widgets
  - show_session_summary handles missing 'progress' key gracefully
  - set_risk_score colour thresholds corrected
  - Topbar badge updates properly
  - status_label kept for backward compat (main.py references it)
  - Break countdown hidden at init, shown only during break/lunch
  - _tick delta detection prevents redundant update_state_ui calls
"""

import customtkinter as ctk
from PIL import Image, ImageDraw
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List
import sys
import httpx
import threading
import urllib.request
import io
import webbrowser

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.time_engine import SessionState
from core.config import Config


# ─────────────────────────────────────────────────────────────────
# Notification Manager
# ─────────────────────────────────────────────────────────────────
class NotificationManager:
    """
    Sends Windows OS toast notifications via winotify.
    Falls back silently if winotify is not installed.
    One class, instantiated once by MainWindow.
    """
    def __init__(self):
        self._icon = str(_asset("sentinel.ico"))
        try:
            from winotify import Notification, audio as _audio
            self._Notification = Notification
            self._audio        = _audio
            self._available    = True
        except ImportError:
            self._available = False
            print("[Notifications] winotify not installed — OS toasts disabled.")
            print("[Notifications] Run: pip install winotify")

    def send(self, title: str, msg: str, severity: str = "info") -> None:
        """
        severity: 'ok' | 'warn' | 'crit' | 'info'
        Toasts are rate-limited to 1 per (title+severity) per 60 seconds
        to avoid spamming the user.
        """
        if not self._available:
            return
        threading.Thread(
            target=self._send_bg,
            args=(title, msg, severity),
            daemon=True
        ).start()

    def _send_bg(self, title: str, msg: str, severity: str) -> None:
        try:
            from winotify import Notification, audio
            icon = self._icon if Path(self._icon).exists() else ""
            toast = Notification(
                app_id   = "SENTINEL Monitoring",
                title    = title,
                msg      = msg,
                icon     = icon,
                duration = "short",   # or 'long' for crit
            )
            if severity == "crit":
                toast.set_audio(audio.Reminder, loop=False)
            toast.show()
        except Exception as e:
            print(f"[Notifications] Toast error: {e}")



def _asset(filename: str) -> Path:
    return Path(__file__).parent.parent.parent / "assets" / "iso" / filename


def _load_ctk_image(filename: str, size: tuple) -> Optional[ctk.CTkImage]:
    path = _asset(filename)
    if not path.exists():
        return None
    try:
        pil = Image.open(path).convert("RGBA")
        return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
    except Exception:
        return None


# ── Palette ──────────────────────────────────────────────────
BG0  = "#0B1120"; BG1 = "#0D1526"; BG2 = "#111C2E"
BG3  = "#1A2640"; BORD = "#1E2D45"; BORD2 = "#243450"

GREEN = "#10B981"; AMBER = "#F59E0B"; RED = "#EF4444"
BLUE  = "#60A5FA"; PURP  = "#8B5CF6"

T1 = "#E2E8F0"; T2 = "#94A3B8"; T3 = "#475569"; T4 = "#2D3F55"

G_BG = "#0B1F14"; G_BD = "#0D3320"
A_BG = "#1A1400"; A_BD = "#3B2C00"
R_BG = "#1A0D0D"; R_BD = "#3B1010"
P_BG = "#150D2E"; P_BD = "#2D1A5E"


# ─────────────────────────────────────────────────────────────
# Feed item widget
# ─────────────────────────────────────────────────────────────
class FeedItem(ctk.CTkFrame):
    _PAL = {
        "warn": dict(bg=A_BG, border=A_BD, ibg="#3B2C00", ifg=AMBER, bbg="#3B2C00", bfg=AMBER),
        "ok":   dict(bg=G_BG, border=G_BD, ibg="#0D3320", ifg=GREEN, bbg="#0D3320", bfg=GREEN),
        "info": dict(bg=BG2,  border=BORD, ibg=BG3,       ifg=BLUE,  bbg=BG3,       bfg=BLUE),
        "crit": dict(bg=R_BG, border=R_BD, ibg="#3B1010", ifg=RED,   bbg="#3B1010", bfg=RED),
    }
    _ICO = {"warn": "!", "ok": "✓", "info": "i", "crit": "✕"}

    def __init__(self, parent, kind: str, title: str, meta: str, badge: str, **kw):
        c = self._PAL.get(kind, self._PAL["info"])
        super().__init__(parent, fg_color=c["bg"], border_color=c["border"],
                         border_width=1, corner_radius=8, **kw)
        self.grid_columnconfigure(1, weight=1)

        # icon box
        ico_f = ctk.CTkFrame(self, width=28, height=28,
                              fg_color=c["ibg"], corner_radius=6)
        ico_f.grid(row=0, column=0, rowspan=2, padx=(8, 6), pady=8, sticky="n")
        ico_f.grid_propagate(False)
        ctk.CTkLabel(ico_f, text=self._ICO.get(kind, "i"),
                     font=("Arial", 11, "bold"), text_color=c["ifg"]
                     ).place(relx=0.5, rely=0.5, anchor="center")

        # title row
        tr = ctk.CTkFrame(self, fg_color="transparent")
        tr.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(8, 0))
        tr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tr, text=title, font=("Arial", 11, "bold"),
                     text_color=T1, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(tr, text=badge, font=("Arial", 9),
                     text_color=c["bfg"], fg_color=c["bbg"],
                     corner_radius=8, padx=6, pady=1
                     ).grid(row=0, column=1, padx=(6, 0))

        # meta row
        ctk.CTkLabel(self, text=meta, font=("Arial", 10),
                     text_color=T3, anchor="w"
                     ).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(0, 8))


# ─────────────────────────────────────────────────────────────
# Sidebar nav button
# ─────────────────────────────────────────────────────────────
class NavButton(ctk.CTkFrame):
    def __init__(self, parent, label: str, icon: str,
                 active: bool = False, command: Callable = None, **kw):
        super().__init__(parent, fg_color=BG3 if active else "transparent",
                         corner_radius=8, height=36, **kw)
        self.pack_propagate(False)
        self.grid_columnconfigure(1, weight=1)
        self._cmd = command
        ctk.CTkLabel(self, text=icon, font=("Arial", 13),
                     text_color=BLUE if active else T3, width=16
                     ).grid(row=0, column=0, padx=(10, 0))
        ctk.CTkLabel(self, text=label, font=("Arial", 12),
                     text_color=T1 if active else T3, anchor="w"
                     ).grid(row=0, column=1, sticky="w", padx=8)
        self.bind("<Button-1>", self._click)
        for ch in self.winfo_children():
            ch.bind("<Button-1>", self._click)

    def _click(self, _=None):
        if self._cmd:
            self._cmd()


# ─────────────────────────────────────────────────────────────
# In-app notification banner
# ─────────────────────────────────────────────────────────────
class _NotificationBanner(ctk.CTkFrame):
    """Slim slide-in banner that appears at the top of the content area."""
    _PAL = {
        "warn": (A_BG, A_BD, AMBER, "⚠"),
        "crit": (R_BG, R_BD, RED,   "✕"),
        "ok":   (G_BG, G_BD, GREEN, "✓"),
        "info": (BG2,  BORD, BLUE,  "i"),
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent", height=50, **kw)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        
        # Inner floating pill
        self._pill = ctk.CTkFrame(self, fg_color=A_BG, border_color=A_BD,
                                  border_width=1, corner_radius=18)
        self._pill.grid(row=0, column=0, pady=(16, 0))
        self._pill.grid_columnconfigure(1, weight=1)
        
        self._icon_lbl = ctk.CTkLabel(self._pill, text="⚠", font=("Arial", 16, "bold"),
                                       text_color=AMBER, width=28)
        self._icon_lbl.grid(row=0, column=0, padx=(16, 4), pady=8)
        
        self._msg_lbl  = ctk.CTkLabel(self._pill, text="", font=("Arial", 12, "bold"),
                                       text_color=AMBER, anchor="w")
        self._msg_lbl.grid(row=0, column=1, sticky="w", padx=(2, 8), pady=8)
        
        self._close_btn = ctk.CTkButton(
            self._pill, text="✕", width=26, height=26, corner_radius=13,
            fg_color="transparent", hover_color=BG3, text_color=T3,
            font=("Arial", 11, "bold"), command=self._dismiss)
        self._close_btn.grid(row=0, column=2, padx=(2, 10), pady=8)
        
        self._after_id = None

    def show(self, msg: str, severity: str = "warn", duration_ms: int = 5000, icon: str = None):
        bg, bd, fg, default_icon = self._PAL.get(severity, self._PAL["info"])
        self._pill.configure(fg_color=bg, border_color=bd)
        self._icon_lbl.configure(text=icon or default_icon, text_color=fg)
        self._msg_lbl.configure(text=msg,   text_color=fg)
        self.grid(row=0, column=0, sticky="ew")
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.after(duration_ms, self._dismiss)

    def _dismiss(self):
        try:
            self.grid_remove()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────
class MainWindow(ctk.CTk):
    MAX_FEED = 80

    def __init__(self, user: dict, access_token: str, time_engine=None):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.user         = user
        self.access_token = access_token
        self.time_engine  = time_engine

        # Notification Manager (OS toasts)
        self.notifier = NotificationManager()

        # Callbacks wired by SentinelApp
        self.on_start_session: Optional[Callable] = None
        self.on_end_session:   Optional[Callable] = None
        self.on_take_break:    Optional[Callable] = None
        self.on_end_break:     Optional[Callable] = None
        self.on_take_lunch:    Optional[Callable] = None
        self.on_end_lunch:     Optional[Callable] = None
        self.on_logout:        Optional[Callable] = None

        # Internal state
        self._prev_state  = None
        self._current_risk_score = 0.0
        self._offense_count = 0
        self._prev_tokens = -1
        self._feed_items: List[FeedItem] = []
        # NOTE: _logo_img must be loaded AFTER this CTk window is shown,
        # never in __init__ before the window exists — images are bound
        # to the Tk instance that was active when they were created.
        self._logo_img: Optional[ctk.CTkImage] = None

        # Break card visibility flag — avoids double grid_remove
        self._break_visible = False

        # Track whether action buttons are in "work" or "resume" mode
        # so we don't call grid ops redundantly
        self._btn_mode = "work"   # "work" | "break" | "lunch"

        self.title(f"SENTINEL — {user.get('full_name', 'User')}")
        self.geometry("1140x720")
        self.minsize(940, 640)
        self.configure(fg_color=BG0)

        from utils.assets import set_window_icon
        set_window_icon(self)

        self.update_idletasks()
        w, h = 1140, 720
        self.geometry(
            f"{w}x{h}"
            f"+{(self.winfo_screenwidth()-w)//2}"
            f"+{(self.winfo_screenheight()-h)//2}")

        self._build()
        self._tick()

    # ─────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────
    def _build(self):
        # Load image HERE — after this CTk window is the active Tk root.
        # Loading earlier (e.g. in __init__) binds the PhotoImage to the
        # previous Tk instance (the login window), which is destroyed before
        # MainWindow opens, causing "pyimage doesn't exist" TclError.
        self._logo_img = None
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_mainarea()

    # ── Sidebar ──────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, fg_color=BG1, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(1, weight=1)

        # Brand
        brand = ctk.CTkFrame(sb, height=64, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew")
        brand.grid_propagate(False)
        inner = ctk.CTkFrame(brand, fg_color="transparent")
        inner.place(x=18, rely=0.5, anchor="w")
        
        # Load Skull Logo
        from utils.assets import get_logo_32
        logo_img = get_logo_32()
        
        if logo_img:
            sh = ctk.CTkLabel(inner, image=logo_img, text="")
            sh.pack(side="left", padx=(0, 10))
        else:
            sh = ctk.CTkFrame(inner, width=32, height=32,
                               fg_color="#1E3A6E", corner_radius=8)
            sh.pack(side="left", padx=(0, 10))
            sh.pack_propagate(False)
            ctk.CTkLabel(sh, text="S", font=("Arial", 14, "bold"),
                         text_color=BLUE).place(relx=0.5, rely=0.5, anchor="center")
                         
        ctk.CTkLabel(inner, text="SENTINEL",
                     font=("Arial", 15, "bold"), text_color=T1).pack(side="left")

        # separator
        ctk.CTkFrame(sb, height=1, fg_color=BORD
                     ).grid(row=0, column=0, sticky="ew", pady=(63, 0))

        # Nav
        nav = ctk.CTkFrame(sb, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="nsew", padx=10, pady=12)
        
        self._nav_btns = {}
        self._nav_btns["dashboard"] = NavButton(
            nav, "Session", "⊞", active=True,
            command=lambda: self._show_view("dashboard"))
        self._nav_btns["dashboard"].pack(fill="x", pady=2)

        self._nav_btns["tasks"] = NavButton(
            nav, "Tasks", "✓",
            command=lambda: self._show_view("tasks"))
        self._nav_btns["tasks"].pack(fill="x", pady=2)

        # ── Portal shortcut tabs (open employee portal in default browser) ──
        portal_items = [
            ("portal",    "Dashboard",       "◈", "my/dashboard"),
            ("history",   "Session History", "○", "my/sessions"),
            ("calendar",  "My Calendar",     "▦", "my/calendar"),
            ("myleave",   "Leave & Appeals", "⇑", "my/leave"),
        ]
        for key, label, icon, path in portal_items:
            btn = NavButton(
                nav, label, icon,
                command=lambda p=path: self._open_portal(p))
            btn.pack(fill="x", pady=2)
            self._nav_btns[key] = btn

        # separator
        ctk.CTkFrame(sb, height=1, fg_color=BORD).grid(row=2, column=0, sticky="ew")

        # User card
        uf = ctk.CTkFrame(sb, height=62, fg_color="transparent")
        uf.grid(row=3, column=0, sticky="ew", padx=14, pady=(10, 0))
        uf.grid_propagate(False)
        initials = "".join(p[0].upper() for p in
                           self.user.get("full_name", "?").split()[:2])
        av = ctk.CTkFrame(uf, width=34, height=34,
                           fg_color="#1E3A6E", corner_radius=17)
        av.place(x=0, rely=0.5, anchor="w")
        av.pack_propagate(False)
        self.avatar_lbl = ctk.CTkLabel(av, text=initials, font=("Arial", 11, "bold"), text_color=BLUE)
        self.avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Trigger async image fetch if URL exists
        self._load_avatar_async()
        
        inf = ctk.CTkFrame(uf, fg_color="transparent")
        inf.place(x=44, rely=0.5, anchor="w")
        name = self.user.get("full_name", "User")
        # Truncate long names
        display_name = name if len(name) <= 18 else name[:16] + "…"
        ctk.CTkLabel(inf, text=display_name,
                     font=("Arial", 12, "bold"), text_color=T1).pack(anchor="w")
        ctk.CTkLabel(inf, text=self.user.get("role", "").replace("_", " ").title(),
                     font=("Arial", 10), text_color=T3).pack(anchor="w")

        # Logout button
        ctk.CTkButton(sb, text="Logout", command=self._logout,
                      height=32, fg_color="transparent", hover_color=R_BG,
                      border_color=BORD, border_width=1,
                      text_color=T3, font=("Arial", 11), corner_radius=8
                      ).grid(row=4, column=0, sticky="ew", padx=14, pady=10)

    # ── Avatar Fetching ──────────────────────────────────────
    def _load_avatar_async(self):
        url = self.user.get("avatar_url")
        if not url:
            return
        
        def fetch():
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                
                # Create circular mask
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                
                # Resize to 68x68 for high DPI crispness (downscaled to 34x34)
                size = (68, 68)
                img = img.resize(size, Image.Resampling.LANCZOS)
                
                mask = Image.new("L", size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + size, fill=255)
                
                output = Image.new("RGBA", size, (0, 0, 0, 0))
                output.paste(img, (0, 0), mask)
                
                # Update UI safely on main thread passing the raw PIL image
                self.after(0, lambda: self._apply_avatar(output))
            except Exception as e:
                print(f"Failed to fetch avatar: {e}")

        threading.Thread(target=fetch, daemon=True).start()
        
    def _apply_avatar(self, raw_pil_image):
        if hasattr(self, 'avatar_lbl'):
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(image=raw_pil_image, master=self)
            self.avatar_lbl.configure(text="", image=photo)
            self._avatar_ctk_img = photo # Keep ref so it isn't garbage collected

    def _open_portal(self, path: str) -> None:
        """
        Open a portal page in the user's default browser.
        The JWT is embedded in the URL hash fragment — fragments are
        never sent to the server, so the token won't appear in access
        logs. The authStore reads it on page load, hydrates itself,
        then immediately clears it from the URL.

        Format:  https://portal.example.com/my/sessions#token=eyJ...
        """
        token = getattr(self, "access_token", "") or ""
        base  = Config.PORTAL_URL.rstrip("/")
        url   = f"{base}/{path}"
        if token:
            url = f"{url}#token={token}"
        threading.Thread(
            target=lambda: webbrowser.open(url),
            daemon=True
        ).start()

    # ── Main area ─────────────────────────────────────────────
    def _build_mainarea(self):

        main = ctk.CTkFrame(self, fg_color=BG0, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)
        self._build_topbar(main)
        self._build_content(main)

    def _build_topbar(self, parent):
        tb = ctk.CTkFrame(parent, height=48, fg_color=BG1, corner_radius=0)
        tb.grid(row=0, column=0, sticky="ew")
        tb.grid_propagate(False)
        tb.grid_columnconfigure(3, weight=1)

        self.session_badge = ctk.CTkLabel(
            tb, text="● Not started", font=("Arial", 11, "bold"),
            text_color=T3, fg_color=BG3, corner_radius=12, padx=12, pady=4)
        self.session_badge.grid(row=0, column=0, padx=(16, 8), pady=10)

        self.alert_badge = ctk.CTkLabel(
            tb, text="No alerts", font=("Arial", 11),
            text_color=T3, fg_color=BG3, corner_radius=12, padx=12, pady=4)
        self.alert_badge.grid(row=0, column=1, padx=(0, 8), pady=10)

        # spacer
        ctk.CTkFrame(tb, fg_color="transparent").grid(row=0, column=3, sticky="ew")

        self.sync_label = ctk.CTkLabel(
            tb, text="Idle", font=("Arial", 10), text_color=T3)
        self.sync_label.grid(row=0, column=4, padx=(0, 16))

        self._right_panel_view = "feed" # "feed" or "alerts"

        self._right_panel_view = "feed" # "feed" or "alerts"

    def _build_content(self, parent):
        self.content_container = ctk.CTkFrame(parent, fg_color=BG0, corner_radius=0)
        self.content_container.grid(row=1, column=0, sticky="nsew")
        self.content_container.grid_rowconfigure(1, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # ── Notification banner (slides in below topbar) ────
        self._notif_banner = _NotificationBanner(self.content_container)
        # starts hidden; shown by show_banner()

        # Dashboard View
        self.dashboard_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.dashboard_frame.grid_rowconfigure(0, weight=1)
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_frame.grid_columnconfigure(1, minsize=340)
        self._alert_history = []
        self._build_left(self.dashboard_frame)
        self._build_right(self.dashboard_frame)

        # Tasks View
        self.tasks_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.tasks_frame.grid_rowconfigure(1, weight=1)
        self.tasks_frame.grid_columnconfigure(0, weight=1)
        self._tasks_data = []
        self._tasks_loading = False
        self._build_tasks_view()

        self._show_view("dashboard")

    def _toggle_alerts_panel(self):
        if self._right_panel_view == "feed":
            self.feed_container.grid_remove()
            self.alerts_container.grid(row=0, column=0, rowspan=10, sticky="nsew")
            self._right_panel_view = "alerts"
        else:
            self.alerts_container.grid_remove()
            self.feed_container.grid(row=0, column=0, rowspan=10, sticky="nsew")
            self._right_panel_view = "feed"

    def _show_view(self, view_name: str):
        for f in [self.dashboard_frame, self.tasks_frame]:
            try:
                f.grid_remove()
            except Exception:
                pass

        # Reset nav buttons
        if hasattr(self, '_nav_btns'):
            for name, btn in self._nav_btns.items():
                for ch in btn.winfo_children():
                    if isinstance(ch, ctk.CTkLabel):
                        ch.configure(text_color=T3)
                btn.configure(fg_color="transparent")

        if view_name == "dashboard":
            self.dashboard_frame.grid(row=1, column=0, sticky="nsew")
        elif view_name == "tasks":
            self.tasks_frame.grid(row=1, column=0, sticky="nsew")
            self._fetch_tasks()

        if hasattr(self, '_nav_btns') and view_name in self._nav_btns:
            btn = self._nav_btns[view_name]
            btn.configure(fg_color=BG3)
            for ch in btn.winfo_children():
                if isinstance(ch, ctk.CTkLabel):
                    if ch.cget("width") == 16:
                        ch.configure(text_color=BLUE)
                    else:
                        ch.configure(text_color=T1)


    # ── Tasks View ───────────────────────────────────────────
    def _build_tasks_view(self):
        """Build the native Tasks tab."""
        tf = self.tasks_frame

        # Header bar
        hdr = ctk.CTkFrame(tf, height=56, fg_color=BG1, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="MY TASKS",
                     font=("Arial", 14, "bold"), text_color=T1
                     ).grid(row=0, column=0, padx=20, pady=14, sticky="w")
        ctk.CTkLabel(hdr, text="Assigned by your manager",
                     font=("Arial", 10), text_color=T3
                     ).grid(row=0, column=1, padx=0, pady=14, sticky="w")

        self._tasks_refresh_btn = ctk.CTkButton(
            hdr, text="↻ Refresh", width=80, height=28, corner_radius=6,
            font=("Arial", 10, "bold"), fg_color=BG3, hover_color=BORD2,
            text_color=T2, border_width=0,
            command=lambda: self._fetch_tasks())
        self._tasks_refresh_btn.grid(row=0, column=2, padx=(0, 20), pady=14)

        # Scrollable task list
        self._tasks_scroll = ctk.CTkScrollableFrame(
            tf, fg_color=BG0, corner_radius=0, scrollbar_button_color=BG3)
        self._tasks_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._tasks_scroll.grid_columnconfigure(0, weight=1)

        # Placeholder
        self._tasks_empty = ctk.CTkLabel(
            self._tasks_scroll,
            text="No tasks assigned\nYou're all caught up ✓",
            font=("Arial", 12), text_color=T3, justify="center")
        self._tasks_empty.grid(row=0, column=0, pady=60)

    # ── Task Cards ──────────────────────────────────────────
    _PRIORITY_COLORS = {
        "low":    {"dot": GREEN, "bg": G_BG, "bd": G_BD},
        "medium": {"dot": AMBER, "bg": A_BG, "bd": A_BD},
        "high":   {"dot": "#F97316", "bg": "#1A1000", "bd": "#3B2200"},
        "urgent": {"dot": RED,   "bg": R_BG, "bd": R_BD},
    }

    def _render_tasks(self):
        """Destroy old task cards and render fresh from self._tasks_data."""
        for w in self._tasks_scroll.winfo_children():
            w.destroy()

        if not self._tasks_data:
            self._tasks_empty = ctk.CTkLabel(
                self._tasks_scroll,
                text="No tasks assigned\nYou're all caught up ✓",
                font=("Arial", 12), text_color=T3, justify="center")
            self._tasks_empty.grid(row=0, column=0, pady=60)
            return

        for idx, task in enumerate(self._tasks_data):
            self._render_task_card(idx, task)

    def _render_task_card(self, idx: int, task: dict):
        """Render a single task card."""
        pc = self._PRIORITY_COLORS.get(task.get("priority", "medium"),
                                        self._PRIORITY_COLORS["medium"])
        is_done = task.get("status") == "completed"
        is_active = task.get("status") == "in_progress"

        card = ctk.CTkFrame(
            self._tasks_scroll,
            fg_color=G_BG if is_done else BG2,
            border_color=G_BD if is_done else BORD,
            border_width=1, corner_radius=10)
        card.grid(row=idx, column=0, sticky="ew", padx=16, pady=(8, 0))
        card.grid_columnconfigure(1, weight=1)

        # Priority dot
        dot = ctk.CTkFrame(card, width=10, height=10,
                            fg_color=pc["dot"], corner_radius=5)
        dot.grid(row=0, column=0, rowspan=3, padx=(14, 8), pady=14, sticky="n")
        dot.grid_propagate(False)

        # Title row
        title_f = ctk.CTkFrame(card, fg_color="transparent")
        title_f.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 0))
        title_f.grid_columnconfigure(0, weight=1)

        title_color = GREEN if is_done else T1
        ctk.CTkLabel(title_f, text=task.get("title", "Untitled"),
                     font=("Arial", 12, "bold"), text_color=title_color,
                     anchor="w").grid(row=0, column=0, sticky="w")

        # Priority badge
        pri_text = task.get("priority", "medium").upper()
        ctk.CTkLabel(title_f, text=pri_text,
                     font=("Arial", 8, "bold"), text_color=pc["dot"],
                     fg_color=pc["bg"], corner_radius=4, padx=6, pady=1
                     ).grid(row=0, column=1, padx=(8, 0))

        # Status badge
        status_map = {"pending": ("PENDING", T3, BG3),
                      "in_progress": ("IN PROGRESS", BLUE, "#0D1F3E"),
                      "completed": ("COMPLETED", GREEN, G_BG)}
        st_label, st_color, st_bg = status_map.get(
            task.get("status", "pending"), ("PENDING", T3, BG3))
        ctk.CTkLabel(title_f, text=st_label,
                     font=("Arial", 8, "bold"), text_color=st_color,
                     fg_color=st_bg, corner_radius=4, padx=6, pady=1
                     ).grid(row=0, column=2, padx=(6, 0))

        # Description (if any)
        desc = task.get("description", "")
        if desc:
            ctk.CTkLabel(card, text=desc[:120] + ("…" if len(desc) > 120 else ""),
                         font=("Arial", 10), text_color=T3, anchor="w",
                         wraplength=450
                         ).grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(2, 0))

        # Meta row: due date, completion note
        meta_f = ctk.CTkFrame(card, fg_color="transparent")
        meta_f.grid(row=2, column=1, sticky="w", padx=(0, 12), pady=(4, 12))

        due = task.get("due_date")
        if due:
            try:
                d = datetime.fromisoformat(due.replace("Z", "+00:00"))
                due_str = d.strftime("%b %d")
            except Exception:
                due_str = due[:10]
            ctk.CTkLabel(meta_f, text=f"DUE: {due_str}",
                         font=("Arial", 9), text_color=T3).pack(side="left", padx=(0, 12))

        if is_done and task.get("completion_note"):
            ctk.CTkLabel(meta_f, text=f'Note: "{task["completion_note"]}"',
                         font=("Arial", 9), text_color=GREEN).pack(side="left")

        # Action buttons (not shown for completed tasks)
        if not is_done:
            btn_f = ctk.CTkFrame(card, fg_color="transparent")
            btn_f.grid(row=0, column=2, rowspan=3, padx=(0, 14), pady=14, sticky="ne")

            if not is_active:
                ctk.CTkButton(
                    btn_f, text="START", width=60, height=28, corner_radius=6,
                    font=("Arial", 9, "bold"),
                    fg_color="#0D1F3E", hover_color="#16305A",
                    text_color=BLUE, border_color="#1E3A6E", border_width=1,
                    command=lambda tid=task["id"]: self._task_action(tid, "in_progress")
                ).pack(pady=(0, 4))

            ctk.CTkButton(
                btn_f, text="DONE ✓", width=60, height=28, corner_radius=6,
                font=("Arial", 9, "bold"),
                fg_color=G_BG, hover_color="#0F2A1A",
                text_color=GREEN, border_color=G_BD, border_width=1,
                command=lambda tid=task["id"], ttl=task.get("title", ""): self._task_complete_dialog(tid, ttl)
            ).pack()

    # ── Task API calls ──────────────────────────────────────
    def _fetch_tasks(self):
        """Fetch tasks from backend in background thread."""
        if self._tasks_loading:
            return
        self._tasks_loading = True

        def _run():
            try:
                url = f"{Config.API_BASE_URL}/api/v1/tasks/my"
                headers = {"Authorization": f"Bearer {self.access_token}",
                           "Content-Type": "application/json"}
                with httpx.Client(timeout=10.0) as client:
                    r = client.get(url, headers=headers)
                if r.status_code == 200:
                    tasks = r.json().get("tasks", [])
                    self.after(0, lambda t=tasks: self._on_tasks_loaded(t))
                else:
                    print(f"Tasks fetch error: {r.status_code}")
                    self.after(0, lambda: self._on_tasks_loaded([]))
            except Exception as e:
                print(f"Tasks fetch error: {e}")
                self.after(0, lambda: self._on_tasks_loaded([]))
            finally:
                self._tasks_loading = False

        threading.Thread(target=_run, daemon=True).start()

    def _on_tasks_loaded(self, tasks: list):
        self._tasks_data = tasks
        self._render_tasks()

    def _task_action(self, task_id: str, status: str, note: str = ""):
        """PATCH task status in background."""
        def _run():
            try:
                url = f"{Config.API_BASE_URL}/api/v1/tasks/{task_id}/status"
                headers = {"Authorization": f"Bearer {self.access_token}",
                           "Content-Type": "application/json"}
                body = {"status": status}
                if note:
                    body["completion_note"] = note
                with httpx.Client(timeout=10.0) as client:
                    r = client.patch(url, headers=headers, json=body)
                if r.status_code == 200:
                    updated = r.json().get("task", {})
                    self.after(0, lambda: self._update_single_task(updated))
                    if status == "completed":
                        self.after(0, lambda: self.show_banner(
                            "Task marked complete! 🎉", severity="ok", duration_ms=4000))
                    else:
                        self.after(0, lambda: self.show_banner(
                            "Task started", severity="info", duration_ms=3000))
                else:
                    print(f"Task update error: {r.status_code}")
                    self.after(0, lambda: self.show_banner(
                        "Failed to update task", severity="crit", duration_ms=4000))
            except Exception as e:
                print(f"Task update error: {e}")
                self.after(0, lambda: self.show_banner(
                    "Failed to update task", severity="crit", duration_ms=4000))

        threading.Thread(target=_run, daemon=True).start()

    def _update_single_task(self, updated: dict):
        """Update a single task in self._tasks_data and re-render."""
        for i, t in enumerate(self._tasks_data):
            if t.get("id") == updated.get("id"):
                self._tasks_data[i] = updated
                break
        self._render_tasks()

    def _task_complete_dialog(self, task_id: str, title: str):
        """Show completion-note dialog before marking done."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Mark as Complete")
        dlg.geometry("400x240")
        dlg.resizable(False, False)
        dlg.configure(fg_color=BG1)
        dlg.transient(self)
        dlg.grab_set()
        ico = _asset("sentinel.ico")
        if ico.exists():
            try:
                dlg.iconbitmap(str(ico))
            except Exception:
                pass
        dlg.update_idletasks()
        dlg.geometry(
            f"400x240"
            f"+{(dlg.winfo_screenwidth()-400)//2}"
            f"+{(dlg.winfo_screenheight()-240)//2}")

        ctk.CTkLabel(dlg, text="Mark as Complete",
                     font=("Arial", 15, "bold"), text_color=GREEN
                     ).pack(pady=(18, 4))
        ctk.CTkLabel(dlg, text=title[:60],
                     font=("Arial", 11), text_color=T2
                     ).pack(pady=(0, 12))

        note_entry = ctk.CTkTextbox(
            dlg, height=60, fg_color=BG2, border_color=BORD,
            border_width=1, corner_radius=8, text_color=T1,
            font=("Arial", 11))
        note_entry.pack(fill="x", padx=24, pady=(0, 14))
        note_entry.insert("1.0", "")

        btn_f = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_f.pack(fill="x", padx=24, pady=(0, 18))
        btn_f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_f, text="Cancel", height=36, corner_radius=8,
            fg_color="transparent", hover_color=BG3,
            text_color=T3, border_color=BORD, border_width=1,
            font=("Arial", 11), command=dlg.destroy
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        def _confirm():
            note = note_entry.get("1.0", "end").strip()
            dlg.destroy()
            self._task_action(task_id, "completed", note)

        ctk.CTkButton(
            btn_f, text="✓ Confirm Done", height=36, corner_radius=8,
            fg_color=G_BG, hover_color="#0F2A1A",
            text_color=GREEN, border_color=G_BD, border_width=1,
            font=("Arial", 11, "bold"), command=_confirm
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def refresh_tasks(self):
        """Public API — called by SentinelApp when a task_assigned WS event arrives."""
        self._fetch_tasks()

    # ── Left panel ───────────────────────────────────────────
    def _build_left(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color=BG0, corner_radius=0,
                                       scrollbar_button_color=BG3)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_columnconfigure(0, weight=1)
        self._left_frame = left

        # ── Timer card
        tc = ctk.CTkFrame(left, fg_color=BG1, corner_radius=14,
                           border_color=BORD, border_width=1)
        tc.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        tc.grid_columnconfigure(0, weight=1)

        self.state_badge = ctk.CTkLabel(
            tc, text="● Not started", font=("Arial", 11, "bold"),
            text_color=T3, fg_color=BG3, corner_radius=12, padx=14, pady=5)
        self.state_badge.grid(row=0, column=0, pady=(22, 12))

        ctk.CTkLabel(tc, text="WORK TIME TODAY",
                     font=("Arial", 9, "bold"), text_color=T3).grid(row=1, column=0)

        self.work_timer = ctk.CTkLabel(
            tc, text="00:00:00", font=("Arial", 60, "bold"), text_color=GREEN)
        self.work_timer.grid(row=2, column=0, pady=(4, 4))

        self.session_sub = ctk.CTkLabel(
            tc, text="Start a session to begin tracking",
            font=("Arial", 10), text_color=T3)
        self.session_sub.grid(row=3, column=0, pady=(0, 16))

        # Progress bar
        pw = ctk.CTkFrame(tc, fg_color="transparent")
        pw.grid(row=4, column=0, sticky="ew", padx=28, pady=(0, 10))
        pw.grid_columnconfigure(0, weight=1)
        self.progress_bar = ctk.CTkProgressBar(
            pw, height=8, corner_radius=4,
            progress_color=GREEN, fg_color=BG3)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        pr = ctk.CTkFrame(pw, fg_color="transparent")
        pr.grid(row=1, column=0, sticky="ew")
        pr.grid_columnconfigure(1, weight=1)
        self.prog_left = ctk.CTkLabel(pr, text="0 / 400 min",
                                       font=("Arial", 10), text_color=T3)
        self.prog_left.grid(row=0, column=0, sticky="w")
        self.prog_pct = ctk.CTkLabel(pr, text="0%",
                                      font=("Arial", 10), text_color=T3)
        self.prog_pct.grid(row=0, column=2, sticky="e")

        # Start/end button
        self.session_btn = ctk.CTkButton(
            tc, text="Start session", command=self._toggle_session,
            height=48, corner_radius=10,
            fg_color=G_BG, hover_color="#0F2A1A",
            text_color=GREEN, border_color=G_BD, border_width=1,
            font=("Arial", 14, "bold"))
        self.session_btn.grid(row=5, column=0, sticky="ew",
                              padx=28, pady=(12, 24))

        # ── Stat cards
        sf = ctk.CTkFrame(left, fg_color="transparent")
        sf.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        sf.grid_columnconfigure((0, 1, 2), weight=1)
        self._stat_labels = {}
        for i, (lbl, val, colour, key) in enumerate([
            ("Work",  "0m", GREEN, "work"),
            ("Break", "0m", AMBER, "break"),
            ("Idle",  "0m", RED,   "idle"),
        ]):
            sc = ctk.CTkFrame(sf, fg_color=BG1, corner_radius=10,
                               border_color=BORD, border_width=1)
            sc.grid(row=0, column=i, sticky="ew",
                    padx=(0 if i == 0 else 6, 6 if i < 2 else 0))
            ctk.CTkLabel(sc, text=lbl.upper(),
                         font=("Arial", 9, "bold"), text_color=T3).pack(pady=(12, 3))
            vl = ctk.CTkLabel(sc, text=val,
                               font=("Arial", 22, "bold"), text_color=colour)
            vl.pack(pady=(0, 12))
            self._stat_labels[key] = vl

        # ── Break tokens
        tk_c = ctk.CTkFrame(left, fg_color=BG1, corner_radius=10,
                             border_color=BORD, border_width=1)
        tk_c.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        tk_hdr = ctk.CTkFrame(tk_c, fg_color="transparent")
        tk_hdr.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(tk_hdr, text="BREAK TOKENS",
                     font=("Arial", 9, "bold"), text_color=T3).pack(side="left")
        ctk.CTkLabel(tk_hdr, text="Refreshes hourly",
                     font=("Arial", 9), text_color=T3).pack(side="right")
        tk_row = ctk.CTkFrame(tk_c, fg_color="transparent")
        tk_row.pack(fill="x", padx=16, pady=(0, 12))
        self._token_dots: List[ctk.CTkFrame] = []
        for _ in range(3):
            d = ctk.CTkFrame(tk_row, width=12, height=12,
                              fg_color=BG3, corner_radius=6)
            d.pack(side="left", padx=(0, 6))
            d.pack_propagate(False)
            self._token_dots.append(d)
        self._token_lbl = ctk.CTkLabel(tk_row, text="0 of 3 available",
                                        font=("Arial", 10), text_color=T3)
        self._token_lbl.pack(side="left", padx=(8, 0))

        # ── Break countdown card (hidden initially)
        self._break_card = ctk.CTkFrame(left, fg_color=A_BG, corner_radius=10,
                                         border_color=A_BD, border_width=1)
        # Not gridded at start — _show_bc() grids it when needed
        ctk.CTkLabel(self._break_card, text="TIME REMAINING",
                     font=("Arial", 9, "bold"), text_color=AMBER).pack(pady=(12, 2))
        self.break_countdown = ctk.CTkLabel(
            self._break_card, text="10:00",
            font=("Arial", 36, "bold"), text_color=AMBER)
        self.break_countdown.pack()
        self.break_prog = ctk.CTkProgressBar(
            self._break_card, height=5, corner_radius=3,
            progress_color=AMBER, fg_color=BG3)
        self.break_prog.set(1.0)
        self.break_prog.pack(fill="x", padx=20, pady=(6, 14))

        # ── Action buttons frame
        self._btn_f = ctk.CTkFrame(left, fg_color="transparent")
        self._btn_f.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        self._btn_f.grid_columnconfigure((0, 1), weight=1)

        # Break button
        self.break_btn = ctk.CTkButton(
            self._btn_f, text="Take break (10 min)",
            command=self._take_break, height=44,
            font=("Arial", 12, "bold"), corner_radius=10,
            fg_color=A_BG, hover_color="#2A1F00",
            text_color=AMBER, border_color=A_BD, border_width=1,
            state="disabled")
        self.break_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # Lunch button
        self.lunch_btn = ctk.CTkButton(
            self._btn_f, text="Lunch (30 min)",
            command=self._take_lunch, height=44,
            font=("Arial", 12, "bold"), corner_radius=10,
            fg_color=P_BG, hover_color="#1D1040",
            text_color=PURP, border_color=P_BD, border_width=1,
            state="disabled")
        self.lunch_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Resume buttons (not gridded at start)
        self.end_break_btn = ctk.CTkButton(
            self._btn_f, text="Resume work",
            command=self._end_break, height=44,
            font=("Arial", 12, "bold"), corner_radius=10,
            fg_color=G_BG, hover_color="#0F2A1A",
            text_color=GREEN, border_color=G_BD, border_width=1)

        self.end_lunch_btn = ctk.CTkButton(
            self._btn_f, text="Resume work",
            command=self._end_lunch, height=44,
            font=("Arial", 12, "bold"), corner_radius=10,
            fg_color=G_BG, hover_color="#0F2A1A",
            text_color=GREEN, border_color=G_BD, border_width=1)

    # ── Right panel ──────────────────────────────────────────
    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color=BG1, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(1, weight=1)

        # left separator line
        ctk.CTkFrame(right, width=1, fg_color=BORD
                     ).grid(row=0, column=0, rowspan=10, sticky="ns")

        # ── Right panel wrapper
        self.right_wrapper = ctk.CTkFrame(right, fg_color="transparent")
        self.right_wrapper.grid(row=0, column=1, rowspan=10, sticky="nsew")
        self.right_wrapper.grid_rowconfigure(0, weight=1)
        self.right_wrapper.grid_columnconfigure(0, weight=1)

        # ── Feed Container ──
        self.feed_container = ctk.CTkFrame(self.right_wrapper, fg_color="transparent")
        self.feed_container.grid(row=0, column=0, sticky="nsew")
        self.feed_container.grid_rowconfigure(2, weight=1)
        self.feed_container.grid_columnconfigure(0, weight=1)

        # Feed header
        hdr = ctk.CTkFrame(self.feed_container, height=44, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=(1, 0))
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="DETECTION FEED", font=("Arial", 10, "bold"), text_color=T3).grid(row=0, column=0, sticky="w", padx=16, pady=12)
        self._feed_count_lbl = ctk.CTkLabel(hdr, text="", font=("Arial", 10), text_color=T3)
        self._feed_count_lbl.grid(row=0, column=1, sticky="w", padx=(0, 12))

        # Toggle button in the right side of the Feed header
        self.feed_to_alerts_btn = ctk.CTkButton(
            hdr, text="🔔 Alerts", command=self._toggle_alerts_panel,
            font=("Arial", 11, "bold"), text_color=T3, fg_color="transparent",
            hover_color=BG3, width=64, height=28, corner_radius=6
        )
        self.feed_to_alerts_btn.grid(row=0, column=2, padx=(0, 16))

        ctk.CTkFrame(self.feed_container, height=1, fg_color=BORD).grid(row=1, column=0, sticky="ew", padx=(1, 0))

        # Scrollable feed
        self.feed_frame = ctk.CTkScrollableFrame(self.feed_container, fg_color="transparent", scrollbar_button_color=BG3, corner_radius=0)
        self.feed_frame.grid(row=2, column=0, sticky="nsew", padx=(1, 0))
        self.feed_frame.grid_columnconfigure(0, weight=1)

        self._feed_ph = ctk.CTkLabel(self.feed_frame, text="Detection events will appear\nhere once a session is active.", font=("Arial", 11), text_color=T3, justify="center")
        self._feed_ph.grid(row=0, column=0, pady=40)

        ctk.CTkFrame(self.feed_container, height=1, fg_color=BORD).grid(row=3, column=0, sticky="ew", padx=(1, 0))

        # Risk score
        rf = ctk.CTkFrame(self.feed_container, fg_color="transparent")
        rf.grid(row=4, column=0, sticky="ew", padx=(1, 0))
        rf.grid_columnconfigure(0, weight=1)
        rh = ctk.CTkFrame(rf, fg_color="transparent")
        rh.pack(fill="x", padx=16, pady=(12, 8))
        ctk.CTkLabel(rh, text="RISK SCORE", font=("Arial", 10, "bold"), text_color=T3).pack(side="left")
        self.risk_val = ctk.CTkLabel(rh, text="0 / 100", font=("Arial", 18, "bold"), text_color=GREEN)
        self.risk_val.pack(side="right")
        self.risk_bar = ctk.CTkProgressBar(rf, height=8, corner_radius=4, progress_color=GREEN, fg_color=BG3)
        self.risk_bar.set(0)
        self.risk_bar.pack(fill="x", padx=16, pady=(0, 6))
        rl = ctk.CTkFrame(rf, fg_color="transparent")
        rl.pack(fill="x", padx=16, pady=(0, 12))
        for lbl in ["Low", "Medium", "High", "Critical"]:
            ctk.CTkLabel(rl, text=lbl, font=("Arial", 9), text_color=T3).pack(side="left", expand=True)

        ctk.CTkFrame(self.feed_container, height=1, fg_color=BORD).grid(row=5, column=0, sticky="ew", padx=(1, 0))

        # Status bar
        bot = ctk.CTkFrame(self.feed_container, height=30, fg_color="#080F1D", corner_radius=0)
        bot.grid(row=6, column=0, sticky="ew", padx=(1, 0))
        bot.grid_propagate(False)
        bot.grid_columnconfigure(1, weight=1)
        self._online_dot = ctk.CTkFrame(bot, width=8, height=8, fg_color=GREEN, corner_radius=4)
        self._online_dot.grid(row=0, column=0, padx=(12, 6), pady=10)
        self._online_dot.grid_propagate(False)

        # status_label kept for backward compat — main.py references it
        self.status_label = ctk.CTkLabel(bot, text="Ready", font=("Arial", 10), text_color=T3, anchor="w")
        self.status_label.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(bot, text="v1.0.0", font=("Arial", 10), text_color=T3).grid(row=0, column=2, padx=(0, 12))

        # ── Alerts Container ──
        self.alerts_container = ctk.CTkFrame(self.right_wrapper, fg_color="transparent")
        self.alerts_container.grid_rowconfigure(2, weight=1)
        self.alerts_container.grid_columnconfigure(0, weight=1)
        
        hdr_alert = ctk.CTkFrame(self.alerts_container, height=44, fg_color="transparent")
        hdr_alert.grid(row=0, column=0, sticky="ew", padx=(1, 0))
        hdr_alert.grid_propagate(False)
        hdr_alert.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr_alert, text="ALERT MESSAGES", font=("Arial", 10, "bold"), text_color=T3).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        # Toggle button in the right side of the Alerts header
        self.alerts_to_feed_btn = ctk.CTkButton(
            hdr_alert, text="⊞ Feed", command=self._toggle_alerts_panel,
            font=("Arial", 11, "bold"), text_color=T3, fg_color="transparent",
            hover_color=BG3, width=64, height=28, corner_radius=6
        )
        self.alerts_to_feed_btn.grid(row=0, column=1, padx=(0, 16))

        ctk.CTkFrame(self.alerts_container, height=1, fg_color=BORD).grid(row=1, column=0, sticky="ew", padx=(1, 0))

        self.alerts_scroll = ctk.CTkScrollableFrame(self.alerts_container, fg_color="transparent", scrollbar_button_color=BG3, corner_radius=0)
        self.alerts_scroll.grid(row=2, column=0, sticky="nsew", padx=0)
        self.alerts_scroll.grid_columnconfigure(0, weight=1)

        self.alerts_empty = ctk.CTkLabel(self.alerts_scroll, text="No alerts received yet.", font=("Arial", 11), text_color=T3, justify="center")
        self.alerts_empty.pack(pady=40)

    # ─────────────────────────────────────────────────────────
    # PUBLIC API — called by SentinelApp (main.py)
    # ─────────────────────────────────────────────────────────

    def update_state_ui(self, state: SessionState, data: dict):
        """Update all UI elements to reflect the new session state."""
        tokens = data.get("break_tokens", 0)
        lunch  = data.get("lunch_taken",  False)

        if state == SessionState.WORKING:
            self._set_badge("Working", GREEN, G_BG, G_BD)
            self.session_btn.configure(
                text="End session",
                fg_color=R_BG, hover_color="#2A0D0D",
                text_color=RED, border_color=R_BD, border_width=1)
            self.session_sub.configure(
                text="Session active · detection running")
            self.break_btn.configure(
                state="normal" if tokens > 0 else "disabled")
            self.lunch_btn.configure(
                state="disabled" if lunch else "normal")
            self._set_work_buttons()
            self._hide_break_card()

        elif state == SessionState.ON_BREAK:
            self._set_badge("On break", AMBER, A_BG, A_BD)
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self.session_sub.configure(text="Break · work timer paused")
            self._set_resume_button(self.end_break_btn)
            self._show_break_card(AMBER, A_BG, A_BD)

        elif state == SessionState.ON_LUNCH:
            self._set_badge("Lunch", PURP, P_BG, P_BD)
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self.session_sub.configure(text="Lunch break · work timer paused")
            self._set_resume_button(self.end_lunch_btn)
            self._show_break_card(PURP, P_BG, P_BD)

        elif state == SessionState.IDLE:
            self._set_badge("Not started", T3, BG3, BORD)
            self.session_btn.configure(
                text="Start session",
                fg_color=G_BG, hover_color="#0F2A1A",
                text_color=GREEN, border_color=G_BD, border_width=1)
            self.session_sub.configure(
                text="Start a session to begin tracking")
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self._set_work_buttons()
            self._hide_break_card()

        elif state == SessionState.ENDED:
            self._set_badge("Session ended", T3, BG3, BORD)
            self.session_btn.configure(
                text="Start session",
                fg_color=G_BG, hover_color="#0F2A1A",
                text_color=GREEN, border_color=G_BD, border_width=1)
            self.session_sub.configure(text="Session complete")
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self._set_work_buttons()
            self._hide_break_card()

        self._update_token_dots(tokens)
        self._token_lbl.configure(text=f"{tokens} of 3 available")

    def notify(self, title: str, msg: str, severity: str = "info"):
        """Send an OS toast notification."""
        if hasattr(self, "notifier"):
            self.notifier.send(title, msg, severity)

    def show_banner(self, msg: str, severity: str = "warn", duration_ms: int = 5000, is_admin_alert: bool = False):
        """Show an in-app slide-down banner and optionally log it to Alerts if from Admin."""
        if is_admin_alert:
            import datetime
            ts = datetime.datetime.now().strftime("%I:%M %p")
            self._alert_history.insert(0, {"msg": msg, "severity": severity, "time": ts})
            self._refresh_alerts_view()
        
        if hasattr(self, "_notif_banner"):
            self._notif_banner.show(msg, severity, duration_ms, icon="🔔" if is_admin_alert else None)

    def _refresh_alerts_view(self):
        if not hasattr(self, 'alerts_scroll'): return
        for child in self.alerts_scroll.winfo_children():
            # Don't destroy the empty label yet if we plan to show it
            if child != getattr(self, 'alerts_empty', None):
                child.destroy()
            
        if not getattr(self, '_alert_history', []):
            if hasattr(self, 'alerts_empty'):
                self.alerts_empty.pack(pady=40)
            return

        if hasattr(self, 'alerts_empty') and self.alerts_empty.winfo_ismapped():
            self.alerts_empty.pack_forget()

        for alert in self._alert_history:
            card = ctk.CTkFrame(self.alerts_scroll, fg_color="transparent")
            card.pack(fill="x", pady=8, padx=12)
            card.grid_columnconfigure(1, weight=1)
            
            # YouTube-style Avatar/Icon circle
            icon_color = BLUE if alert['severity'] == 'info' else RED
            avatar_frame = ctk.CTkFrame(card, width=36, height=36, corner_radius=18, fg_color=icon_color)
            avatar_frame.grid(row=0, column=0, rowspan=2, sticky="n", pady=2, padx=(0, 12))
            avatar_frame.grid_propagate(False) # lock size
            avatar_frame.grid_columnconfigure(0, weight=1)
            avatar_frame.grid_rowconfigure(0, weight=1)
            
            ctk.CTkLabel(avatar_frame, text="🔔", font=("Arial", 14), text_color="white").grid(row=0, column=0)
            
            # Message and Time Stack
            ctk.CTkLabel(card, text=alert['msg'], font=("Roboto", 13), text_color=T1, justify="left", wraplength=250).grid(row=0, column=1, sticky="w", pady=(0, 4))
            ctk.CTkLabel(card, text=alert['time'], font=("Roboto", 11), text_color=T3).grid(row=1, column=1, sticky="w")
            
            # YouTube-style subtle separator line at the bottom
            ctk.CTkFrame(card, height=1, fg_color=BORD).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    def add_feed_item(self, kind: str, title: str, meta: str, badge: str):
        """Add a detection event to the feed (newest at top)."""
        # Remove placeholder
        try:
            if self._feed_ph.winfo_exists() and self._feed_ph.winfo_ismapped():
                self._feed_ph.grid_remove()
        except Exception:
            pass

        # Shift existing items down
        for fi in self._feed_items:
            try:
                if fi.winfo_exists():
                    info = fi.grid_info()
                    if info:
                        fi.grid(row=int(info.get("row", 0)) + 1)
            except Exception:
                pass

        # Insert new item at top
        fi = FeedItem(self.feed_frame, kind=kind, title=title,
                      meta=meta, badge=badge)
        fi.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))
        self._feed_items.insert(0, fi)

        # Prune old items
        while len(self._feed_items) > self.MAX_FEED:
            old = self._feed_items.pop()
            try:
                if old.winfo_exists():
                    old.destroy()
            except Exception:
                pass

        self._feed_count_lbl.configure(text=f"{len(self._feed_items)} events")
        self._update_alert_badge()

        # Always trigger in-app banner for warnings and criticals
        if kind in ("warn", "crit"):
            self.show_banner(f"{title} - {badge}", severity=kind, duration_ms=6000)
            
            # Throttle OS toasts: only ring if risk > 50 or 3 consecutive offenses
            self._offense_count += 1
            if self._current_risk_score > 50 or self._offense_count >= 3:
                self.notify(title, meta, severity=kind)
                self._offense_count = 0  # reset after ringing to avoid spam
        elif kind == "info":
            # Taking an action that isn't a warn/crit resets the consecutive counter
            self._offense_count = 0

    def set_sync_status(self, online: bool, last_sync: str = ""):
        """Update bottom status bar and sync label."""
        try:
            self._online_dot.configure(fg_color=GREEN if online else RED)
            txt = (f"Online · synced {last_sync}" if online
                   else f"Offline · {last_sync}")
            self.status_label.configure(text=txt)
            self.sync_label.configure(
                text=f"Synced {last_sync}" if online else "Offline")
        except Exception:
            pass

    def set_risk_score(self, score: float):
        """Update risk score meter."""
        try:
            score = max(0.0, min(float(score), 100.0))
            self._current_risk_score = score
            self.risk_val.configure(text=f"{int(score)} / 100")
            self.risk_bar.set(score / 100)
            if score < 30:
                c = GREEN
            elif score < 60:
                c = AMBER
            else:
                c = RED
            self.risk_bar.configure(progress_color=c)
            self.risk_val.configure(text_color=c)
        except Exception:
            pass

    def show_session_summary(self, summary: dict):
        """Show end-of-session summary dialog."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Session complete")
        dlg.geometry("480x390")
        dlg.resizable(False, False)
        dlg.configure(fg_color=BG1)
        dlg.transient(self)
        dlg.grab_set()
        ico = _asset("sentinel.ico")
        if ico.exists():
            try:
                dlg.iconbitmap(str(ico))
            except Exception:
                pass
        dlg.update_idletasks()
        dlg.geometry(
            f"480x390"
            f"+{(dlg.winfo_screenwidth()-480)//2}"
            f"+{(dlg.winfo_screenheight()-390)//2}")

        ctk.CTkLabel(dlg, text="Session complete",
                     font=("Arial", 20, "bold"), text_color=GREEN
                     ).pack(pady=(28, 18))

        sc = ctk.CTkFrame(dlg, fg_color=BG2, corner_radius=12)
        sc.pack(fill="x", padx=28, pady=(0, 14))

        work_min  = summary.get("work_minutes", 0)
        break_min = summary.get("break_minutes", 0)
        sess_sec  = summary.get("session_seconds", 0)
        progress  = summary.get("progress", 0.0)
        completed = summary.get("completed", False)

        rows = [
            ("Work time",      f"{work_min} min",       GREEN),
            ("Break time",     f"{break_min} min",      AMBER),
            ("Session length", f"{sess_sec//60} min",   BLUE),
            ("Daily progress", f"{int(progress*100)}%", GREEN),
        ]
        for i, (k, v, c) in enumerate(rows):
            r = ctk.CTkFrame(sc, fg_color="transparent")
            r.pack(fill="x", padx=18,
                   pady=(14 if i == 0 else 6,
                         14 if i == len(rows) - 1 else 0))
            ctk.CTkLabel(r, text=k, font=("Arial", 12),
                         text_color=T2).pack(side="left")
            ctk.CTkLabel(r, text=v, font=("Arial", 14, "bold"),
                         text_color=c).pack(side="right")

        msg = ("Daily target reached!" if completed
               else f"Target {int(progress*100)}% complete")
        ctk.CTkLabel(dlg, text=msg, font=("Arial", 13, "bold"),
                     text_color=GREEN if completed else AMBER
                     ).pack(pady=(0, 16))

        ctk.CTkButton(dlg, text="Close", command=dlg.destroy,
                      height=44, corner_radius=10,
                      fg_color="#1E3A6E", hover_color="#16305A",
                      font=("Arial", 13, "bold"), text_color=BLUE
                      ).pack(fill="x", padx=28, pady=(0, 28))

    # ─────────────────────────────────────────────────────────
    # TICK — called every second
    # ─────────────────────────────────────────────────────────
    def _tick(self):
        if self.time_engine:
            try:
                state  = self.time_engine.update()
                cur    = self.time_engine.state
                tokens = state.get("break_tokens", 0)
                self._refresh_timers(state)

                # Only call update_state_ui when something actually changed
                if cur != self._prev_state or tokens != self._prev_tokens:
                    self.update_state_ui(cur, state)
                    self._prev_state  = cur
                    self._prev_tokens = tokens
            except Exception as e:
                print(f"Tick error: {e}")

        self.after(1000, self._tick)

    def _refresh_timers(self, s: dict):
        """Refresh just the timer numbers — called every second."""
        try:
            ws = s.get("work_seconds", 0)
            self.work_timer.configure(
                text=f"{ws//3600:02d}:{(ws%3600)//60:02d}:{ws%60:02d}")

            wm = s.get("work_minutes", 0)
            tgt = s.get("target_minutes", 400)
            prog = s.get("progress", 0.0)
            self.prog_left.configure(text=f"{wm} / {tgt} min")
            self.prog_pct.configure(text=f"{int(prog*100)}%")
            self.progress_bar.set(min(prog, 1.0))

            self._stat_labels["work"].configure(text=f"{wm}m")
            self._stat_labels["break"].configure(
                text=f"{s.get('break_minutes', 0)}m")

            # Break countdown
            if (self.time_engine and
                    self.time_engine.state in (SessionState.ON_BREAK,
                                               SessionState.ON_LUNCH)):
                rem   = s.get("current_break_remaining", 0)
                total = (600 if self.time_engine.state == SessionState.ON_BREAK
                         else 1800)
                self.break_countdown.configure(
                    text=f"{rem//60:02d}:{rem%60:02d}")
                filled = max(0.0, 1.0 - (rem / total)) if total > 0 else 0.0
                self.break_prog.set(filled)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────

    def _set_badge(self, text: str, fg: str, bg: str, border: str):
        """Update both the topbar badge and the timer card badge."""
        try:
            self.state_badge.configure(
                text=f"● {text}", text_color=fg, fg_color=bg,
                border_color=border)
        except Exception:
            pass
        try:
            self.session_badge.configure(
                text=f"● {text}", text_color=fg, fg_color=bg)
        except Exception:
            pass

    def _update_token_dots(self, n: int):
        for i, d in enumerate(self._token_dots):
            try:
                d.configure(fg_color=AMBER if i < n else BG3)
            except Exception:
                pass

    def _update_alert_badge(self):
        n = len(self._feed_items)
        try:
            self.alert_badge.configure(
                text=f"{n} events" if n else "No alerts",
                text_color=AMBER if n else T3,
                fg_color=A_BG if n else BG3)
        except Exception:
            pass

    def _safe_grid_remove(self, widget):
        try:
            if widget.winfo_exists() and widget.grid_info():
                widget.grid_remove()
        except Exception:
            pass

    def _set_work_buttons(self):
        """Show break + lunch buttons, hide resume buttons."""
        if self._btn_mode == "work":
            return
        self._btn_mode = "work"
        self._safe_grid_remove(self.end_break_btn)
        self._safe_grid_remove(self.end_lunch_btn)
        try:
            self.break_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            self.lunch_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        except Exception:
            pass

    def _set_resume_button(self, btn):
        """Show only the resume button (spans both columns)."""
        mode = "break" if btn is self.end_break_btn else "lunch"
        if self._btn_mode == mode:
            return
        self._btn_mode = mode
        self._safe_grid_remove(self.break_btn)
        self._safe_grid_remove(self.lunch_btn)
        self._safe_grid_remove(self.end_break_btn)
        self._safe_grid_remove(self.end_lunch_btn)
        try:
            btn.grid(row=0, column=0, columnspan=2, sticky="ew")
        except Exception:
            pass

    def _show_break_card(self, colour: str, bg: str, border: str):
        """Show break countdown card."""
        try:
            self._break_card.configure(fg_color=bg, border_color=border)
            self.break_countdown.configure(text_color=colour)
            self.break_prog.configure(progress_color=colour)
            if not self._break_visible:
                self._break_card.grid(row=3, column=0, sticky="ew",
                                      in_=self._left_frame, pady=(0, 12))
                self._break_visible = True
        except Exception:
            pass

    def _hide_break_card(self):
        """Hide break countdown card."""
        if not self._break_visible:
            return
        self._safe_grid_remove(self._break_card)
        self._break_visible = False

    # ─────────────────────────────────────────────────────────
    # BUTTON HANDLERS
    # ─────────────────────────────────────────────────────────

    def _toggle_session(self):
        if not self.time_engine:
            return
        if self.time_engine.state == SessionState.IDLE:
            if self.on_start_session:
                self.on_start_session()
        elif self.time_engine.state not in (SessionState.ENDED,):
            if self.on_end_session:
                self.on_end_session()

    def _take_break(self):
        if self.on_take_break:
            self.on_take_break()

    def _end_break(self):
        if self.on_end_break:
            self.on_end_break()

    def _take_lunch(self):
        if self.on_take_lunch:
            self.on_take_lunch()

    def _end_lunch(self):
        if self.on_end_lunch:
            self.on_end_lunch()

    def _logout(self):
        if (self.time_engine and
                self.time_engine.state not in (SessionState.IDLE,
                                               SessionState.ENDED)):
            dlg = ctk.CTkToplevel(self)
            dlg.title("Active session")
            dlg.geometry("360x180")
            dlg.resizable(False, False)
            dlg.configure(fg_color=BG1)
            dlg.transient(self)
            dlg.grab_set()
            dlg.update_idletasks()
            dlg.geometry(
                f"360x180"
                f"+{(dlg.winfo_screenwidth()-360)//2}"
                f"+{(dlg.winfo_screenheight()-180)//2}")
            ico = _asset("sentinel.ico")
            if ico.exists():
                try:
                    dlg.iconbitmap(str(ico))
                except Exception:
                    pass
            ctk.CTkLabel(dlg, text="Active session running",
                         font=("Arial", 15, "bold"), text_color=AMBER
                         ).pack(pady=(24, 8))
            ctk.CTkLabel(dlg, text="End your session before logging out.",
                         font=("Arial", 11), text_color=T2).pack(pady=(0, 18))
            ctk.CTkButton(dlg, text="OK", command=dlg.destroy,
                          height=40, corner_radius=8,
                          fg_color="#1E3A6E", hover_color="#16305A",
                          text_color=BLUE
                          ).pack(fill="x", padx=28, pady=(0, 24))
        else:
            if self.on_logout:
                self.on_logout()
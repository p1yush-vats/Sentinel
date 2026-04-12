"""
Main Window — SENTINEL Desktop App
Redesigned CustomTkinter UI

Layout:
  Left sidebar  : nav links + user card + logout
  Top bar       : session/alert badges + sync label
  Centre-left   : timer hero, progress, stat cards, token dots, action buttons
  Centre-right  : scrollable detection feed + risk score meter + status bar
"""

import customtkinter as ctk
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.time_engine import SessionState


def _asset(filename: str) -> Path:
    return Path(__file__).parent.parent.parent / "assets" / "iso" / filename


def _load_ctk_image(filename: str, size: tuple) -> Optional[ctk.CTkImage]:
    path = _asset(filename)
    if not path.exists():
        return None
    pil = Image.open(path).convert("RGBA")
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)


BG0   = "#0B1120";  BG1 = "#0D1526";  BG2 = "#111C2E"
BG3   = "#1A2640";  BORD = "#1E2D45"; BORD2 = "#243450"
GREEN = "#10B981";  AMBER = "#F59E0B"; RED = "#EF4444"
BLUE  = "#60A5FA";  PURP = "#8B5CF6"
T1 = "#E2E8F0";     T2 = "#94A3B8";   T3 = "#475569";  T4 = "#2D3F55"
G_BG="#0B1F14"; G_BD="#0D3320"
A_BG="#1A1400"; A_BD="#3B2C00"
R_BG="#1A0D0D"; R_BD="#3B1010"
P_BG="#150D2E"; P_BD="#2D1A5E"


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

        ico_f = ctk.CTkFrame(self, width=28, height=28,
                              fg_color=c["ibg"], corner_radius=6)
        ico_f.grid(row=0, column=0, rowspan=2, padx=(8, 6), pady=8, sticky="n")
        ico_f.grid_propagate(False)
        ctk.CTkLabel(ico_f, text=self._ICO.get(kind, "i"),
                     font=("Arial", 11, "bold"), text_color=c["ifg"]
                     ).place(relx=.5, rely=.5, anchor="center")

        tr = ctk.CTkFrame(self, fg_color="transparent")
        tr.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(8, 0))
        tr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tr, text=title, font=("Arial", 11, "bold"),
                     text_color=T1, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(tr, text=badge, font=("Arial", 9),
                     text_color=c["bfg"], fg_color=c["bbg"],
                     corner_radius=8, padx=6, pady=1
                     ).grid(row=0, column=1, padx=(6, 0))

        ctk.CTkLabel(self, text=meta, font=("Arial", 10),
                     text_color=T3, anchor="w"
                     ).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(0, 8))


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


class MainWindow(ctk.CTk):
    MAX_FEED = 60

    def __init__(self, user: dict, access_token: str, time_engine=None):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.user = user
        self.access_token = access_token
        self.time_engine  = time_engine

        self.on_start_session: Optional[Callable] = None
        self.on_end_session:   Optional[Callable] = None
        self.on_take_break:    Optional[Callable] = None
        self.on_end_break:     Optional[Callable] = None
        self.on_take_lunch:    Optional[Callable] = None
        self.on_end_lunch:     Optional[Callable] = None
        self.on_logout:        Optional[Callable] = None

        self._prev_state  = SessionState.IDLE
        self._prev_tokens = 0
        self._feed_items: List[FeedItem] = []
        self._logo_img: Optional[ctk.CTkImage] = None

        self.title(f"SENTINEL — {user['full_name']}")
        self.geometry("1120x700")
        self.minsize(920, 620)
        self.configure(fg_color=BG0)

        ico = _asset("sentinel.ico")
        if ico.exists():
            self.iconbitmap(str(ico))

        self.update_idletasks()
        w, h = 1120, 700
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

        self._build()
        self._tick()

    # ─────────────────────────────────────────────────────────
    def _build(self):
        self._logo_img = _load_ctk_image("sentinel_shield.png", (22, 22))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._sidebar()
        self._mainarea()

    # ── SIDEBAR ──────────────────────────────────────────────
    def _sidebar(self):
        sb = ctk.CTkFrame(self, width=216, fg_color=BG1, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(1, weight=1)

        brand = ctk.CTkFrame(sb, height=64, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew")
        brand.grid_propagate(False)
        inner = ctk.CTkFrame(brand, fg_color="transparent")
        inner.place(x=18, rely=.5, anchor="w")
        sh = ctk.CTkFrame(inner, width=32, height=32,
                           fg_color="#1E3A6E", corner_radius=8)
        sh.pack(side="left", padx=(0, 10))
        sh.pack_propagate(False)
        if self._logo_img:
            ctk.CTkLabel(sh, image=self._logo_img, text=""
                         ).place(relx=.5, rely=.5, anchor="center")
        else:
            ctk.CTkLabel(sh, text="S", font=("Arial", 14, "bold"),
                         text_color=BLUE).place(relx=.5, rely=.5, anchor="center")
        ctk.CTkLabel(inner, text="SENTINEL",
                     font=("Arial", 15, "bold"), text_color=T1).pack(side="left")

        ctk.CTkFrame(sb, height=1, fg_color=BORD).grid(
            row=0, column=0, sticky="ew", pady=(63, 0))

        nav = ctk.CTkFrame(sb, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="nsew", padx=10, pady=12)
        NavButton(nav, "Dashboard",       "⊞", active=True).pack(fill="x", pady=2)
        NavButton(nav, "Session history", "○").pack(fill="x", pady=2)
        NavButton(nav, "Analytics",       "↗").pack(fill="x", pady=2)
        NavButton(nav, "Profile",         "◎").pack(fill="x", pady=2)

        ctk.CTkFrame(sb, height=1, fg_color=BORD).grid(row=2, column=0, sticky="ew")

        uf = ctk.CTkFrame(sb, height=62, fg_color="transparent")
        uf.grid(row=3, column=0, sticky="ew", padx=14, pady=(10, 0))
        uf.grid_propagate(False)
        initials = "".join(p[0].upper() for p in
                           self.user.get("full_name", "?").split()[:2])
        av = ctk.CTkFrame(uf, width=34, height=34,
                           fg_color="#1E3A6E", corner_radius=17)
        av.place(x=0, rely=.5, anchor="w")
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=initials, font=("Arial", 11, "bold"),
                     text_color=BLUE).place(relx=.5, rely=.5, anchor="center")
        inf = ctk.CTkFrame(uf, fg_color="transparent")
        inf.place(x=44, rely=.5, anchor="w")
        ctk.CTkLabel(inf, text=self.user.get("full_name", "User"),
                     font=("Arial", 12, "bold"), text_color=T1).pack(anchor="w")
        ctk.CTkLabel(inf, text=self.user.get("role", "").replace("_", " ").title(),
                     font=("Arial", 10), text_color=T3).pack(anchor="w")

        ctk.CTkButton(sb, text="Logout", command=self._logout,
                      height=32, fg_color="transparent", hover_color=BG3,
                      border_color=BORD, border_width=1,
                      text_color=T3, font=("Arial", 11), corner_radius=8
                      ).grid(row=4, column=0, sticky="ew", padx=14, pady=10)

    # ── MAIN AREA ─────────────────────────────────────────────
    def _mainarea(self):
        main = ctk.CTkFrame(self, fg_color=BG0, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)
        self._topbar(main)
        self._content(main)

    def _topbar(self, parent):
        tb = ctk.CTkFrame(parent, height=48, fg_color=BG1, corner_radius=0)
        tb.grid(row=0, column=0, sticky="ew")
        tb.grid_propagate(False)
        tb.grid_columnconfigure(5, weight=1)

        self.session_badge = ctk.CTkLabel(
            tb, text="● Not started", font=("Arial", 11, "bold"),
            text_color=T3, fg_color=BG3, corner_radius=12, padx=12, pady=4)
        self.session_badge.grid(row=0, column=0, padx=(16, 8), pady=10)

        self.alert_badge = ctk.CTkLabel(
            tb, text="No alerts", font=("Arial", 11),
            text_color=T3, fg_color=BG3, corner_radius=12, padx=12, pady=4)
        self.alert_badge.grid(row=0, column=1, padx=(0, 8), pady=10)

        ctk.CTkFrame(tb, fg_color="transparent").grid(row=0, column=5, sticky="ew")

        self.sync_label = ctk.CTkLabel(
            tb, text="Idle", font=("Arial", 10), text_color=T3)
        self.sync_label.grid(row=0, column=6, padx=(0, 16))

    def _content(self, parent):
        c = ctk.CTkFrame(parent, fg_color=BG0, corner_radius=0)
        c.grid(row=1, column=0, sticky="nsew")
        c.grid_rowconfigure(0, weight=1)
        c.grid_columnconfigure(0, weight=1)
        c.grid_columnconfigure(1, minsize=330)
        self._left(c)
        self._right(c)

    # ── LEFT PANEL ───────────────────────────────────────────
    def _left(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color=BG0, corner_radius=0,
                                       scrollbar_button_color=BG3)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_columnconfigure(0, weight=1)

        # TIMER CARD
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

        self.session_btn = ctk.CTkButton(
            tc, text="Start session", command=self._toggle_session,
            height=48, corner_radius=10,
            fg_color=GREEN, hover_color="#059669",
            text_color="white", font=("Arial", 14, "bold"))
        self.session_btn.grid(row=5, column=0, sticky="ew",
                              padx=28, pady=(12, 24))

        # STAT CARDS
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

        # BREAK TOKENS
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

        # BREAK COUNTDOWN (hidden)
        self._break_card = ctk.CTkFrame(left, fg_color=A_BG, corner_radius=10,
                                         border_color=A_BD, border_width=1)
        self._break_card_row = 3
        self._break_visible  = False
        ctk.CTkLabel(self._break_card, text="BREAK TIME REMAINING",
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

        # ACTION BUTTONS
        self._btn_f = ctk.CTkFrame(left, fg_color="transparent")
        self._btn_f.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        self._btn_f.grid_columnconfigure((0, 1), weight=1)

        self.break_btn = ctk.CTkButton(
            self._btn_f, text="Take break (10 min)",
            command=self._take_break, height=44,
            font=("Arial", 12, "bold"), corner_radius=10,
            fg_color=A_BG, hover_color="#2A1F00",
            text_color=AMBER, border_color=A_BD, border_width=1,
            state="disabled")
        self.break_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.lunch_btn = ctk.CTkButton(
            self._btn_f, text="Lunch (30 min)",
            command=self._take_lunch, height=44,
            font=("Arial", 12, "bold"), corner_radius=10,
            fg_color=P_BG, hover_color="#1D1040",
            text_color=PURP, border_color=P_BD, border_width=1,
            state="disabled")
        self.lunch_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

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

    # ── RIGHT PANEL ──────────────────────────────────────────
    def _right(self, parent):
        right = ctk.CTkFrame(parent, fg_color=BG1, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(right, width=1, fg_color=BORD).grid(
            row=0, column=0, rowspan=10, sticky="ns")

        hdr = ctk.CTkFrame(right, height=44, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=(1, 0))
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="DETECTION FEED",
                     font=("Arial", 10, "bold"), text_color=T3
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=12)
        self._feed_count_lbl = ctk.CTkLabel(
            hdr, text="", font=("Arial", 10), text_color=T3)
        self._feed_count_lbl.grid(row=0, column=1, padx=(0, 12))

        ctk.CTkFrame(right, height=1, fg_color=BORD).grid(
            row=1, column=0, sticky="ew", padx=(1, 0))

        self.feed_frame = ctk.CTkScrollableFrame(
            right, fg_color="transparent",
            scrollbar_button_color=BG3, corner_radius=0)
        self.feed_frame.grid(row=2, column=0, sticky="nsew", padx=(1, 0))
        self.feed_frame.grid_columnconfigure(0, weight=1)

        self._feed_ph = ctk.CTkLabel(
            self.feed_frame,
            text="Detection events will appear\nhere once a session is active.",
            font=("Arial", 11), text_color=T3, justify="center")
        self._feed_ph.grid(row=0, column=0, pady=40)

        ctk.CTkFrame(right, height=1, fg_color=BORD).grid(
            row=3, column=0, sticky="ew", padx=(1, 0))

        # risk score
        rf = ctk.CTkFrame(right, fg_color="transparent")
        rf.grid(row=4, column=0, sticky="ew", padx=(1, 0))
        rf.grid_columnconfigure(0, weight=1)
        rh = ctk.CTkFrame(rf, fg_color="transparent")
        rh.pack(fill="x", padx=16, pady=(12, 8))
        ctk.CTkLabel(rh, text="RISK SCORE",
                     font=("Arial", 10, "bold"), text_color=T3).pack(side="left")
        self.risk_val = ctk.CTkLabel(
            rh, text="0 / 100", font=("Arial", 18, "bold"), text_color=AMBER)
        self.risk_val.pack(side="right")
        self.risk_bar = ctk.CTkProgressBar(
            rf, height=8, corner_radius=4,
            progress_color=AMBER, fg_color=BG3)
        self.risk_bar.set(0)
        self.risk_bar.pack(fill="x", padx=16, pady=(0, 6))
        rl = ctk.CTkFrame(rf, fg_color="transparent")
        rl.pack(fill="x", padx=16, pady=(0, 12))
        for lbl in ["Low", "Medium", "High", "Critical"]:
            ctk.CTkLabel(rl, text=lbl, font=("Arial", 9),
                         text_color=T3).pack(side="left", expand=True)

        ctk.CTkFrame(right, height=1, fg_color=BORD).grid(
            row=5, column=0, sticky="ew", padx=(1, 0))

        bot = ctk.CTkFrame(right, height=30, fg_color="#080F1D", corner_radius=0)
        bot.grid(row=6, column=0, sticky="ew", padx=(1, 0))
        bot.grid_propagate(False)
        bot.grid_columnconfigure(1, weight=1)
        self._online_dot = ctk.CTkFrame(bot, width=8, height=8,
                                         fg_color=GREEN, corner_radius=4)
        self._online_dot.grid(row=0, column=0, padx=(12, 6), pady=10)
        self._online_dot.grid_propagate(False)
        self.status_label = ctk.CTkLabel(
            bot, text="Ready", font=("Arial", 10), text_color=T3, anchor="w")
        self.status_label.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(bot, text="v1.0.0",
                     font=("Arial", 10), text_color=T3
                     ).grid(row=0, column=2, padx=(0, 12))

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────
    def update_state_ui(self, state: SessionState, data: dict):
        tokens = data.get("break_tokens", 0)
        lunch  = data.get("lunch_taken",  False)

        if state == SessionState.WORKING:
            self._badge("Working", GREEN, G_BG, G_BD)
            self.session_btn.configure(
                text="End session", fg_color=R_BG, hover_color="#2A0D0D",
                text_color=RED, border_color=R_BD, border_width=1)
            self.break_btn.configure(state="normal" if tokens > 0 else "disabled")
            self.lunch_btn.configure(state="disabled" if lunch else "normal")
            self._work_btns()
            self._hide_bc()

        elif state == SessionState.ON_BREAK:
            self._badge("On break", AMBER, A_BG, A_BD)
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self._resume_btn(self.end_break_btn)
            self._show_bc(AMBER, A_BG, A_BD)

        elif state == SessionState.ON_LUNCH:
            self._badge("Lunch break", PURP, P_BG, P_BD)
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self._resume_btn(self.end_lunch_btn)
            self._show_bc(PURP, P_BG, P_BD)

        elif state == SessionState.IDLE:
            self._badge("Not started", T3, BG3, BORD)
            self.session_btn.configure(
                text="Start session", fg_color=GREEN,
                hover_color="#059669", text_color="white", border_width=0)
            self.break_btn.configure(state="disabled")
            self.lunch_btn.configure(state="disabled")
            self._work_btns()
            self._hide_bc()

        self._token_dots_update(tokens)
        self._token_lbl.configure(text=f"{tokens} of 3 available")

    def add_feed_item(self, kind: str, title: str, meta: str, badge: str):
        if self._feed_ph.winfo_exists():
            try:
                self._feed_ph.grid_remove()
            except Exception:
                pass

        for fi in self._feed_items:
            if fi.winfo_exists():
                r = int(fi.grid_info().get("row", 0))
                fi.grid(row=r + 1)

        fi = FeedItem(self.feed_frame, kind=kind, title=title,
                      meta=meta, badge=badge)
        fi.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))
        self._feed_items.insert(0, fi)

        while len(self._feed_items) > self.MAX_FEED:
            old = self._feed_items.pop()
            if old.winfo_exists():
                old.destroy()

        self._feed_count_lbl.configure(text=f"{len(self._feed_items)} events")
        self._alert_badge()

    def set_sync_status(self, online: bool, last_sync: str = ""):
        self._online_dot.configure(fg_color=GREEN if online else RED)
        self.status_label.configure(
            text=f"Online · {last_sync}" if online else f"Offline · {last_sync}")
        self.sync_label.configure(
            text=f"Synced {last_sync}" if online else "Offline")

    def set_risk_score(self, score: float):
        self.risk_val.configure(text=f"{int(score)} / 100")
        self.risk_bar.set(min(score / 100, 1.0))
        c = GREEN if score < 30 else (AMBER if score < 65 else RED)
        self.risk_bar.configure(progress_color=c)
        self.risk_val.configure(text_color=c)

    def show_session_summary(self, summary: dict):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Session complete")
        dlg.geometry("480x370")
        dlg.resizable(False, False)
        dlg.configure(fg_color=BG1)
        dlg.transient(self)
        dlg.grab_set()
        ico = _asset("sentinel.ico")
        if ico.exists():
            dlg.iconbitmap(str(ico))
        dlg.update_idletasks()
        dlg.geometry(
            f"480x370+{(dlg.winfo_screenwidth()-480)//2}"
            f"+{(dlg.winfo_screenheight()-370)//2}")

        ctk.CTkLabel(dlg, text="Session complete",
                     font=("Arial", 20, "bold"), text_color=GREEN
                     ).pack(pady=(28, 18))

        sc = ctk.CTkFrame(dlg, fg_color=BG2, corner_radius=12)
        sc.pack(fill="x", padx=28, pady=(0, 14))
        rows = [
            ("Work time",      f"{summary['work_minutes']} min",          GREEN),
            ("Break time",     f"{summary['break_minutes']} min",         AMBER),
            ("Session length", f"{summary['session_seconds']//60} min",   BLUE),
            ("Daily progress", f"{int(summary['progress']*100)}%",        GREEN),
        ]
        for i, (k, v, c) in enumerate(rows):
            r = ctk.CTkFrame(sc, fg_color="transparent")
            r.pack(fill="x", padx=18,
                   pady=(14 if i == 0 else 6, 14 if i == len(rows)-1 else 0))
            ctk.CTkLabel(r, text=k, font=("Arial", 12),
                         text_color=T2).pack(side="left")
            ctk.CTkLabel(r, text=v, font=("Arial", 14, "bold"),
                         text_color=c).pack(side="right")

        msg = ("Daily target reached!" if summary["completed"]
               else f"Target {int(summary['progress']*100)}% complete")
        ctk.CTkLabel(dlg, text=msg, font=("Arial", 13, "bold"),
                     text_color=GREEN if summary["completed"] else AMBER
                     ).pack(pady=(0, 16))
        ctk.CTkButton(dlg, text="Close", command=dlg.destroy,
                      height=44, corner_radius=10,
                      fg_color="#1E3A6E", hover_color="#16305A",
                      font=("Arial", 13, "bold")
                      ).pack(fill="x", padx=28, pady=(0, 28))

    # ─────────────────────────────────────────────────────────
    # TICK
    # ─────────────────────────────────────────────────────────
    def _tick(self):
        if self.time_engine:
            state  = self.time_engine.update()
            cur    = self.time_engine.state
            tokens = state["break_tokens"]
            self._refresh(state)
            if cur != self._prev_state or tokens != self._prev_tokens:
                self.update_state_ui(cur, state)
                self._prev_state  = cur
                self._prev_tokens = tokens
        self.after(1000, self._tick)

    def _refresh(self, s: dict):
        ws = s["work_seconds"]
        self.work_timer.configure(
            text=f"{ws//3600:02d}:{(ws%3600)//60:02d}:{ws%60:02d}")
        wm = s["work_minutes"]
        self.prog_left.configure(text=f"{wm} / {s['target_minutes']} min")
        self.prog_pct.configure(text=f"{int(s['progress']*100)}%")
        self.progress_bar.set(s["progress"])
        self._stat_labels["work"].configure(text=f"{wm}m")
        self._stat_labels["break"].configure(text=f"{s['break_minutes']}m")

        if self.time_engine and self.time_engine.state in [
                SessionState.ON_BREAK, SessionState.ON_LUNCH]:
            rem   = s["current_break_remaining"]
            total = (600 if self.time_engine.state == SessionState.ON_BREAK
                     else 1800)
            self.break_countdown.configure(
                text=f"{rem//60:02d}:{rem%60:02d}")
            self.break_prog.set(max(0, (total - rem) / total))

    # ─────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────
    def _badge(self, text, fg, bg, border):
        self.state_badge.configure(
            text=f"● {text}", text_color=fg, fg_color=bg, border_color=border)
        self.session_badge.configure(
            text=f"● {text}", text_color=fg, fg_color=bg)

    def _token_dots_update(self, n: int):
        for i, d in enumerate(self._token_dots):
            d.configure(fg_color=AMBER if i < n else BG3)

    def _alert_badge(self):
        n = len(self._feed_items)
        self.alert_badge.configure(
            text=f"{n} events" if n else "No alerts",
            text_color=AMBER if n else T3,
            fg_color=A_BG if n else BG3)

    def _work_btns(self):
        self.end_break_btn.grid_remove()
        self.end_lunch_btn.grid_remove()
        self.break_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.lunch_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _resume_btn(self, btn):
        self.break_btn.grid_remove()
        self.lunch_btn.grid_remove()
        self.end_break_btn.grid_remove()
        self.end_lunch_btn.grid_remove()
        btn.grid(row=0, column=0, columnspan=2, sticky="ew")

    def _show_bc(self, colour, bg, border):
        self._break_card.configure(fg_color=bg, border_color=border)
        self.break_countdown.configure(text_color=colour)
        self.break_prog.configure(progress_color=colour)
        self._break_card.grid(
            row=self._break_card_row, column=0, sticky="ew", pady=(0, 12))
        self._break_visible = True

    def _hide_bc(self):
        self._break_card.grid_remove()
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
        else:
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
        if (self.time_engine
                and self.time_engine.state != SessionState.IDLE):
            dlg = ctk.CTkToplevel(self)
            dlg.title("Active session")
            dlg.geometry("360x170")
            dlg.resizable(False, False)
            dlg.configure(fg_color=BG1)
            dlg.transient(self)
            dlg.grab_set()
            dlg.update_idletasks()
            dlg.geometry(
                f"360x170"
                f"+{(dlg.winfo_screenwidth()-360)//2}"
                f"+{(dlg.winfo_screenheight()-170)//2}")
            ico = _asset("sentinel.ico")
            if ico.exists():
                dlg.iconbitmap(str(ico))
            ctk.CTkLabel(dlg, text="Active session running",
                         font=("Arial", 15, "bold"), text_color=AMBER
                         ).pack(pady=(24, 8))
            ctk.CTkLabel(dlg, text="End your session before logging out.",
                         font=("Arial", 11), text_color=T2).pack(pady=(0, 18))
            ctk.CTkButton(dlg, text="OK", command=dlg.destroy,
                          height=40, corner_radius=8,
                          fg_color="#1E3A6E", hover_color="#16305A"
                          ).pack(fill="x", padx=28, pady=(0, 24))
        else:
            if self.on_logout:
                self.on_logout()
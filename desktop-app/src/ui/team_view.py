import logging
import customtkinter as ctk
import subprocess
import sys
from core.config import Config

logger = logging.getLogger(__name__)

# Palette (matched with main_window.py)
BG0  = "#0B1120"; BG1 = "#0D1526"; BG2 = "#111C2E"
BG3  = "#1A2640"; BORD = "#1E2D45"; BORD2 = "#243450"
GREEN = "#10B981"; AMBER = "#F59E0B"; RED = "#EF4444"
BLUE  = "#60A5FA"; PURP  = "#8B5CF6"
T1 = "#E2E8F0"; T2 = "#94A3B8"; T3 = "#475569"; T4 = "#2D3F55"


class TeamView(ctk.CTkFrame):
    def __init__(self, parent, user: dict, access_token: str, api_base_url: str, session_manager, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.user = user
        self.access_token = access_token
        self.api_base_url = api_base_url
        self.session_manager = session_manager
        
        # Compatibility attribute
        self.active_dm_windows = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Build url with token query parameter for automatic login
        base_url = Config.PORTAL_URL.rstrip("/")
        self.url = f"{base_url}/my/team"
        if self.access_token:
            self.url = f"{self.url}?token={self.access_token}"

        # Outer container frame
        self.container = ctk.CTkFrame(self, fg_color=BG1, corner_radius=16, border_color=BORD, border_width=1)
        self.container.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self.container.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Content Card
        inner = ctk.CTkFrame(self.container, fg_color="transparent")
        inner.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=40)
        inner.grid_columnconfigure(0, weight=1)

        # Icon / Badge
        icon_lbl = ctk.CTkLabel(inner, text="👥", font=("Arial", 64))
        icon_lbl.grid(row=0, column=0, pady=(0, 16))

        # Title
        title_lbl = ctk.CTkLabel(
            inner, text="SENTINEL TEAM WORKSPACE",
            font=("Arial", 20, "bold"), text_color=BLUE
        )
        title_lbl.grid(row=1, column=0, pady=(0, 8))

        # Subtitle / Description
        desc_text = (
            "The SENTINEL Team Workspace runs inside a dedicated high-performance\n"
            "standalone browser window. It provides real-time group chat, direct messaging,\n"
            "typing indicators, member presence, and pinned notifications."
        )
        desc_lbl = ctk.CTkLabel(
            inner, text=desc_text, font=("Arial", 12), text_color=T2, justify="center"
        )
        desc_lbl.grid(row=2, column=0, pady=(0, 28))

        # Status Badge
        status_f = ctk.CTkFrame(inner, fg_color="#10B981", height=28, corner_radius=14)
        status_f.grid(row=3, column=0, pady=(0, 32))
        status_lbl = ctk.CTkLabel(status_f, text="● Connected & Syncing", font=("Arial", 10, "bold"), text_color="#FFFFFF")
        status_lbl.pack(padx=16, pady=4)

        # Launch Button
        self.launch_btn = ctk.CTkButton(
            inner, text="Launch Team Chat Window",
            width=260, height=48, font=("Arial", 13, "bold"),
            fg_color=BLUE, hover_color="#2563EB", text_color="#FFFFFF",
            corner_radius=10, command=self.launch_chat_window
        )
        self.launch_btn.grid(row=4, column=0)

        # Auto-launch on first show
        self.after(500, self.launch_chat_window)

    def launch_chat_window(self):
        logger.info(f"TeamView: Spawning standalone pywebview window for {self.url}")
        
        # We start a separate background process pointing to pywebview.
        # This completely avoids COM threading conflicts, pythonnet crashes, or UI lockups.
        cmd = [
            sys.executable,
            "-c",
            f"import webview; "
            f"window = webview.create_window('SENTINEL Team Chat', '{self.url}', width=1020, height=720, background_color='#0B1120'); "
            f"webview.start()"
        ]
        try:
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        except Exception as e:
            logger.error(f"Failed to spawn team chat window: {e}")

    def refresh_all(self):
        # Focus/re-launch window
        self.launch_chat_window()

    # WebSocket compatibility stubs
    def handle_ws_team_chat(self, data: dict): pass
    def handle_ws_typing(self, data: dict): pass
    def handle_ws_presence(self, data: dict): pass
    def handle_ws_pin_update(self, data: dict): pass

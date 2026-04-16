"""
Login Window — SENTINEL Desktop App

IMAGE SAFETY NOTE:
  CTkImage wraps a Tkinter PhotoImage which is bound to whichever Tk
  root is active when it is created. We must NOT load the image before
  the window exists, and we must NOT cache it across window lifetimes
  (i.e. login → logout → login again). Each LoginWindow instance loads
  its own fresh image inside _build(), after super().__init__() has
  made this CTk the active root.
"""
import customtkinter as ctk
from PIL import Image
from utils.assets import get_logo_64, set_window_icon


# Palette
BG0  = "#0B1120"; BG1 = "#0D1526"; BG2 = "#111C2E"
BG3  = "#1A2640"; BORD = "#1E2D45"; BORD2 = "#243450"
GREEN = "#10B981"; BLUE = "#60A5FA"; RED = "#EF4444"
T1 = "#E2E8F0"; T2 = "#94A3B8"; T3 = "#475569"; T4 = "#2D3F55"


class LoginWindow(ctk.CTk):

    def __init__(
        self,
        on_login_success: Callable,
        api_base_url: str = "http://127.0.0.1:8000"
    ):
        super().__init__()   # ← this CTk() becomes the active Tk root

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.on_login_success = on_login_success
        self.api_base_url     = api_base_url

        # Image loaded in _build() — AFTER super().__init__() so it is
        # bound to THIS window's Tk instance, not any previous one.
        self._shield_img: Optional[ctk.CTkImage] = None

        self.title("SENTINEL — Login")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(fg_color=BG0)

        set_window_icon(self)

        self._center()
        self._build()   # image loaded here, safely inside active root

    def _center(self):
        self.update_idletasks()
        w, h = 440, 560
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # Load Skull Logo safely
        self._shield_img = get_logo_64()

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=32, pady=32)

        card = ctk.CTkFrame(outer, fg_color=BG1, corner_radius=16,
                            border_color=BORD, border_width=1)
        card.pack(fill="both", expand=True)

        # Logo
        logo_f = ctk.CTkFrame(card, fg_color="transparent")
        logo_f.pack(pady=(32, 16))

        if self._shield_img:
            ctk.CTkLabel(logo_f, image=self._shield_img, text="").pack()
        else:
            sh = ctk.CTkFrame(logo_f, width=64, height=64,
                              fg_color="#1E3A6E", corner_radius=14)
            sh.pack()
            sh.pack_propagate(False)
            ctk.CTkLabel(sh, text="S", font=("Arial", 28, "bold"),
                        text_color=BLUE).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(logo_f, text="SENTINEL",
                    font=("Arial", 26, "bold"), text_color=T1).pack(pady=(10, 2))
        ctk.CTkLabel(logo_f, text="Work integrity system",
                    font=("Arial", 12), text_color=T3).pack()

        # Form
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=32, pady=(8, 0))

        ctk.CTkLabel(form, text="Email", font=("Arial", 12),
                    text_color=T3, anchor="w").pack(fill="x", pady=(0, 5))
        self.email_entry = ctk.CTkEntry(
            form, placeholder_text="you@company.com",
            height=42, corner_radius=8,
            fg_color=BG2, border_color=BORD2, border_width=1,
            text_color=T1, placeholder_text_color=T4, font=("Arial", 13))
        self.email_entry.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Password", font=("Arial", 12),
                    text_color=T3, anchor="w").pack(fill="x", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(
            form, placeholder_text="••••••••", show="●",
            height=42, corner_radius=8,
            fg_color=BG2, border_color=BORD2, border_width=1,
            text_color=T1, placeholder_text_color=T4, font=("Arial", 13))
        self.password_entry.pack(fill="x", pady=(0, 14))

        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="Remember me", variable=self.remember_var,
            font=("Arial", 12), text_color=T3,
            fg_color=BLUE, hover_color="#2563EB",
            checkmark_color="white", corner_radius=4, border_color=BORD2
        ).pack(anchor="w", pady=(0, 20))

        self.login_btn = ctk.CTkButton(
            form, text="Login", command=self._handle_login,
            height=46, corner_radius=10,
            fg_color="#1E3A6E", hover_color="#16305A",
            text_color=BLUE, font=("Arial", 14, "bold"))
        self.login_btn.pack(fill="x", pady=(0, 10))

        self.status_lbl = ctk.CTkLabel(
            form, text="", font=("Arial", 11),
            text_color=RED, wraplength=360)
        self.status_lbl.pack(pady=(0, 4))

        ctk.CTkLabel(card, text=f"API: {self.api_base_url}",
                    font=("Arial", 9), text_color=T4).pack(pady=(4, 4))
        ctk.CTkLabel(card, text="v1.0.0",
                    font=("Arial", 10), text_color=T4).pack(pady=(0, 18))

        self.email_entry.bind("<Return>", lambda _: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda _: self._handle_login())

    def _handle_login(self):
        email    = self.email_entry.get().strip()
        password = self.password_entry.get()
        if not email:
            self._show_error("Please enter your email")
            return
        if not password:
            self._show_error("Please enter your password")
            return
        self.login_btn.configure(state="disabled", text="Logging in…")
        self.status_lbl.configure(text="Authenticating…", text_color=T3)
        threading.Thread(target=self._do_login, args=(email, password), daemon=True).start()

    def _do_login(self, email: str, password: str):
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.api_base_url}/api/v1/auth/login",
                    json={"email": email, "password": password}
                )
            if resp.status_code == 200:
                data = resp.json()
                self.after(0, lambda: self._login_success(data))
            else:
                try:
                    msg = resp.json().get("detail", "Login failed")
                    if isinstance(msg, dict):
                        msg = str(msg)
                except Exception:
                    msg = f"Login failed (HTTP {resp.status_code})"
                self.after(0, lambda m=msg: self._login_failed(m))
        except httpx.ConnectError:
            self.after(0, lambda: self._login_failed(
                f"Cannot connect.\nIs the backend running at {self.api_base_url}?"))
        except httpx.TimeoutException:
            self.after(0, lambda: self._login_failed("Connection timed out."))
        except Exception as e:
            self.after(0, lambda err=str(e): self._login_failed(err))

    def _login_success(self, data: dict):
        name = data.get("user", {}).get("full_name", "User")
        self.status_lbl.configure(text=f"Welcome, {name}!", text_color=GREEN)
        # Give the user 800ms to see the welcome message, then fire callback.
        # main.py will call self.withdraw() before opening MainWindow so
        # the image binding stays safe.
        self.after(800, lambda: self.on_login_success(data["user"], data["access_token"]))

    def _login_failed(self, msg: str):
        self._show_error(msg)
        self.login_btn.configure(state="normal", text="Login")

    def _show_error(self, msg: str):
        self.status_lbl.configure(text=msg, text_color=RED)
        self.after(7000, lambda: self.status_lbl.configure(text=""))
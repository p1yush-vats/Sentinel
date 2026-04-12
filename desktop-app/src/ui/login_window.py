"""
Login Window — SENTINEL Desktop App
Redesigned CustomTkinter UI
"""
import customtkinter as ctk
from PIL import Image
from pathlib import Path
from typing import Optional, Callable
import threading
import httpx


def _asset(filename: str) -> Path:
    return Path(__file__).parent.parent.parent / "assets" / "iso" / filename


def _load_ctk_image(filename: str, size: tuple) -> Optional[ctk.CTkImage]:
    path = _asset(filename)
    if not path.exists():
        return None
    pil = Image.open(path).convert("RGBA")
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)


# ── palette ──────────────────────────────────────────────────
BG0  = "#0B1120"
BG1  = "#0D1526"
BG2  = "#111C2E"
BG3  = "#1A2640"
BORD = "#1E2D45"
BORD2= "#243450"

GREEN = "#10B981"
BLUE  = "#60A5FA"
RED   = "#EF4444"
AMBER = "#F59E0B"

T1 = "#E2E8F0"
T2 = "#94A3B8"
T3 = "#475569"
T4 = "#2D3F55"


class LoginWindow(ctk.CTk):
    """
    Full-screen login window with shield branding.
    Calls on_login_success(user_dict, access_token) on success.
    """

    def __init__(
        self,
        on_login_success: Callable,
        api_base_url: str = "http://127.0.0.1:8000"
    ):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.on_login_success = on_login_success
        self.api_base_url     = api_base_url

        self.title("SENTINEL — Login")
        self.geometry("460x580")
        self.resizable(False, False)
        self.configure(fg_color=BG0)

        ico = _asset("sentinel.ico")
        if ico.exists():
            self.iconbitmap(str(ico))

        self._shield_img: Optional[ctk.CTkImage] = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = 460, 580
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        self._shield_img = _load_ctk_image("sentinel_shield.png", (64, 64))

        # outer card
        card = ctk.CTkFrame(self, fg_color=BG1, corner_radius=16,
                             border_color=BORD, border_width=1)
        card.place(relx=.5, rely=.5, anchor="center", relwidth=.85)

        # ── logo ──
        logo_frame = ctk.CTkFrame(card, fg_color="transparent")
        logo_frame.pack(pady=(36, 20))

        if self._shield_img:
            ctk.CTkLabel(logo_frame, image=self._shield_img, text="").pack()
        else:
            shield_box = ctk.CTkFrame(logo_frame, width=64, height=64,
                                       fg_color="#1E3A6E", corner_radius=14)
            shield_box.pack()
            shield_box.pack_propagate(False)
            ctk.CTkLabel(shield_box, text="S", font=("Arial", 28, "bold"),
                         text_color=BLUE).place(relx=.5, rely=.5, anchor="center")

        ctk.CTkLabel(logo_frame, text="SENTINEL",
                     font=("Arial", 26, "bold"), text_color=T1,
                     ).pack(pady=(10, 2))
        ctk.CTkLabel(logo_frame, text="Work integrity system",
                     font=("Arial", 12), text_color=T3).pack()

        # ── form ──
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=32, pady=(8, 0))

        ctk.CTkLabel(form, text="Email", font=("Arial", 12),
                     text_color=T3, anchor="w").pack(fill="x", pady=(0, 5))
        self.email_entry = ctk.CTkEntry(
            form, placeholder_text="you@company.com",
            height=42, corner_radius=8,
            fg_color=BG2, border_color=BORD2, border_width=1,
            text_color=T1, placeholder_text_color=T4,
            font=("Arial", 13)
        )
        self.email_entry.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Password", font=("Arial", 12),
                     text_color=T3, anchor="w").pack(fill="x", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(
            form, placeholder_text="••••••••",
            show="●", height=42, corner_radius=8,
            fg_color=BG2, border_color=BORD2, border_width=1,
            text_color=T1, placeholder_text_color=T4,
            font=("Arial", 13)
        )
        self.password_entry.pack(fill="x", pady=(0, 14))

        # remember me
        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="Remember me", variable=self.remember_var,
            font=("Arial", 12), text_color=T3,
            fg_color=BLUE, hover_color="#2563EB",
            checkmark_color="white", corner_radius=4,
            border_color=BORD2
        ).pack(anchor="w", pady=(0, 22))

        # login button
        self.login_btn = ctk.CTkButton(
            form, text="Login", command=self._handle_login,
            height=46, corner_radius=10,
            fg_color="#1E3A6E", hover_color="#16305A",
            text_color=BLUE, font=("Arial", 14, "bold")
        )
        self.login_btn.pack(fill="x", pady=(0, 12))

        # status label
        self.status_lbl = ctk.CTkLabel(
            form, text="", font=("Arial", 11),
            text_color=RED, wraplength=340
        )
        self.status_lbl.pack(pady=(0, 4))

        # api hint
        ctk.CTkLabel(card, text=f"API: {self.api_base_url}",
                     font=("Arial", 9), text_color=T4
                     ).pack(pady=(4, 6))

        # version
        ctk.CTkLabel(card, text="v1.0.0",
                     font=("Arial", 10), text_color=T4
                     ).pack(pady=(0, 20))

        # key bindings
        self.email_entry.bind("<Return>",
                               lambda _: self.password_entry.focus())
        self.password_entry.bind("<Return>",
                                  lambda _: self._handle_login())

    # ─────────────────────────────────────────────────────────

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

        threading.Thread(
            target=self._do_login, args=(email, password), daemon=True
        ).start()

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
                except Exception:
                    msg = f"Login failed (HTTP {resp.status_code})"
                self.after(0, lambda: self._login_failed(msg))

        except httpx.ConnectError:
            self.after(0, lambda: self._login_failed(
                f"Cannot connect to backend.\n{self.api_base_url}"
            ))
        except Exception as e:
            self.after(0, lambda: self._login_failed(str(e)))

    def _login_success(self, data: dict):
        self.status_lbl.configure(
            text=f"Welcome, {data['user']['full_name']}!", text_color=GREEN
        )
        self.after(900, lambda: self.on_login_success(
            data["user"], data["access_token"]
        ))
        self.after(1400, self.destroy)

    def _login_failed(self, msg: str):
        self._show_error(msg)
        self.login_btn.configure(state="normal", text="Login")

    def _show_error(self, msg: str):
        self.status_lbl.configure(text=msg, text_color=RED)
        self.after(6000, lambda: self.status_lbl.configure(text=""))


if __name__ == "__main__":
    def _on_success(user, token):
        print(f"Login OK — {user['email']}")

    app = LoginWindow(on_login_success=_on_success)
    app.mainloop()
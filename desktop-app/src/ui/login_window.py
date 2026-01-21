"""
Login Window for SENTINEL Desktop App
"""
import customtkinter as ctk
from typing import Optional, Callable
import threading
import httpx


class LoginWindow(ctk.CTk):
    """Main login window"""
    
    def __init__(self, on_login_success: Callable, api_base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        
        self.on_login_success = on_login_success
        self.api_base_url = api_base_url
        
        # Configure window
        self.title("SENTINEL - Login")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Center window on screen
        self.center_window()
        
        # Create UI
        self.create_widgets()
        
    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create and layout all widgets"""
        
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Logo/Title
        title = ctk.CTkLabel(
            container,
            text="🛡️ SENTINEL",
            font=("Arial", 32, "bold"),
            text_color="#3B82F6"
        )
        title.pack(pady=(0, 10))
        
        subtitle = ctk.CTkLabel(
            container,
            text="Work Integrity System",
            font=("Arial", 14),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 40))
        
        # Email input
        self.email_label = ctk.CTkLabel(
            container,
            text="Email",
            font=("Arial", 12)
        )
        self.email_label.pack(anchor="w", pady=(0, 5))
        
        self.email_entry = ctk.CTkEntry(
            container,
            placeholder_text="Enter your email",
            height=45,
            font=("Arial", 12)
        )
        self.email_entry.pack(fill="x", pady=(0, 20))
        
        # Password input
        self.password_label = ctk.CTkLabel(
            container,
            text="Password",
            font=("Arial", 12)
        )
        self.password_label.pack(anchor="w", pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            container,
            placeholder_text="Enter your password",
            show="●",
            height=45,
            font=("Arial", 12)
        )
        self.password_entry.pack(fill="x", pady=(0, 10))
        
        # Remember me checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_check = ctk.CTkCheckBox(
            container,
            text="Remember me",
            variable=self.remember_var,
            font=("Arial", 11)
        )
        self.remember_check.pack(anchor="w", pady=(0, 30))
        
        # Login button
        self.login_button = ctk.CTkButton(
            container,
            text="Login",
            command=self.handle_login,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.login_button.pack(fill="x", pady=(0, 15))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            container,
            text="",
            font=("Arial", 11),
            text_color="red"
        )
        self.status_label.pack(pady=(0, 10))
        
        # API URL info
        api_info = ctk.CTkLabel(
            container,
            text=f"API: {self.api_base_url}",
            font=("Arial", 9),
            text_color="gray"
        )
        api_info.pack(pady=(5, 0))
        
        # Version info
        version_label = ctk.CTkLabel(
            container,
            text="Version 1.0.0",
            font=("Arial", 10),
            text_color="gray"
        )
        version_label.pack(side="bottom", pady=(20, 0))
        
        # Bind Enter key to login
        self.password_entry.bind("<Return>", lambda e: self.handle_login())
        self.email_entry.bind("<Return>", lambda e: self.password_entry.focus())
    
    def handle_login(self):
        """Handle login button click"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not email:
            self.show_error("Please enter your email")
            return
        
        if not password:
            self.show_error("Please enter your password")
            return
        
        # Disable button during login
        self.login_button.configure(state="disabled", text="Logging in...")
        self.status_label.configure(text="Authenticating...", text_color="gray")
        
        # Start login in background thread
        thread = threading.Thread(
            target=self.do_login,
            args=(email, password),
            daemon=True
        )
        thread.start()
    
    def do_login(self, email: str, password: str):
        """Perform login in background thread"""
        try:
            # Make HTTP request to backend
            url = f"{self.api_base_url}/api/v1/auth/login"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    json={"email": email, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Schedule success callback on main thread
                    self.after(0, lambda: self.login_success(data))
                else:
                    error_msg = "Login failed"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", error_msg)
                    except:
                        pass
                    
                    # Schedule error display on main thread
                    self.after(0, lambda: self.login_failed(error_msg))
                    
        except httpx.ConnectError:
            self.after(0, lambda: self.login_failed(
                f"Cannot connect to backend at {self.api_base_url}\n"
                "Make sure the backend server is running!"
            ))
        except Exception as e:
            self.after(0, lambda: self.login_failed(f"Error: {str(e)}"))
    
    def login_success(self, data: dict):
        """Handle successful login (runs on main thread)"""
        # Save token if remember me is checked
        if self.remember_var.get():
            self.save_credentials(data["user"]["email"], data["access_token"])
        
        # Show success message briefly
        self.status_label.configure(
            text=f"Welcome, {data['user']['full_name']}!",
            text_color="green"
        )
        
        # Call success callback after a short delay
        self.after(1000, lambda: self.on_login_success(data["user"], data["access_token"]))
        
        # Close login window
        self.after(1500, self.destroy)
    
    def login_failed(self, error_msg: str):
        """Handle failed login (runs on main thread)"""
        self.show_error(error_msg)
        self.login_button.configure(state="normal", text="Login")
    
    def show_error(self, message: str):
        """Display error message"""
        self.status_label.configure(text=message, text_color="red")
        
        # Clear after 5 seconds
        self.after(5000, lambda: self.status_label.configure(text=""))
    
    def save_credentials(self, email: str, token: str):
        """Save credentials securely"""
        # TODO: Implement secure credential storage
        print(f"Saving credentials for: {email}")
    
    def load_saved_credentials(self):
        """Load saved credentials if any"""
        # TODO: Implement credential loading
        pass


def main():
    """Test the login window"""
    def on_success(user, token):
        print(f"\n✅ Login successful!")
        print(f"User: {user['email']}")
        print(f"Name: {user['full_name']}")
        print(f"Role: {user['role']}")
        print(f"Token: {token[:50]}...")
    
    app = LoginWindow(on_login_success=on_success)
    app.mainloop()


if __name__ == "__main__":
    main()
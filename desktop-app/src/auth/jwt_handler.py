"""
JWT Token Handler

Manages JWT tokens with secure storage and auto-refresh.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
from cryptography.fernet import Fernet
import base64
import hashlib


class JWTHandler:
    """
    Secure JWT token manager
    
    Features:
    - Encrypted token storage
    - Auto-refresh before expiry
    - Token validation
    """
    
    def __init__(self, storage_dir: Path):
        """
        Initialize JWT handler
        
        Args:
            storage_dir: Directory to store encrypted tokens
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.storage_dir / "tokens.enc"
        
        # Generate encryption key from machine-specific data
        self.cipher = self._get_cipher()
        
        # Cached tokens
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._user_data: Optional[Dict] = None
        
        # Load saved tokens
        self._load_tokens()
    
    def _get_cipher(self) -> Fernet:
        """Generate encryption cipher from machine ID"""
        # Create a machine-specific key (in production, use better method)
        machine_id = os.getenv("COMPUTERNAME", "default-machine")
        key_material = f"sentinel-{machine_id}".encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
        return Fernet(key)
    
    def save_tokens(
        self,
        access_token: str,
        refresh_token: str,
        user_data: Dict,
        expires_in_minutes: int = 1440  # 24 hours default
    ):
        """
        Save tokens securely
        
        Args:
            access_token: JWT access token
            refresh_token: JWT refresh token
            user_data: User information
            expires_in_minutes: Token validity in minutes
        """
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._user_data = user_data
        self._token_expiry = datetime.now() + timedelta(minutes=expires_in_minutes)
        
        # Prepare data
        data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data,
            "expiry": self._token_expiry.isoformat()
        }
        
        # Encrypt and save
        try:
            encrypted = self.cipher.encrypt(json.dumps(data).encode())
            self.token_file.write_bytes(encrypted)
        except Exception as e:
            print(f"Error saving tokens: {e}")
    
    def _load_tokens(self):
        """Load saved tokens from disk"""
        if not self.token_file.exists():
            return
        
        try:
            encrypted = self.token_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted)
            
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            self._user_data = data.get("user")
            
            expiry_str = data.get("expiry")
            if expiry_str:
                self._token_expiry = datetime.fromisoformat(expiry_str)
            
        except Exception as e:
            print(f"Error loading tokens: {e}")
            self.clear_tokens()
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token"""
        return self._access_token
    
    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token"""
        return self._refresh_token
    
    def get_user_data(self) -> Optional[Dict]:
        """Get stored user data"""
        return self._user_data
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid"""
        if not self._access_token or not self._token_expiry:
            return False
        
        # Consider expired if less than 5 minutes remaining
        return datetime.now() < (self._token_expiry - timedelta(minutes=5))
    
    def needs_refresh(self) -> bool:
        """Check if token needs refresh"""
        if not self._access_token or not self._token_expiry:
            return False
        
        # Refresh if less than 30 minutes remaining
        time_remaining = self._token_expiry - datetime.now()
        return time_remaining < timedelta(minutes=30)
    
    def clear_tokens(self):
        """Clear all stored tokens"""
        self._access_token = None
        self._refresh_token = None
        self._user_data = None
        self._token_expiry = None
        
        if self.token_file.exists():
            self.token_file.unlink()
    
    def has_saved_tokens(self) -> bool:
        """Check if there are saved tokens"""
        return self._access_token is not None


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    
    handler = JWTHandler(Path.home() / ".sentinel")
    
    # Save tokens
    handler.save_tokens(
        access_token="eyJhbGc...",
        refresh_token="eyJhbGc...",
        user_data={
            "id": "123",
            "email": "test@example.com",
            "full_name": "John Doe"
        }
    )
    
    print(f"Valid: {handler.is_token_valid()}")
    print(f"Needs refresh: {handler.needs_refresh()}")
    print(f"User: {handler.get_user_data()}")
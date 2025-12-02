"""
Authentication module for MarketResearcher web interface.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path

from passlib.context import CryptContext
from jose import JWTError, jwt

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

class UserManager:
    """Simple user management system."""
    
    def __init__(self, users_file: str = "web/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(exist_ok=True)
        self._load_users()
    
    def _load_users(self):
        """Load users from JSON file."""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            # Create default admin user
            self.users = {
                "admin": {
                    "username": "admin",
                    "hashed_password": self.get_password_hash("admin123"),
                    "email": "admin@localhost",
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
            }
            self._save_users()
    
    def _save_users(self):
        """Save users to JSON file."""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user."""
        user = self.users.get(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        if not user.get("is_active", True):
            return None
        return user
    
    def create_user(self, username: str, password: str, email: str = "") -> bool:
        """Create a new user."""
        if username in self.users:
            return False
        
        self.users[username] = {
            "username": username,
            "hashed_password": self.get_password_hash(password),
            "email": email,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        self._save_users()
        return True
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self.users.get(username)
    
    def change_password(self, username: str, new_password: str) -> bool:
        """Change user password."""
        if username not in self.users:
            return False
        
        self.users[username]["hashed_password"] = self.get_password_hash(new_password)
        self._save_users()
        return True

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return username."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

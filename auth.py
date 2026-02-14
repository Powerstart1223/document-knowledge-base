"""
Authentication system for Corporate Law Document Generator.

Features:
- SQLite user database
- Bcrypt password hashing
- Session management via Streamlit session state
- Role-based access (admin, user)
- Per-user data isolation
"""

import sqlite3
import bcrypt
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class User:
    """User model."""

    def __init__(
        self,
        user_id: int,
        email: str,
        full_name: str,
        role: str,
        created_at: str,
        is_active: bool = True,
    ):
        self.user_id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.created_at = created_at
        self.is_active = is_active

    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "created_at": self.created_at,
            "is_active": self.is_active,
        }


class AuthManager:
    """Manages user authentication and session state."""

    DB_PATH = Path("./users.db")

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with users table."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        conn.commit()
        conn.close()

        # Create default admin user if no users exist
        if self.get_user_count() == 0:
            self._create_default_admin()

    def _create_default_admin(self):
        """Create a default admin user for initial setup."""
        # Default credentials: admin@lawfirm.com / Admin123!
        self.register_user(
            email="admin@lawfirm.com",
            password="Admin123!",
            full_name="System Administrator",
            role="admin",
        )

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    def validate_email(self, email: str) -> tuple[bool, str]:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, ""

    def validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Requirements: 8+ chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, ""

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "user",
    ) -> tuple[bool, str]:
        """
        Register a new user.
        Returns (success: bool, message: str)
        """
        # Validate email
        valid, msg = self.validate_email(email)
        if not valid:
            return False, msg

        # Validate password (skip for default admin creation)
        if email != "admin@lawfirm.com":
            valid, msg = self.validate_password(password)
            if not valid:
                return False, msg

        # Validate name
        if not full_name or len(full_name.strip()) < 2:
            return False, "Full name is required"

        # Check if user already exists
        if self.get_user_by_email(email):
            return False, "Email already registered"

        # Hash password
        password_hash = self._hash_password(password)

        # Insert into database
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
                """,
                (email.lower(), password_hash, full_name.strip(), role)
            )
            conn.commit()
            conn.close()
            return True, "Registration successful"
        except sqlite3.IntegrityError:
            return False, "Email already registered"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def login(self, email: str, password: str) -> tuple[bool, Optional[User], str]:
        """
        Authenticate a user.
        Returns (success: bool, user: Optional[User], message: str)
        """
        user = self.get_user_by_email(email)

        if not user:
            return False, None, "Invalid email or password"

        if not user.is_active:
            return False, None, "Account has been deactivated. Contact administrator."

        # Verify password
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (email.lower(),)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, None, "Invalid email or password"

        password_hash = row[0]

        if self._verify_password(password, password_hash):
            return True, user, "Login successful"
        else:
            return False, None, "Invalid email or password"

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, full_name, role, created_at, is_active
            FROM users WHERE email = ?
            """,
            (email.lower(),)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return User(
                user_id=row[0],
                email=row[1],
                full_name=row[2],
                role=row[3],
                created_at=row[4],
                is_active=bool(row[5]),
            )
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, full_name, role, created_at, is_active
            FROM users WHERE user_id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return User(
                user_id=row[0],
                email=row[1],
                full_name=row[2],
                role=row[3],
                created_at=row[4],
                is_active=bool(row[5]),
            )
        return None

    def get_all_users(self) -> list[User]:
        """Retrieve all users (admin only)."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, full_name, role, created_at, is_active
            FROM users ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            User(
                user_id=row[0],
                email=row[1],
                full_name=row[2],
                role=row[3],
                created_at=row[4],
                is_active=bool(row[5]),
            )
            for row in rows
        ]

    def get_user_count(self) -> int:
        """Get total number of users."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def toggle_user_active(self, user_id: int) -> tuple[bool, str]:
        """Toggle user active status (admin only)."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            # Get current status
            cursor.execute(
                "SELECT is_active FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "User not found"

            new_status = not bool(row[0])

            # Update status
            cursor.execute(
                "UPDATE users SET is_active = ? WHERE user_id = ?",
                (new_status, user_id)
            )
            conn.commit()
            conn.close()

            status_text = "activated" if new_status else "deactivated"
            return True, f"User {status_text} successfully"
        except Exception as e:
            return False, f"Failed to update user: {str(e)}"

    def change_user_role(self, user_id: int, new_role: str) -> tuple[bool, str]:
        """Change user role (admin only)."""
        if new_role not in ["admin", "user"]:
            return False, "Invalid role"

        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET role = ? WHERE user_id = ?",
                (new_role, user_id)
            )
            conn.commit()
            conn.close()
            return True, f"User role changed to {new_role}"
        except Exception as e:
            return False, f"Failed to change role: {str(e)}"

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> tuple[bool, str]:
        """Change user password."""
        # Get user
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        # Verify old password
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()

        if not row or not self._verify_password(old_password, row[0]):
            conn.close()
            return False, "Current password is incorrect"

        # Validate new password
        valid, msg = self.validate_password(new_password)
        if not valid:
            conn.close()
            return False, msg

        # Update password
        new_hash = self._hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (new_hash, user_id)
        )
        conn.commit()
        conn.close()

        return True, "Password changed successfully"


def init_session_state(st_session_state):
    """Initialize authentication-related session state variables."""
    if "authenticated" not in st_session_state:
        st_session_state.authenticated = False
    if "current_user" not in st_session_state:
        st_session_state.current_user = None
    if "show_register" not in st_session_state:
        st_session_state.show_register = False


def require_auth(st_session_state) -> bool:
    """Check if user is authenticated. Returns True if authenticated."""
    return st_session_state.get("authenticated", False)


def require_admin(st_session_state) -> bool:
    """Check if user is an admin. Returns True if admin."""
    if not require_auth(st_session_state):
        return False
    user = st_session_state.get("current_user")
    return user and user.is_admin()


def logout(st_session_state):
    """Log out the current user."""
    st_session_state.authenticated = False
    st_session_state.current_user = None
    # Clear user-specific data
    if "messages" in st_session_state:
        st_session_state.messages = []
    if "generated_text" in st_session_state:
        st_session_state.generated_text = ""
    if "generated_title" in st_session_state:
        st_session_state.generated_title = ""


def get_user_collection_name(user_id: int) -> str:
    """Get the ChromaDB collection name for a specific user."""
    return f"user_{user_id}_documents"

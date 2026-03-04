"""
Authentication system for Corporate Law Document Generator.

Features:
- SQLite user database
- Bcrypt password hashing
- Session management via Streamlit session state
- Role-based access (admin, user)
- Per-user data isolation
- Optional email verification (6-digit code via SMTP)
- Configurable email-domain restrictions
"""

import sqlite3
import bcrypt
import re
import os
import secrets
import smtplib
import logging

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DEFAULT_ALLOWED_DOMAIN = "cypressllp.com"
MAX_VERIFICATION_ATTEMPTS = 8
VERIFICATION_RESEND_COOLDOWN_SECONDS = 60

logger = logging.getLogger(__name__)


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
        email_verified: bool = False,
        must_change_password: bool = False,
    ):
        self.user_id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.created_at = created_at
        self.is_active = is_active
        self.email_verified = email_verified
        self.must_change_password = must_change_password

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
            "email_verified": self.email_verified,
            "must_change_password": self.must_change_password,
        }


class AuthManager:
    """Manages user authentication and session state."""

    DB_PATH = Path(__file__).resolve().parent / "users.db"

    def __init__(self):
        self.allowed_email_domains = self._load_allowed_email_domains()
        self.require_email_verification = self._load_email_verification_requirement()
        if self.allowed_email_domains:
            self.primary_allowed_domain = sorted(self.allowed_email_domains)[0]
        else:
            self.primary_allowed_domain = DEFAULT_ALLOWED_DOMAIN
        self._init_db()

    def _load_email_verification_requirement(self) -> bool:
        """Return True when email verification is required for sign-up/sign-in."""
        value = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _load_allowed_email_domains(self) -> Optional[set[str]]:
        """
        Load allowed email domains from environment.
        - ALLOWED_EMAIL_DOMAINS="*" or "any" means any domain is allowed.
        - Otherwise use comma-separated domains (with or without leading "@").
        - Falls back to legacy ALLOWED_DOMAIN, then DEFAULT_ALLOWED_DOMAIN.
        """
        configured = os.getenv("ALLOWED_EMAIL_DOMAINS", "").strip()
        if configured:
            if configured in {"*", "any", "ANY"}:
                return None
            parsed = {
                domain.strip().lower().lstrip("@")
                for domain in configured.split(",")
                if domain.strip()
            }
            return parsed if parsed else {DEFAULT_ALLOWED_DOMAIN}

        legacy = os.getenv("ALLOWED_DOMAIN", "").strip().lower().lstrip("@")
        if legacy:
            return {legacy}

        return {DEFAULT_ALLOWED_DOMAIN}

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
                is_active BOOLEAN DEFAULT 1,
                email_verified BOOLEAN DEFAULT 0,
                verification_code TEXT,
                verification_expires TIMESTAMP,
                must_change_password BOOLEAN DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                verification_attempts INTEGER DEFAULT 0,
                last_verification_sent TIMESTAMP
            )
        """)

        # Migrate existing tables: add new columns if missing
        migrated_verified = False
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
            migrated_verified = True
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN verification_expires TIMESTAMP")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN verification_attempts INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_verification_sent TIMESTAMP")
        except sqlite3.OperationalError:
            pass

        # Mark all pre-existing users as verified so they aren't locked out
        if migrated_verified:
            cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified = 0")

        conn.commit()
        conn.close()

        # Create default admin user if no users exist
        if self.get_user_count() == 0:
            self._create_default_admin()

    def _create_default_admin(self):
        """Create a bootstrap admin user for initial setup."""
        admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", f"admin@{self.primary_allowed_domain}").strip().lower()
        admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "").strip()

        admin_domain = admin_email.split("@")[-1]
        if self.allowed_email_domains and admin_domain not in self.allowed_email_domains:
            admin_email = f"admin@{self.primary_allowed_domain}"

        generated = False
        if not admin_password:
            # Generate one-time bootstrap credential if no explicit secret is provided.
            admin_password = f"{secrets.token_urlsafe(14)}A1!"
            generated = True

        success, message = self.register_user(
            email=admin_email,
            password=admin_password,
            full_name="System Administrator",
            role="admin",
            skip_verification=True,
            must_change_password=True,
        )

        if not success:
            logger.error("Failed to create bootstrap admin account: %s", message)
            return

        if generated:
            try:
                bootstrap_file = Path("./bootstrap_admin_credentials.txt")
                bootstrap_file.write_text(
                    "Temporary bootstrap admin credentials\n"
                    f"Email: {admin_email}\n"
                    f"Password: {admin_password}\n"
                    "Rotate this password immediately after first login.\n",
                    encoding="utf-8",
                )
                logger.warning("Bootstrap admin credentials written to %s", bootstrap_file.resolve())
            except Exception as exc:
                logger.warning("Could not write bootstrap admin credentials file: %s", exc)

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
        """Validate email format and optional domain restriction."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        domain = email.strip().lower().split("@")[-1]
        if self.allowed_email_domains and domain not in self.allowed_email_domains:
            allowed = sorted(self.allowed_email_domains)
            if len(allowed) == 1:
                return False, f"Only @{allowed[0]} email addresses are permitted"
            allowed_text = ", ".join(f"@{value}" for value in allowed)
            return False, f"Only these email domains are permitted: {allowed_text}"
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

    def _generate_verification_code(self) -> str:
        """Generate a cryptographically secure 6-digit verification code."""
        return f"{secrets.randbelow(1_000_000):06d}"

    def _send_verification_email(self, email: str, code: str, full_name: str) -> tuple[bool, str]:
        """Send verification code via SMTP."""
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from = os.getenv("SMTP_FROM", smtp_user)

        if not smtp_user or not smtp_password:
            return False, "Email service not configured. Contact administrator."

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your Document Generator account"
        msg["From"] = smtp_from
        msg["To"] = email

        html = f"""\
        <html>
        <body style="font-family: Arial, sans-serif; background: #0f1923; color: #ffffff; padding: 2rem;">
            <div style="max-width: 480px; margin: 0 auto; background: #1a2a3a; border-radius: 12px; padding: 2rem;">
                <h2 style="color: #d4af37; margin-top: 0;">Email Verification</h2>
                <p>Hi {full_name},</p>
                <p>Your verification code is:</p>
                <div style="text-align: center; margin: 1.5rem 0;">
                    <span style="font-size: 2rem; font-weight: bold; letter-spacing: 0.3em; color: #d4af37;
                                 background: rgba(212,175,55,0.1); padding: 0.75rem 1.5rem; border-radius: 8px;">
                        {code}
                    </span>
                </div>
                <p style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">
                    This code expires in 15 minutes. If you didn't request this, ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, email, msg.as_string())
            return True, "Verification email sent"
        except Exception as e:
            return False, f"Failed to send verification email: {str(e)}"

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "user",
        skip_verification: bool = False,
        must_change_password: bool = False,
    ) -> tuple[bool, str]:
        """
        Register a new user.
        Returns (success: bool, message: str)
        """
        # Validate email
        valid, msg = self.validate_email(email)
        if not valid:
            return False, msg

        if role not in ["admin", "user"]:
            return False, "Invalid role"

        # Validate password for all user registrations.
        # Bootstrap admin creation may bypass this via skip_verification + admin role.
        if not (skip_verification and role == "admin"):
            valid, msg = self.validate_password(password)
            if not valid:
                return False, msg

        # Validate name
        if not full_name or len(full_name.strip()) < 2:
            return False, "Full name is required"

        # Check if user already exists
        existing = self.get_user_by_email(email)
        if existing:
            if existing.email_verified:
                return False, "Email already registered"
            else:
                # Allow re-registration if previous attempt was never verified
                conn = sqlite3.connect(self.DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (existing.user_id,))
                conn.commit()
                conn.close()

        # Hash password
        password_hash = self._hash_password(password)

        effective_skip_verification = skip_verification or not self.require_email_verification

        # Generate verification code
        verified = 1 if effective_skip_verification else 0
        code = None
        expires = None
        verification_attempts = 0
        last_verification_sent = None
        if not effective_skip_verification:
            code = self._generate_verification_code()
            expires = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            last_verification_sent = datetime.utcnow().isoformat()

        # Insert into database
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role,
                                   email_verified, verification_code, verification_expires,
                                   must_change_password, verification_attempts, last_verification_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (email.lower(), password_hash, full_name.strip(), role,
                 verified, code, expires, 1 if must_change_password else 0,
                 verification_attempts, last_verification_sent)
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return False, "Email already registered"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

        # Send verification email
        if not effective_skip_verification:
            ok, send_msg = self._send_verification_email(email, code, full_name)
            if not ok:
                # Keep registration atomic: remove pending user if email delivery failed.
                conn = sqlite3.connect(self.DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM users WHERE email = ? AND email_verified = 0",
                    (email.lower(),),
                )
                conn.commit()
                conn.close()
                return False, send_msg
            return True, "Verification code sent to your email"

        return True, "Registration successful"

    def verify_email(self, email: str, code: str) -> tuple[bool, str]:
        """Verify a user's email with the 6-digit code."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT verification_code, verification_expires, email_verified, verification_attempts
            FROM users WHERE email = ?
            """,
            (email.lower(),)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "Account not found"

        stored_code, expires_str, already_verified, verification_attempts = row

        if already_verified:
            conn.close()
            return True, "Email already verified"

        if verification_attempts >= MAX_VERIFICATION_ATTEMPTS:
            conn.close()
            return False, "Too many incorrect attempts. Please request a new code."

        if not stored_code or not expires_str:
            conn.close()
            return False, "No verification pending"

        if datetime.utcnow() > datetime.fromisoformat(expires_str):
            conn.close()
            return False, "Verification code has expired. Please request a new code."

        if code.strip() != stored_code:
            cursor.execute(
                "UPDATE users SET verification_attempts = verification_attempts + 1 WHERE email = ?",
                (email.lower(),)
            )
            conn.commit()
            conn.close()
            return False, "Invalid verification code"

        cursor.execute(
            """
            UPDATE users
            SET email_verified = 1,
                verification_code = NULL,
                verification_expires = NULL,
                verification_attempts = 0
            WHERE email = ?
            """,
            (email.lower(),)
        )
        conn.commit()
        conn.close()
        return True, "Email verified successfully"

    def resend_verification(self, email: str) -> tuple[bool, str]:
        """Resend a new verification code."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT full_name, email_verified, last_verification_sent
            FROM users WHERE email = ?
            """,
            (email.lower(),)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Account not found"

        full_name, already_verified, last_verification_sent = row
        if already_verified:
            conn.close()
            return True, "Email already verified"

        if last_verification_sent:
            last_sent = datetime.fromisoformat(last_verification_sent)
            elapsed = (datetime.utcnow() - last_sent).total_seconds()
            if elapsed < VERIFICATION_RESEND_COOLDOWN_SECONDS:
                remaining = int(VERIFICATION_RESEND_COOLDOWN_SECONDS - elapsed)
                conn.close()
                return False, f"Please wait {remaining}s before requesting another code"

        code = self._generate_verification_code()
        expires = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        now_iso = datetime.utcnow().isoformat()
        cursor.execute(
            """
            UPDATE users
            SET verification_code = ?, verification_expires = ?,
                verification_attempts = 0, last_verification_sent = ?
            WHERE email = ?
            """,
            (code, expires, now_iso, email.lower())
        )
        conn.commit()
        conn.close()

        ok, send_msg = self._send_verification_email(email, code, full_name)
        if not ok:
            return False, send_msg
        return True, "New verification code sent"

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

        if self.require_email_verification and not user.email_verified:
            return False, None, "Email not verified. Please check your inbox for the verification code."

        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT password_hash, failed_login_attempts
            FROM users WHERE email = ?
            """,
            (email.lower(),)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, None, "Invalid email or password"

        password_hash, failed_attempts = row

        if self._verify_password(password, password_hash):
            cursor.execute(
                "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE email = ?",
                (email.lower(),)
            )
            conn.commit()
            conn.close()
            return True, user, "Login successful"

        failed_attempts = (failed_attempts or 0) + 1
        cursor.execute(
            "UPDATE users SET failed_login_attempts = ?, locked_until = NULL WHERE email = ?",
            (failed_attempts, email.lower())
        )
        conn.commit()
        conn.close()
        return False, None, "Invalid email or password"

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, full_name, role, created_at, is_active, email_verified, must_change_password
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
                email_verified=bool(row[6]),
                must_change_password=bool(row[7]),
            )
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, full_name, role, created_at, is_active, email_verified, must_change_password
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
                email_verified=bool(row[6]),
                must_change_password=bool(row[7]),
            )
        return None

    def get_all_users(self) -> list[User]:
        """Retrieve all users (admin only)."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, email, full_name, role, created_at, is_active, email_verified, must_change_password
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
                email_verified=bool(row[6]),
                must_change_password=bool(row[7]),
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
            "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE user_id = ?",
            (new_hash, user_id)
        )
        conn.commit()
        conn.close()

        return True, "Password changed successfully"


def start_authenticated_session(st_session_state, user: User):
    """Persist a successful authentication with session security metadata."""
    now = datetime.utcnow().isoformat()
    st_session_state.authenticated = True
    st_session_state.current_user = user
    st_session_state.authenticated_at = now
    st_session_state.last_activity_at = now
    st_session_state.auth_expired_reason = None


def init_session_state(st_session_state):
    """Initialize authentication-related session state variables."""
    if "authenticated" not in st_session_state:
        st_session_state.authenticated = False
    if "current_user" not in st_session_state:
        st_session_state.current_user = None
    if "show_register" not in st_session_state:
        st_session_state.show_register = False
    if "verify_email" not in st_session_state:
        st_session_state.verify_email = None
    if "authenticated_at" not in st_session_state:
        st_session_state.authenticated_at = None
    if "last_activity_at" not in st_session_state:
        st_session_state.last_activity_at = None
    if "auth_expired_reason" not in st_session_state:
        st_session_state.auth_expired_reason = None
    if "login_rate_attempts" not in st_session_state:
        st_session_state.login_rate_attempts = []
    if "login_rate_limited_until" not in st_session_state:
        st_session_state.login_rate_limited_until = 0.0


def require_auth(st_session_state) -> bool:
    """Check if user is authenticated and session has not expired."""
    if not st_session_state.get("authenticated", False):
        return False

    now = datetime.utcnow()
    idle_minutes = max(1, int(os.getenv("SESSION_IDLE_TIMEOUT_MINUTES", "15")))
    absolute_hours = max(1, int(os.getenv("SESSION_ABSOLUTE_TIMEOUT_HOURS", "8")))

    authenticated_at = st_session_state.get("authenticated_at")
    last_activity_at = st_session_state.get("last_activity_at")

    if not authenticated_at or not last_activity_at:
        stamp = now.isoformat()
        st_session_state.authenticated_at = stamp
        st_session_state.last_activity_at = stamp
        return True

    try:
        auth_time = datetime.fromisoformat(authenticated_at)
        last_activity = datetime.fromisoformat(last_activity_at)
    except ValueError:
        stamp = now.isoformat()
        st_session_state.authenticated_at = stamp
        st_session_state.last_activity_at = stamp
        return True

    if (now - auth_time) > timedelta(hours=absolute_hours):
        st_session_state.auth_expired_reason = "Your session expired for security reasons. Please sign in again."
        logout(st_session_state)
        return False

    if (now - last_activity) > timedelta(minutes=idle_minutes):
        st_session_state.auth_expired_reason = "You were signed out after inactivity. Please sign in again."
        logout(st_session_state)
        return False

    st_session_state.last_activity_at = now.isoformat()
    return True


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
    st_session_state.authenticated_at = None
    st_session_state.last_activity_at = None
    st_session_state.verify_email = False
    st_session_state.verification_user_id = None

    # Reset navigation state so user lands on login view on rerun.
    st_session_state.show_settings = False
    st_session_state.show_knowledge_base = False
    st_session_state.show_model_improvement = False
    st_session_state.workflow_mode = None

    # Clear user-specific data.
    if "messages" in st_session_state:
        st_session_state.messages = []
    if "generated_text" in st_session_state:
        st_session_state.generated_text = ""
    if "generated_title" in st_session_state:
        st_session_state.generated_title = ""


def get_user_collection_name(user_id: int) -> str:
    """Get the ChromaDB collection name for a specific user."""
    return f"user_{user_id}_documents"

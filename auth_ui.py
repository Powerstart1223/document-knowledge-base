"""
Authentication UI components for Corporate Law Document Generator.

Sigma-inspired minimal, elegant dark login design.
"""

import os
import time
import streamlit as st
from auth import AuthManager, init_session_state, logout, User, start_authenticated_session


_LOGIN_CSS = """
<style>
    section[data-testid="stSidebar"] { display: none !important; }

    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #f8faf8 100%);
    }

    .main .block-container {
        max-width: 520px;
        margin: 0 auto;
        padding-top: 8vh;
        padding-bottom: 2rem;
    }

    .login-brand {
        text-align: center;
        margin-bottom: 1.3rem;
    }

    .login-brand .logo-icon {
        width: 52px;
        height: 52px;
        background: #0f1720;
        color: #ffffff;
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 0.95rem;
    }

    .login-brand h1 {
        color: #121212;
        font-size: 1.45rem;
        font-weight: 750;
        letter-spacing: -0.02em;
        margin: 0 0 0.2rem 0;
    }

    .login-brand p {
        color: #414141;
        font-size: 0.88rem;
        margin: 0;
    }

    .form-header {
        text-align: center;
        margin-bottom: 1rem;
    }

    .form-header h2 {
        color: #1f1f1f;
        font-size: 1.02rem;
        font-weight: 650;
        margin: 0;
    }

    .stTextInput label {
        color: #2f2f2f !important;
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
    }

    .stApp .stTextInput > div > div > input,
    .stApp input[type="text"],
    .stApp input[type="password"],
    [data-testid="stTextInput"] input,
    [data-baseweb="input"] input {
        background: #ffffff !important;
        border: 1px solid #b8beb8 !important;
        border-radius: 10px !important;
        color: #121212 !important;
        padding: 0.74rem 0.86rem !important;
        font-size: 0.92rem !important;
        -webkit-text-fill-color: #121212 !important;
    }

    .stApp .stTextInput > div > div > input:focus,
    .stApp input[type="text"]:focus,
    .stApp input[type="password"]:focus,
    [data-testid="stTextInput"] input:focus {
        border-color: #0f1720 !important;
        box-shadow: 0 0 0 3px rgba(15, 23, 32, 0.08) !important;
    }

    .stApp input::placeholder,
    [data-baseweb="input"] input::placeholder {
        color: #7a7a7a !important;
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button,
    .stFormSubmitButton > button[kind="primary"] {
        background: #171717 !important;
        color: #ffffff !important;
        border: 1px solid #171717 !important;
        border-radius: 999px !important;
        min-height: 2.18rem !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        padding: 0.32rem 1rem !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover {
        background: #000000 !important;
    }

    .stButton > button:not([kind="primary"]) {
        background: #ffffff !important;
        color: #161616 !important;
        border: 1px solid #b8beb8 !important;
        border-radius: 999px !important;
        min-height: 2.12rem !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        padding: 0.32rem 1rem !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: #f1f4f1 !important;
    }

    .login-divider {
        border-top: 1px solid #d5d9d5;
        margin: 1.05rem 0;
    }

    .login-security {
        text-align: center;
        margin-top: 1.05rem;
        color: #606060;
        font-size: 0.75rem;
    }

    .pw-reqs {
        color: #5b5b5b;
        font-size: 0.78rem;
        line-height: 1.55;
        margin-top: 0.25rem;
    }

    .stCaption, small {
        color: #626262 !important;
    }
</style>
"""


def _get_login_rate_config() -> tuple[int, int, int]:
    """Return (max_attempts, window_seconds, cooldown_seconds)."""
    max_attempts = max(1, int(os.getenv("LOGIN_MAX_ATTEMPTS_PER_WINDOW", "6")))
    window_seconds = max(10, int(os.getenv("LOGIN_WINDOW_SECONDS", "60")))
    cooldown_seconds = max(10, int(os.getenv("LOGIN_COOLDOWN_SECONDS", "90")))
    return max_attempts, window_seconds, cooldown_seconds


def _too_many_login_attempts() -> tuple[bool, int]:
    """Per-session login throttle to slow credential stuffing attempts."""
    now = time.time()
    lock_until = float(st.session_state.get("login_rate_limited_until", 0.0) or 0.0)
    if lock_until > now:
        return True, int(lock_until - now)

    max_attempts, window_seconds, cooldown_seconds = _get_login_rate_config()
    attempts = [
        ts for ts in st.session_state.get("login_rate_attempts", [])
        if isinstance(ts, (int, float)) and (now - ts) <= window_seconds
    ]
    st.session_state.login_rate_attempts = attempts

    if len(attempts) >= max_attempts:
        until = now + cooldown_seconds
        st.session_state.login_rate_limited_until = until
        st.session_state.login_rate_attempts = []
        return True, cooldown_seconds

    return False, 0


def _record_failed_login_attempt():
    now = time.time()
    attempts = st.session_state.get("login_rate_attempts", [])
    attempts.append(now)
    st.session_state.login_rate_attempts = attempts


def _clear_login_throttle_state():
    st.session_state.login_rate_attempts = []
    st.session_state.login_rate_limited_until = 0.0

def render_login_page(auth_manager: AuthManager):
    """Render a clean, high-contrast login page."""

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    expired_reason = st.session_state.pop("auth_expired_reason", None)
    if expired_reason:
        st.warning(expired_reason)

    # Brand
    st.markdown("""
    <div class="login-brand">
        <div class="logo-icon">&#9878;</div>
        <h1>Document Generator</h1>
        <p>AI-powered legal drafting platform</p>
    </div>
    <div class="form-header">
        <h2>Sign in to your account</h2>
    </div>
    """, unsafe_allow_html=True)

    # Login form — renders directly below brand
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        submit = st.form_submit_button(
            "Sign In",
            type="primary",
            use_container_width=True
        )

        if submit:
            rate_limited, wait_seconds = _too_many_login_attempts()
            if rate_limited:
                st.error(f"Too many login attempts. Please wait {wait_seconds}s and try again.")
            elif not email or not password:
                st.error("Please enter both email and password.")
            else:
                success, user, message = auth_manager.login(email, password)
                if success:
                    _clear_login_throttle_state()
                    start_authenticated_session(st.session_state, user)
                    # Always land users on the primary workspace after login.
                    st.session_state.show_settings = False
                    st.session_state.show_knowledge_base = False
                    st.session_state.workflow_mode = None
                    st.rerun()
                else:
                    _record_failed_login_attempt()
                    st.error(message)

    # Divider
    st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)

    # Create account button
    if st.button("Create Account", use_container_width=True):
        st.session_state.show_register = True
        st.rerun()
    st.markdown('<div class="login-security">Encrypted & secure</div>', unsafe_allow_html=True)


def render_registration_page(auth_manager: AuthManager):
    """Render a clean, high-contrast registration page."""

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # Brand
    st.markdown(f"""
    <div class="login-brand">
        <div class="logo-icon">&#9878;</div>
        <h1>Document Generator</h1>
        <p>AI-powered legal drafting platform</p>
    </div>
    <div class="form-header">
        <h2>Create your account</h2>
    </div>
    """, unsafe_allow_html=True)

    with st.form("registration_form", clear_on_submit=True):
        full_name = st.text_input(
            "Full Name",
            placeholder="Jane Smith",
            key="reg_name"
        )

        email = st.text_input(
            "Email",
            placeholder="jane.smith@example.com",
            key="reg_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            key="reg_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
            key="reg_confirm"
        )

        st.markdown("""
        <div class="pw-reqs">
            8+ characters &middot; uppercase &middot; lowercase &middot; number &middot; special character
        </div>
        """, unsafe_allow_html=True)

        submit = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True
        )

        if submit:
            if not all([full_name, email, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = auth_manager.register_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    role="user",
                    skip_verification=True,
                )
                if success:
                    st.session_state.verify_email = None
                    st.session_state.show_register = False
                    st.success("Account created. Sign in with your new password.")
                    st.rerun()
                else:
                    st.error(message)

    st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)

    if st.button("Back to Sign In", use_container_width=True):
        st.session_state.show_register = False
        st.rerun()


def render_verification_page(auth_manager: AuthManager):
    """Render the email verification code entry page."""

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    email = st.session_state.get("verify_email", "")

    st.markdown("""
    <div class="login-brand">
        <div class="logo-icon">&#9878;</div>
        <h1>Document Generator</h1>
        <p>AI-powered legal drafting platform</p>
    </div>
    <div class="form-header">
        <h2>Verify your email</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center; color: #4a4a4a; font-size: 0.88rem; margin-bottom: 1.25rem;">
        We sent a 6-digit code to <strong style="color:#d4af37;">{email}</strong>
    </div>
    """, unsafe_allow_html=True)

    with st.form("verify_form", clear_on_submit=False):
        code = st.text_input(
            "Verification Code",
            placeholder="123456",
            max_chars=6,
            key="verify_code"
        )

        submit = st.form_submit_button(
            "Verify Email",
            type="primary",
            use_container_width=True
        )

        if submit:
            if not code or len(code.strip()) != 6:
                st.error("Please enter the 6-digit code.")
            else:
                success, message = auth_manager.verify_email(email, code)
                if success:
                    st.session_state.verify_email = None
                    st.success("Email verified! You can now sign in.")
                    import time
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Resend Code", use_container_width=True):
            success, message = auth_manager.resend_verification(email)
            if success:
                st.success("New code sent!")
            else:
                st.error(message)
    with col2:
        if st.button("Back to Sign In", use_container_width=True, key="verify_back"):
            st.session_state.verify_email = None
            st.rerun()


def render_admin_panel(auth_manager: AuthManager, current_user: User):
    """Render the admin panel for user management."""
    if not current_user.is_admin():
        st.error("Access denied. Admin privileges required.")
        return

    st.markdown("""
    <div class="card-header">
        User Management
    </div>
    """, unsafe_allow_html=True)

    users = auth_manager.get_all_users()
    total_users = len(users)
    active_users = sum(1 for u in users if u.is_active)
    admin_users = sum(1 for u in users if u.role == "admin")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Active Users", active_users)
    with col3:
        st.metric("Administrators", admin_users)

    st.caption("Manage account status and role assignments. Changes apply immediately.")
    st.divider()

    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 1.5, 1.5])

            with col1:
                st.markdown(f"**{user.full_name}**")
                st.caption(user.email)

            with col2:
                role_color = "var(--accent-gold)" if user.is_admin() else "var(--text-secondary)"
                st.markdown(f"""
                <div style="
                    display: inline-block;
                    background: {role_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                ">
                {user.role}
                </div>
                """, unsafe_allow_html=True)

            with col3:
                status_class = "success" if user.is_active else "error"
                status_text = "Active" if user.is_active else "Inactive"
                st.markdown(f"""
                <span class="status-badge status-{status_class}">
                {status_text}
                </span>
                """, unsafe_allow_html=True)

            with col4:
                if user.user_id != current_user.user_id:
                    action_text = "Deactivate" if user.is_active else "Activate"
                    if st.button(action_text, key=f"toggle_{user.user_id}", use_container_width=True):
                        success, msg = auth_manager.toggle_user_active(user.user_id)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with col5:
                if user.user_id != current_user.user_id:
                    new_role = "user" if user.is_admin() else "admin"
                    role_text = "Make User" if user.is_admin() else "Make Admin"
                    if st.button(role_text, key=f"role_{user.user_id}", use_container_width=True):
                        success, msg = auth_manager.change_user_role(user.user_id, new_role)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            if user.user_id == current_user.user_id:
                st.caption("Current account: role/status changes are disabled for this row.")
            st.caption(f"Joined: {user.created_at[:10]}")
            st.divider()


def render_profile_settings(auth_manager: AuthManager, current_user: User):
    """Render user profile and settings."""
    st.markdown("""
    <div class="card-header">
        Profile Settings
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-card">
        <strong>Name:</strong> {current_user.full_name}<br>
        <strong>Email:</strong> {current_user.email}<br>
        <strong>Role:</strong> {current_user.role.title()}<br>
        <strong>Member Since:</strong> {current_user.created_at[:10]}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if current_user.must_change_password:
        st.warning("Password update required before continuing. Please set a new password now.")

    st.subheader("Change Password")
    st.caption("Use at least 8 characters and include upper/lowercase letters, a number, and a special character.")

    with st.form("change_password_form"):
        old_password = st.text_input("Current Password", type="password", key="old_pass")
        new_password = st.text_input(
            "New Password", type="password", key="new_pass",
            help="8+ characters with uppercase, lowercase, number, and special character"
        )
        confirm_new = st.text_input("Confirm New Password", type="password", key="confirm_new")

        submit = st.form_submit_button("Update Password", type="primary")

        if submit:
            if not all([old_password, new_password, confirm_new]):
                st.error("Please fill in all fields.")
            elif new_password != confirm_new:
                st.error("New passwords do not match.")
            else:
                success, msg = auth_manager.change_password(
                    current_user.user_id, old_password, new_password
                )
                if success:
                    current_user.must_change_password = False
                    st.success(msg)
                    st.caption("Password updated. Use your new password on the next sign-in.")
                else:
                    st.error(msg)


def render_auth_sidebar(current_user: User):
    """Render authentication-related sidebar content."""
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-header">
            <h2>{current_user.full_name}</h2>
            <div style="
                color: var(--accent-gold-light);
                font-size: 0.85rem;
                margin-top: 0.4rem;
            ">
            {current_user.email}
            </div>
            <div style="
                color: rgba(255, 255, 255, 0.5);
                font-size: 0.75rem;
                margin-top: 0.25rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            ">
            {current_user.role}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Sign Out", use_container_width=True):
            logout(st.session_state)
            st.rerun()

        st.divider()

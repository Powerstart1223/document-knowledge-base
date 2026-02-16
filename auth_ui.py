"""
Authentication UI components for Corporate Law Document Generator.

Sigma-inspired minimal, elegant dark login design.
"""

import streamlit as st
from auth import AuthManager, init_session_state, logout, User, ALLOWED_DOMAIN


_LOGIN_CSS = """
<style>
    /* Hide sidebar and reset padding on auth pages */
    section[data-testid="stSidebar"] { display: none; }
    header[data-testid="stHeader"] { background: #0f1923; }

    .main .block-container {
        max-width: 440px;
        margin: 0 auto;
        padding-top: 8vh;
        padding-bottom: 4rem;
    }

    /* Dark background on the whole page */
    .stApp {
        background: linear-gradient(160deg, #0f1923 0%, #1a2a3a 40%, #243447 100%);
    }

    /* Brand section */
    .login-brand {
        text-align: center;
        margin-bottom: 2rem;
        padding-top: 1rem;
    }

    .login-brand .logo-icon {
        width: 56px;
        height: 56px;
        background: linear-gradient(135deg, #d4af37 0%, #f0d878 100%);
        border-radius: 16px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 24px rgba(212, 175, 55, 0.25);
    }

    .login-brand h1 {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 600;
        letter-spacing: -0.03em;
        margin: 0 0 0.35rem 0;
    }

    .login-brand p {
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.875rem;
        margin: 0;
    }

    /* Section header for form */
    .form-header {
        text-align: center;
        margin-bottom: 1.25rem;
    }

    .form-header h2 {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0;
    }

    /* Override Streamlit input/button styles for dark theme */
    .stTextInput label {
        color: rgba(255, 255, 255, 0.55) !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    /* Force dark inputs — override all Streamlit specificity */
    .stApp .stTextInput > div > div > input,
    .stApp .stTextInput input,
    .stApp input[type="text"],
    .stApp input[type="password"],
    .stApp input[type="email"],
    [data-testid="stTextInput"] input,
    [data-baseweb="input"] input,
    [data-baseweb="base-input"] input {
        background: rgba(255, 255, 255, 0.06) !important;
        background-color: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 0.85rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stApp .stTextInput > div > div > input:focus,
    .stApp input[type="text"]:focus,
    .stApp input[type="password"]:focus,
    [data-testid="stTextInput"] input:focus,
    [data-baseweb="input"] input:focus {
        border-color: rgba(212, 175, 55, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1) !important;
        background: rgba(255, 255, 255, 0.09) !important;
        background-color: rgba(255, 255, 255, 0.09) !important;
    }

    .stApp .stTextInput > div > div > input::placeholder,
    .stApp input::placeholder,
    [data-baseweb="input"] input::placeholder {
        color: rgba(255, 255, 255, 0.2) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* Also style the input container/wrapper from BaseWeb */
    [data-baseweb="base-input"],
    [data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
    }

    /* Password toggle icon */
    [data-testid="stTextInput"] button {
        color: rgba(255, 255, 255, 0.4) !important;
    }

    /* Primary button — gold (override Streamlit red default) */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button,
    .stFormSubmitButton > button[kind="primary"],
    button[kind="primaryFormSubmit"],
    .stFormSubmitButton button {
        background: linear-gradient(135deg, #d4af37 0%, #e8c84a 100%) !important;
        background-color: #d4af37 !important;
        color: #0f1923 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 4px 16px rgba(212, 175, 55, 0.3) !important;
        transition: all 0.25s ease !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 24px rgba(212, 175, 55, 0.4) !important;
        background: linear-gradient(135deg, #e8c84a 0%, #d4af37 100%) !important;
    }

    /* Secondary buttons — ghost style */
    .stButton > button:not([kind="primary"]) {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.55) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(255, 255, 255, 0.04) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }

    /* Divider */
    .login-divider {
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin: 1.5rem 0;
    }

    /* Footer */
    .login-security {
        text-align: center;
        margin-top: 1.5rem;
        color: rgba(255, 255, 255, 0.2);
        font-size: 0.75rem;
        letter-spacing: 0.02em;
    }

    /* Password requirements */
    .pw-reqs {
        color: rgba(255, 255, 255, 0.3);
        font-size: 0.78rem;
        line-height: 1.7;
        margin-top: 0.25rem;
    }

    /* Caption override */
    .stCaption, small {
        color: rgba(255, 255, 255, 0.3) !important;
    }
</style>
"""


def render_login_page(auth_manager: AuthManager):
    """Render a sleek, Sigma-inspired login page."""

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

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
            placeholder=f"you@{ALLOWED_DOMAIN}",
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
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                success, user, message = auth_manager.login(email, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.current_user = user
                    # Always land users on the primary workspace after login.
                    st.session_state.show_settings = False
                    st.session_state.show_knowledge_base = False
                    st.session_state.workflow_mode = None
                    st.rerun()
                else:
                    st.error(message)

    # Divider
    st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)

    # Create account button
    if st.button("Create Account", use_container_width=True):
        st.session_state.show_register = True
        st.rerun()
    st.markdown('<div class="login-security">Encrypted & secure</div>', unsafe_allow_html=True)


def render_registration_page(auth_manager: AuthManager):
    """Render a sleek, Sigma-inspired registration page."""

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

    st.markdown(f"""
    <div style="text-align:center; color: rgba(255,255,255,0.4); font-size: 0.82rem; margin-bottom: 1rem;">
        Only <strong style="color:#d4af37;">@{ALLOWED_DOMAIN}</strong> email addresses are permitted
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
            placeholder=f"jane.smith@{ALLOWED_DOMAIN}",
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
                    role="user"
                )
                if success:
                    st.session_state.verify_email = email.lower()
                    st.session_state.show_register = False
                    st.success("Check your inbox for the verification code.")
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
    <div style="text-align:center; color: rgba(255,255,255,0.5); font-size: 0.88rem; margin-bottom: 1.25rem;">
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

    st.divider()

    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 1.5, 1.5])

            with col1:
                st.markdown(f"""
                **{user.full_name}**
                <span style="color: var(--text-secondary); font-size: 0.875rem;">
                {user.email}
                </span>
                """, unsafe_allow_html=True)

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
                    role_text = "-> User" if user.is_admin() else "-> Admin"
                    if st.button(role_text, key=f"role_{user.user_id}", use_container_width=True):
                        success, msg = auth_manager.change_user_role(user.user_id, new_role)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

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

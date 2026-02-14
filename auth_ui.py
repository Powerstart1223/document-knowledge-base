"""
Authentication UI components for Corporate Law Document Generator.

Provides login, registration, and admin pages.
Sigma-inspired minimal, elegant design.
"""

import streamlit as st
from auth import AuthManager, init_session_state, logout, User


def render_login_page(auth_manager: AuthManager):
    """Render a sleek, Sigma-inspired login page."""

    # Hide sidebar on login
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none; }
        .main .block-container { max-width: 100%; padding: 0; }

        .login-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(160deg, #0f1923 0%, #1a2a3a 40%, #243447 100%);
            margin: -6rem -4rem -4rem -4rem;
            padding: 2rem;
        }

        .login-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(40px);
            -webkit-backdrop-filter: blur(40px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 3.5rem 3rem;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 32px 64px rgba(0, 0, 0, 0.3);
        }

        .login-brand {
            text-align: center;
            margin-bottom: 2.5rem;
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
            margin: 0 0 0.4rem 0;
            line-height: 1.3;
        }

        .login-brand p {
            color: rgba(255, 255, 255, 0.45);
            font-size: 0.875rem;
            margin: 0;
            font-weight: 400;
        }

        .login-label {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.8rem;
            font-weight: 500;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .login-footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        .login-footer p {
            color: rgba(255, 255, 255, 0.35);
            font-size: 0.8rem;
            margin: 0;
        }

        .login-footer a {
            color: #d4af37;
            text-decoration: none;
            font-weight: 500;
        }

        .login-security {
            text-align: center;
            margin-top: 1.5rem;
        }

        .login-security p {
            color: rgba(255, 255, 255, 0.25);
            font-size: 0.75rem;
            margin: 0;
            letter-spacing: 0.02em;
        }

        /* Override Streamlit form styles for dark login */
        .login-wrapper .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            padding: 0.85rem 1rem !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
        }

        .login-wrapper .stTextInput > div > div > input:focus {
            border-color: rgba(212, 175, 55, 0.5) !important;
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.08) !important;
            background: rgba(255, 255, 255, 0.08) !important;
        }

        .login-wrapper .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.25) !important;
        }

        .login-wrapper .stTextInput label {
            color: rgba(255, 255, 255, 0.6) !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.03em !important;
            text-transform: uppercase !important;
        }

        .login-wrapper .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #d4af37 0%, #e8c84a 100%) !important;
            color: #0f1923 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.85rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.02em !important;
            transition: all 0.25s ease !important;
            box-shadow: 0 4px 16px rgba(212, 175, 55, 0.25) !important;
        }

        .login-wrapper .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 24px rgba(212, 175, 55, 0.35) !important;
        }

        .login-wrapper .stButton > button:not([kind="primary"]) {
            background: transparent !important;
            color: rgba(255, 255, 255, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            transition: all 0.2s ease !important;
        }

        .login-wrapper .stButton > button:not([kind="primary"]):hover {
            background: rgba(255, 255, 255, 0.05) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
        }

        /* Expander styling in login */
        .login-wrapper .streamlit-expanderHeader {
            color: rgba(255, 255, 255, 0.4) !important;
            font-size: 0.85rem !important;
            background: transparent !important;
            border: none !important;
        }

        .login-wrapper .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 12px !important;
        }

        .login-wrapper .stAlert {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
        }

        .demo-creds {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.5);
        }

        .demo-creds code {
            background: rgba(212, 175, 55, 0.15);
            color: #e8c84a;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.825rem;
        }

        .demo-creds strong {
            color: rgba(255, 255, 255, 0.7);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="login-wrapper"><div class="login-card">
        <div class="login-brand">
            <div class="logo-icon">&#9878;</div>
            <h1>Document Generator</h1>
            <p>AI-powered legal drafting platform</p>
        </div>
    </div></div>""", unsafe_allow_html=True)

    # Use columns to center the form
    col1, col2, col3 = st.columns([1.2, 2, 1.2])

    with col2:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="you@lawfirm.com",
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
                        st.rerun()
                    else:
                        st.error(message)

        # Create account
        if st.button("Create Account", use_container_width=True):
            st.session_state.show_register = True
            st.rerun()

        # Demo credentials
        with st.expander("Demo credentials"):
            st.markdown("""
            <div class="demo-creds">
                <strong>Admin:</strong> <code>admin@lawfirm.com</code> / <code>Admin123!</code><br>
                <em style="font-size: 0.8rem; color: rgba(255,255,255,0.35);">Change password after first login</em>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="login-security">
            <p>&#128274; Encrypted & secure</p>
        </div>
        """, unsafe_allow_html=True)


def render_registration_page(auth_manager: AuthManager):
    """Render a sleek, Sigma-inspired registration page."""

    # Same dark styling as login
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none; }
        .main .block-container { max-width: 100%; padding: 0; }

        .reg-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(160deg, #0f1923 0%, #1a2a3a 40%, #243447 100%);
            margin: -6rem -4rem -4rem -4rem;
            padding: 2rem;
        }

        .reg-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(40px);
            -webkit-backdrop-filter: blur(40px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 3rem;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 32px 64px rgba(0, 0, 0, 0.3);
        }

        .reg-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .reg-header h1 {
            color: #ffffff;
            font-size: 1.4rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin: 0 0 0.4rem 0;
        }

        .reg-header p {
            color: rgba(255, 255, 255, 0.4);
            font-size: 0.875rem;
            margin: 0;
        }

        /* Override Streamlit form styles for dark registration */
        .reg-wrapper .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            padding: 0.85rem 1rem !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
        }

        .reg-wrapper .stTextInput > div > div > input:focus {
            border-color: rgba(212, 175, 55, 0.5) !important;
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.08) !important;
            background: rgba(255, 255, 255, 0.08) !important;
        }

        .reg-wrapper .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.25) !important;
        }

        .reg-wrapper .stTextInput label {
            color: rgba(255, 255, 255, 0.6) !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.03em !important;
            text-transform: uppercase !important;
        }

        .reg-wrapper .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #d4af37 0%, #e8c84a 100%) !important;
            color: #0f1923 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.85rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            box-shadow: 0 4px 16px rgba(212, 175, 55, 0.25) !important;
        }

        .reg-wrapper .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 24px rgba(212, 175, 55, 0.35) !important;
        }

        .reg-wrapper .stButton > button:not([kind="primary"]) {
            background: transparent !important;
            color: rgba(255, 255, 255, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
        }

        .reg-wrapper .stButton > button:not([kind="primary"]):hover {
            background: rgba(255, 255, 255, 0.05) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
        }

        .reg-wrapper .stAlert {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
        }

        .pw-reqs {
            color: rgba(255, 255, 255, 0.35);
            font-size: 0.78rem;
            line-height: 1.7;
            margin-top: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="reg-wrapper"><div class="reg-card">
        <div class="reg-header">
            <h1>Create Your Account</h1>
            <p>Join the document generation platform</p>
        </div>
    </div></div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 2, 1.2])

    with col2:
        with st.form("registration_form", clear_on_submit=True):
            full_name = st.text_input(
                "Full Name",
                placeholder="Jane Smith",
                key="reg_name"
            )

            email = st.text_input(
                "Email",
                placeholder="jane.smith@lawfirm.com",
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
                        st.session_state.show_register = False
                        # Auto-login
                        success, user, _ = auth_manager.login(email, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.current_user = user
                            st.rerun()
                    else:
                        st.error(message)

        if st.button("Back to Sign In", use_container_width=True):
            st.session_state.show_register = False
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
                    if st.button(
                        action_text,
                        key=f"toggle_{user.user_id}",
                        use_container_width=True
                    ):
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
                    if st.button(
                        role_text,
                        key=f"role_{user.user_id}",
                        use_container_width=True
                    ):
                        success, msg = auth_manager.change_user_role(
                            user.user_id,
                            new_role
                        )
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
                    current_user.user_id,
                    old_password,
                    new_password
                )
                if success:
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

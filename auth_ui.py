"""
Authentication UI components for Corporate Law Document Generator.

Provides login, registration, and admin pages.
"""

import streamlit as st
from auth import AuthManager, init_session_state, logout, User


def render_login_page(auth_manager: AuthManager):
    """Render the login page."""
    st.markdown("""
    <div class="auth-container fade-in">
        <div class="auth-header">
            <div class="logo">⚖️</div>
            <h1>Welcome Back</h1>
            <p style="color: var(--text-secondary); margin: 0;">
                Sign in to access the Corporate Law Document Generator
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input(
                    "Email Address",
                    placeholder="your.email@lawfirm.com",
                    key="login_email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button(
                        "Sign In",
                        type="primary",
                        use_container_width=True
                    )
                with col_btn2:
                    register_btn = st.form_submit_button(
                        "Create Account",
                        use_container_width=True
                    )

                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        success, user, message = auth_manager.login(email, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.current_user = user
                            st.success(f"Welcome back, {user.full_name}!")
                            st.rerun()
                        else:
                            st.error(message)

                if register_btn:
                    st.session_state.show_register = True
                    st.rerun()

            # Default credentials info
            with st.expander("Default Admin Credentials"):
                st.info("""
                **First-time login:**
                - Email: `admin@lawfirm.com`
                - Password: `Admin123!`

                Please change the password after first login.
                """)

            st.markdown("""
            <div class="auth-divider">
                <span>Secure Authentication</span>
            </div>
            """, unsafe_allow_html=True)

            st.caption("🔒 Your credentials are encrypted and stored securely")


def render_registration_page(auth_manager: AuthManager):
    """Render the registration page."""
    st.markdown("""
    <div class="auth-container fade-in">
        <div class="auth-header">
            <div class="logo">⚖️</div>
            <h1>Create Account</h1>
            <p style="color: var(--text-secondary); margin: 0;">
                Join your team on the Corporate Law Document Generator
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.form("registration_form", clear_on_submit=True):
                full_name = st.text_input(
                    "Full Name",
                    placeholder="John Doe",
                    key="reg_name"
                )

                email = st.text_input(
                    "Email Address",
                    placeholder="john.doe@lawfirm.com",
                    key="reg_email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a strong password",
                    key="reg_password",
                    help="Must be 8+ characters with uppercase, lowercase, number, and special character"
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm"
                )

                st.caption("""
                **Password Requirements:**
                - At least 8 characters
                - One uppercase letter
                - One lowercase letter
                - One number
                - One special character (!@#$%^&*)
                """)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button(
                        "Create Account",
                        type="primary",
                        use_container_width=True
                    )
                with col_btn2:
                    back_btn = st.form_submit_button(
                        "Back to Login",
                        use_container_width=True
                    )

                if submit:
                    # Validate inputs
                    if not all([full_name, email, password, confirm_password]):
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = auth_manager.register_user(
                            email=email,
                            password=password,
                            full_name=full_name,
                            role="user"
                        )
                        if success:
                            st.success(f"{message}! You can now log in.")
                            st.session_state.show_register = False
                            st.balloons()
                            # Auto-login the new user
                            success, user, _ = auth_manager.login(email, password)
                            if success:
                                st.session_state.authenticated = True
                                st.session_state.current_user = user
                                st.rerun()
                        else:
                            st.error(message)

                if back_btn:
                    st.session_state.show_register = False
                    st.rerun()

            st.markdown("""
            <div class="auth-divider">
                <span>Secure Registration</span>
            </div>
            """, unsafe_allow_html=True)

            st.caption("🔒 All passwords are hashed using bcrypt encryption")


def render_admin_panel(auth_manager: AuthManager, current_user: User):
    """Render the admin panel for user management."""
    if not current_user.is_admin():
        st.error("Access denied. Admin privileges required.")
        return

    st.markdown("""
    <div class="card-header">
        👥 User Management
    </div>
    """, unsafe_allow_html=True)

    # Stats
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

    # User list
    st.subheader("Registered Users")

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
                # Don't allow deactivating self
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
                # Don't allow changing role for self
                if user.user_id != current_user.user_id:
                    new_role = "user" if user.is_admin() else "admin"
                    role_text = "→ User" if user.is_admin() else "→ Admin"
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

            st.markdown(f"""
            <div style="
                font-size: 0.75rem;
                color: var(--text-light);
                margin-top: 0.25rem;
            ">
            Joined: {user.created_at[:10]}
            </div>
            """, unsafe_allow_html=True)

            st.divider()


def render_profile_settings(auth_manager: AuthManager, current_user: User):
    """Render user profile and settings."""
    st.markdown("""
    <div class="card-header">
        👤 Profile Settings
    </div>
    """, unsafe_allow_html=True)

    # User info
    st.markdown(f"""
    <div class="info-card">
        <strong>Name:</strong> {current_user.full_name}<br>
        <strong>Email:</strong> {current_user.email}<br>
        <strong>Role:</strong> {current_user.role.title()}<br>
        <strong>Member Since:</strong> {current_user.created_at[:10]}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Change password
    st.subheader("Change Password")

    with st.form("change_password_form"):
        old_password = st.text_input(
            "Current Password",
            type="password",
            key="old_pass"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_pass",
            help="Must be 8+ characters with uppercase, lowercase, number, and special character"
        )

        confirm_new = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_new"
        )

        submit = st.form_submit_button("Update Password", type="primary")

        if submit:
            if not all([old_password, new_password, confirm_new]):
                st.error("Please fill in all fields")
            elif new_password != confirm_new:
                st.error("New passwords do not match")
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
            <h2>👤 {current_user.full_name}</h2>
            <div style="
                color: var(--accent-gold-light);
                font-size: 0.875rem;
                margin-top: 0.5rem;
            ">
            {current_user.email}
            </div>
            <div style="
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.75rem;
                margin-top: 0.25rem;
            ">
            Role: {current_user.role.title()}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            logout(st.session_state)
            st.rerun()

        st.divider()

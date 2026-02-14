"""
Modern UI styling for Corporate Law Document Generator.

Professional legal/corporate theme with:
- Clean typography
- Dark navy and gold color scheme
- Card-based layouts
- Smooth transitions
- Proper spacing and hierarchy
"""


def get_custom_css() -> str:
    """Return custom CSS for the application."""
    return """
    <style>
    /* ====================================================================
       Global Theme & Typography
       ==================================================================== */

    :root {
        --primary-navy: #1a2332;
        --secondary-navy: #2d3e50;
        --accent-gold: #d4af37;
        --accent-gold-light: #e8d4a0;
        --text-primary: #1a2332;
        --text-secondary: #5a6c7d;
        --text-light: #8b95a1;
        --bg-white: #ffffff;
        --bg-light: #f8f9fa;
        --bg-card: #ffffff;
        --border-color: #e1e4e8;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
        --shadow-lg: 0 10px 20px rgba(0,0,0,0.1);
        --success: #28a745;
        --warning: #ffc107;
        --error: #dc3545;
        --info: #17a2b8;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        color: var(--text-primary);
    }

    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: var(--primary-navy);
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    h2 {
        font-size: 1.75rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    h3 {
        font-size: 1.25rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    p {
        line-height: 1.6;
        color: var(--text-secondary);
    }

    /* ====================================================================
       Header & Branding
       ==================================================================== */

    .app-header {
        background: linear-gradient(135deg, var(--primary-navy) 0%, var(--secondary-navy) 100%);
        color: white;
        padding: 2rem 2rem 1.5rem 2rem;
        margin: -2rem -2rem 2rem -2rem;
        border-radius: 0 0 16px 16px;
        box-shadow: var(--shadow-lg);
    }

    .app-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }

    .app-header .subtitle {
        color: var(--accent-gold-light);
        font-size: 0.95rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    .app-header .disclaimer {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.75rem;
        margin-top: 1rem;
        font-style: italic;
    }

    /* User info badge */
    .user-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.15);
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.875rem;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }

    .user-badge .role-tag {
        background: var(--accent-gold);
        color: var(--primary-navy);
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ====================================================================
       Cards & Containers
       ==================================================================== */

    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }

    .card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .card-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary-navy);
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--accent-gold);
    }

    .info-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 4px solid var(--info);
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .warning-card {
        background: #fff9e6;
        border-left: 4px solid var(--warning);
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .success-card {
        background: #e8f5e9;
        border-left: 4px solid var(--success);
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .error-card {
        background: #ffebee;
        border-left: 4px solid var(--error);
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    /* ====================================================================
       Buttons
       ==================================================================== */

    .stButton > button {
        background: linear-gradient(135deg, var(--primary-navy) 0%, var(--secondary-navy) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.5rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        background: linear-gradient(135deg, var(--secondary-navy) 0%, var(--primary-navy) 100%);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-gold) 0%, #c9a84a 100%);
        color: var(--primary-navy);
        font-weight: 600;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #c9a84a 0%, var(--accent-gold) 100%);
    }

    .stButton > button[kind="secondary"] {
        background: white;
        color: var(--primary-navy);
        border: 2px solid var(--border-color);
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: var(--accent-gold);
        background: var(--bg-light);
    }

    /* ====================================================================
       Forms & Inputs
       ==================================================================== */

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-radius: 8px;
        border: 2px solid var(--border-color);
        padding: 0.75rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: var(--accent-gold);
        box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
        outline: none;
    }

    .stTextArea > div > div > textarea {
        min-height: 120px;
        font-family: inherit;
    }

    label {
        font-weight: 500;
        color: var(--text-primary);
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    /* File uploader */
    .stFileUploader > div {
        border: 2px dashed var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        background: var(--bg-light);
    }

    .stFileUploader > div:hover {
        border-color: var(--accent-gold);
        background: white;
    }

    /* ====================================================================
       Tabs
       ==================================================================== */

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--bg-light);
        padding: 0.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: var(--text-secondary);
        background: transparent;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: white;
        color: var(--primary-navy);
    }

    .stTabs [aria-selected="true"] {
        background: white;
        color: var(--primary-navy);
        box-shadow: var(--shadow-sm);
    }

    /* ====================================================================
       Chat Interface
       ==================================================================== */

    .stChatMessage {
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        box-shadow: var(--shadow-sm);
    }

    .stChatMessage[data-testid="user"] {
        background: linear-gradient(135deg, var(--primary-navy) 0%, var(--secondary-navy) 100%);
        color: white;
        margin-left: 2rem;
    }

    .stChatMessage[data-testid="assistant"] {
        background: white;
        border: 1px solid var(--border-color);
        margin-right: 2rem;
    }

    .stChatInputContainer {
        border-top: 1px solid var(--border-color);
        padding-top: 1rem;
        margin-top: 1rem;
    }

    /* ====================================================================
       Sidebar
       ==================================================================== */

    section[data-testid="stSidebar"] {
        background: var(--bg-light);
        border-right: 1px solid var(--border-color);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }

    .sidebar-header {
        background: linear-gradient(135deg, var(--primary-navy) 0%, var(--secondary-navy) 100%);
        color: white;
        padding: 1.5rem;
        margin: -2rem -1rem 1.5rem -1rem;
        border-radius: 0 0 12px 12px;
    }

    .sidebar-header h2 {
        color: white;
        font-size: 1.25rem;
        margin: 0;
    }

    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem 0;
    }

    .status-success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .status-warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }

    .status-error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .status-info {
        background: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }

    /* Connection indicators */
    .connection-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }

    .connection-success {
        background: var(--success);
        box-shadow: 0 0 8px rgba(40, 167, 69, 0.5);
    }

    .connection-warning {
        background: var(--warning);
        box-shadow: 0 0 8px rgba(255, 193, 7, 0.5);
    }

    .connection-error {
        background: var(--error);
        box-shadow: 0 0 8px rgba(220, 53, 69, 0.5);
    }

    /* ====================================================================
       Metrics & Stats
       ==================================================================== */

    [data-testid="stMetric"] {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stMetric"] label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-navy);
    }

    /* ====================================================================
       Document Cards
       ==================================================================== */

    .doc-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .doc-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateX(4px);
        border-color: var(--accent-gold);
    }

    .doc-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.75rem;
    }

    .doc-card-title {
        font-weight: 600;
        color: var(--primary-navy);
        font-size: 1rem;
    }

    .doc-card-meta {
        font-size: 0.8rem;
        color: var(--text-light);
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
    }

    .doc-type-tag {
        display: inline-block;
        background: var(--accent-gold);
        color: var(--primary-navy);
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ====================================================================
       Loading & Progress
       ==================================================================== */

    .stProgress > div > div {
        background: var(--accent-gold);
        border-radius: 10px;
    }

    .stSpinner > div {
        border-top-color: var(--accent-gold);
    }

    /* ====================================================================
       Alerts & Messages
       ==================================================================== */

    .stAlert {
        border-radius: 10px;
        padding: 1rem 1.25rem;
        border-width: 1px;
        margin: 1rem 0;
    }

    .stSuccess {
        background: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }

    .stWarning {
        background: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
    }

    .stError {
        background: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }

    .stInfo {
        background: #d1ecf1;
        border-color: #bee5eb;
        color: #0c5460;
    }

    /* ====================================================================
       Authentication Pages
       ==================================================================== */

    .auth-container {
        max-width: 450px;
        margin: 4rem auto;
        background: white;
        padding: 3rem;
        border-radius: 16px;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
    }

    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .auth-header h1 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .auth-header .logo {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .auth-divider {
        text-align: center;
        margin: 1.5rem 0;
        position: relative;
    }

    .auth-divider::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: var(--border-color);
    }

    .auth-divider span {
        background: white;
        padding: 0 1rem;
        position: relative;
        color: var(--text-light);
        font-size: 0.875rem;
    }

    /* ====================================================================
       Footer
       ==================================================================== */

    .app-footer {
        margin-top: 4rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-color);
        text-align: center;
        color: var(--text-light);
        font-size: 0.875rem;
    }

    .app-footer .version {
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* ====================================================================
       Responsive Design
       ==================================================================== */

    @media (max-width: 768px) {
        .app-header {
            padding: 1.5rem 1rem;
        }

        .app-header h1 {
            font-size: 1.5rem;
        }

        .stChatMessage[data-testid="user"],
        .stChatMessage[data-testid="assistant"] {
            margin-left: 0;
            margin-right: 0;
        }

        .auth-container {
            margin: 2rem 1rem;
            padding: 2rem 1.5rem;
        }
    }

    /* ====================================================================
       Utility Classes
       ==================================================================== */

    .text-center {
        text-align: center;
    }

    .text-muted {
        color: var(--text-light);
    }

    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mt-3 { margin-top: 1.5rem; }
    .mt-4 { margin-top: 2rem; }

    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .mb-3 { margin-bottom: 1.5rem; }
    .mb-4 { margin-bottom: 2rem; }

    .p-1 { padding: 0.5rem; }
    .p-2 { padding: 1rem; }
    .p-3 { padding: 1.5rem; }
    .p-4 { padding: 2rem; }

    .hidden {
        display: none;
    }

    /* ====================================================================
       Animations
       ==================================================================== */

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    .fade-in {
        animation: fadeIn 0.3s ease;
    }

    .slide-in {
        animation: slideIn 0.4s ease;
    }

    </style>
    """


def render_header(title: str, subtitle: str = "", user_info: dict = None):
    """Render the application header with branding."""
    import streamlit as st

    user_badge = ""
    if user_info:
        role_tag = f'<span class="role-tag">{user_info.get("role", "user")}</span>'
        user_badge = f'''
        <div class="user-badge">
            <span>{user_info.get("full_name", "User")}</span>
            {role_tag}
        </div>
        '''

    disclaimer = """
    <div class="disclaimer">
    This tool generates legal document drafts for attorney review.
    It does not provide legal advice.
    </div>
    """

    st.markdown(f"""
    <div class="app-header">
        <h1>{title}</h1>
        <div class="subtitle">{subtitle}</div>
        {user_badge}
        {disclaimer}
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the application footer."""
    import streamlit as st

    st.markdown("""
    <div class="app-footer">
        <div class="version">Corporate Law Document Generator v2.0</div>
        <div class="mt-1">Powered by AI • Built with Streamlit</div>
        <div class="mt-1 text-muted">
            For attorney use only • All generated documents require legal review
        </div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(label: str, status: str = "success") -> str:
    """
    Generate a status badge HTML.
    status: 'success', 'warning', 'error', 'info'
    """
    return f'<span class="status-badge status-{status}">{label}</span>'


def connection_indicator(connected: bool) -> str:
    """Generate a connection indicator dot."""
    status = "success" if connected else "error"
    return f'<span class="connection-indicator connection-{status}"></span>'


def card(content: str, header: str = None) -> str:
    """Generate a card layout."""
    header_html = f'<div class="card-header">{header}</div>' if header else ""
    return f"""
    <div class="card fade-in">
        {header_html}
        {content}
    </div>
    """

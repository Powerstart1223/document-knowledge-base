"""
Minimal UI styling for Corporate Law Document Generator.

Visual direction: lightweight, editorial, and restrained.
"""


def get_custom_css() -> str:
    """Return custom CSS for the application."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink-900: #111111;
        --ink-700: #2b2b2b;
        --ink-500: #6b6b6b;
        --ink-300: #cfcfcf;
        --paper-100: #ffffff;
        --paper-200: #f6f6f4;
        --paper-300: #efefed;
        --line: #dfdfdc;
        --accent: #1f1f1f;
        --success: #1f7a3f;
        --warning: #8a6700;
        --error: #9f2121;
        --info: #115f8a;
        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --shadow-soft: 0 6px 26px rgba(17, 17, 17, 0.07);
        --shadow-tight: 0 2px 8px rgba(17, 17, 17, 0.08);
    }

    html, body, [class*="css"] {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--ink-900);
        background: var(--paper-100);
    }

    .main .block-container {
        max-width: 1220px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--ink-900);
        letter-spacing: -0.02em;
        font-weight: 700;
    }

    h1 {
        font-size: clamp(2rem, 3vw, 2.8rem);
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }

    h2 {
        font-size: clamp(1.45rem, 2.2vw, 1.85rem);
        line-height: 1.2;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    h3 {
        font-size: 1.18rem;
        margin-top: 1.2rem;
        margin-bottom: 0.65rem;
    }

    p, li {
        color: var(--ink-700);
        line-height: 1.62;
    }

    .app-header {
        background:
            radial-gradient(80rem 36rem at 12% -12%, rgba(0,0,0,0.06), transparent 62%),
            linear-gradient(180deg, #ffffff 0%, #fbfbfa 100%);
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin: 0 0 1.5rem 0;
        box-shadow: var(--shadow-soft);
    }

    .app-header h1 {
        margin: 0;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.01em;
    }

    .app-header .subtitle {
        color: var(--ink-500);
        margin-top: 0.5rem;
        font-size: 0.96rem;
    }

    .app-header .disclaimer {
        margin-top: 0.95rem;
        color: var(--ink-500);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }

    .user-badge {
        display: none;
    }

    .user-badge .role-tag {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        border-radius: 999px;
        background: var(--paper-200);
        border: 1px solid var(--line);
        color: var(--ink-700);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .card {
        background: var(--paper-100);
        border: 1px solid var(--line);
        border-radius: var(--radius-md);
        padding: 1.35rem 1.45rem;
        margin: 0.9rem 0;
        box-shadow: var(--shadow-tight);
    }

    .card:hover {
        border-color: #c9c9c4;
    }

    .card-header {
        margin: 0 0 0.7rem 0;
        padding: 0 0 0.55rem 0;
        border-bottom: 1px solid var(--line);
        color: var(--ink-900);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .info-card,
    .warning-card,
    .success-card,
    .error-card {
        border-radius: var(--radius-sm);
        border: 1px solid var(--line);
        padding: 0.9rem 1rem;
        margin: 0.85rem 0;
    }

    .info-card {
        background: #f3f8fb;
        border-left: 4px solid var(--info);
    }

    .warning-card {
        background: #fff9ea;
        border-left: 4px solid var(--warning);
    }

    .success-card {
        background: #edf8f0;
        border-left: 4px solid var(--success);
    }

    .error-card {
        background: #fff1f1;
        border-left: 4px solid var(--error);
    }

    .stButton > button {
        border-radius: 999px;
        border: 1px solid #1c1c1c;
        background: #1c1c1c;
        color: #ffffff;
        font-weight: 700;
        letter-spacing: 0.02em;
        padding: 0.62rem 1.25rem;
        min-height: 2.65rem;
        transition: transform 120ms ease, background 140ms ease, box-shadow 140ms ease;
        box-shadow: 0 1px 0 rgba(0,0,0,0.12);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        background: #000000;
        box-shadow: 0 8px 18px rgba(0,0,0,0.16);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    .stButton > button[kind="secondary"] {
        background: #ffffff;
        color: #111111;
        border-color: var(--line);
    }

    .stButton > button[kind="secondary"]:hover {
        background: var(--paper-200);
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input,
    [data-baseweb="select"] > div {
        border-radius: 10px;
        border: 1px solid var(--line);
        background: #ffffff;
        color: var(--ink-900);
        font-size: 0.95rem;
        transition: border-color 150ms ease, box-shadow 150ms ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stDateInput > div > div > input:focus {
        border-color: #8d8d8a;
        box-shadow: 0 0 0 3px rgba(17,17,17,0.06);
        outline: none;
    }

    label {
        color: var(--ink-700);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 700;
    }

    .stFileUploader > div {
        border: 1px dashed #bdbdb8;
        border-radius: var(--radius-md);
        padding: 1.5rem;
        background: repeating-linear-gradient(
            -45deg,
            #ffffff,
            #ffffff 8px,
            #fafaf8 8px,
            #fafaf8 16px
        );
    }

    .stFileUploader > div:hover {
        border-color: #8f8f89;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        border-bottom: 1px solid var(--line);
        padding-bottom: 0.35rem;
        margin-bottom: 0.8rem;
        overflow-x: auto;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        border: 1px solid transparent;
        background: transparent;
        color: var(--ink-500);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-size: 0.72rem;
        padding: 0.45rem 0.78rem;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        border-color: var(--line);
        color: var(--ink-900);
        background: #ffffff;
    }

    .stChatMessage {
        border-radius: 12px;
        border: 1px solid var(--line);
        box-shadow: none;
    }

    .stChatMessage[data-testid="user"] {
        background: #141414;
        color: #ffffff;
        margin-left: 1.5rem;
    }

    .stChatMessage[data-testid="assistant"] {
        background: #ffffff;
        color: var(--ink-900);
        margin-right: 1.5rem;
    }

    .stChatInputContainer {
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fcfcfb 0%, #f5f5f2 100%);
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.35rem;
    }

    .sidebar-header {
        background: transparent;
        border-bottom: 1px solid var(--line);
        padding: 0 0 0.75rem 0;
        margin: 0 0 0.85rem 0;
    }

    .sidebar-header h2 {
        margin: 0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--ink-700);
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.4rem 0.62rem;
        border-radius: 999px;
        border: 1px solid var(--line);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        background: #ffffff;
    }

    .status-success { color: #14512c; }
    .status-warning { color: #6c4f00; }
    .status-error { color: #8a1e1e; }
    .status-info { color: #0f4f73; }

    .connection-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .connection-success { background: #1f7a3f; }
    .connection-warning { background: #8a6700; }
    .connection-error { background: #9f2121; }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: var(--radius-sm);
        box-shadow: none;
    }

    [data-testid="stMetric"] label {
        letter-spacing: 0.08em;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--ink-900);
        font-size: 1.9rem;
        font-weight: 800;
    }

    .doc-card,
    .doc-type-grid-card,
    .landing-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: var(--radius-md);
    }

    .doc-card {
        padding: 1rem 1.1rem;
        margin: 0.6rem 0;
    }

    .doc-card:hover {
        border-color: #bdbdb8;
        box-shadow: var(--shadow-tight);
    }

    .doc-card-title {
        color: var(--ink-900);
        font-weight: 700;
    }

    .doc-card-meta {
        color: var(--ink-500);
        font-size: 0.78rem;
    }

    .doc-type-tag {
        border-radius: 999px;
        border: 1px solid var(--line);
        background: var(--paper-200);
        color: var(--ink-700);
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.22rem 0.58rem;
    }

    .doc-type-grid-card {
        padding: 1.2rem;
        text-align: center;
        box-shadow: none;
    }

    .doc-type-grid-card:hover {
        border-color: #bdbdb8;
        transform: translateY(-2px);
    }

    .doc-type-icon {
        font-size: 2.6rem;
        margin-bottom: 0.7rem;
        filter: grayscale(100%);
    }

    .landing-card {
        padding: 1.7rem 1.3rem;
        text-align: center;
        box-shadow: var(--shadow-tight);
    }

    .landing-card:hover {
        border-color: #b9b9b4;
        transform: translateY(-3px);
    }

    .landing-card-icon {
        font-size: 2.8rem;
        margin-bottom: 0.7rem;
    }

    .stProgress > div > div {
        background: #1f1f1f;
        border-radius: 999px;
    }

    .stSpinner > div {
        border-top-color: #222222;
    }

    .stAlert {
        border-radius: 10px;
        border-width: 1px;
    }

    .auth-container {
        max-width: 460px;
        margin: 2.6rem auto;
        background: #ffffff;
        padding: 2rem;
        border-radius: var(--radius-md);
        border: 1px solid var(--line);
        box-shadow: var(--shadow-soft);
    }

    .auth-header {
        text-align: center;
        margin-bottom: 1.4rem;
    }

    .auth-header h1 {
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 1.55rem;
    }

    .auth-divider {
        text-align: center;
        margin: 1.15rem 0;
        position: relative;
    }

    .auth-divider::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: var(--line);
    }

    .auth-divider span {
        background: #ffffff;
        padding: 0 0.7rem;
        position: relative;
        color: var(--ink-500);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .app-footer {
        margin-top: 3rem;
        border-top: 1px solid var(--line);
        padding-top: 1.2rem;
        text-align: center;
        color: var(--ink-500);
        font-size: 0.78rem;
    }

    .app-footer .version {
        color: var(--ink-700);
        font-weight: 700;
    }

    @media (max-width: 920px) {
        .main .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }

        .app-header {
            padding: 1.25rem;
            border-radius: 14px;
        }

        .stChatMessage[data-testid="user"],
        .stChatMessage[data-testid="assistant"] {
            margin-left: 0;
            margin-right: 0;
        }
    }

    @media (max-width: 640px) {
        h1 { font-size: 1.6rem; }
        h2 { font-size: 1.25rem; }
        .auth-container {
            margin: 0.8rem 0.25rem;
            padding: 1.3rem 1rem;
        }

        .stButton > button {
            width: 100%;
        }
    }

    .text-center { text-align: center; }
    .text-muted { color: var(--ink-500); }
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
    .hidden { display: none; }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideIn {
        from { transform: translateX(-10px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    .fade-in { animation: fadeIn 0.22s ease; }
    .slide-in { animation: slideIn 0.24s ease; }
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
        <div style="color: var(--ink-700); font-weight: 700;">Corporate Law Document Generator</div>
        <div class="mt-1">Powered by AI | Built with Streamlit</div>
        <div class="mt-1 text-muted">
            For attorney use only | All generated documents require legal review
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

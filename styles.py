"""
High-contrast streamlined UI styling for Corporate Law Document Generator.
"""


def get_custom_css() -> str:
    """Return custom CSS for the application."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #111111;
        --ink-soft: #2d2d2d;
        --ink-muted: #4f4f4f;
        --paper: #ffffff;
        --paper-soft: #f7f8f7;
        --line: #d7dbd7;
        --line-strong: #b9beb9;
        --focus: #0f1720;
        --success: #1d7a43;
        --warning: #8c6600;
        --error: #9a2525;
        --info: #125b89;

        --text-primary: #111111;
        --text-secondary: #4f4f4f;
        --text-light: #707070;
        --primary-navy: #111111;
        --accent-gold: #8c6600;
        --bg-light: #f7f8f7;
        --border-color: #d7dbd7;

        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --shadow-soft: 0 8px 30px rgba(12, 18, 12, 0.08);
    }

    section[data-testid="stSidebar"] { display: none !important; }

    html, body, [class*="css"] {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--ink);
        background: var(--paper);
    }

    .stApp {
        background: #ffffff;
    }

    .main .block-container {
        max-width: 1220px;
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        position: relative;
        z-index: 1;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--ink);
        letter-spacing: -0.02em;
        font-weight: 750;
    }

    h1 { font-size: clamp(1.8rem, 2.6vw, 2.35rem); margin-bottom: 0.35rem; }
    h2 { font-size: clamp(1.35rem, 2vw, 1.7rem); margin: 1rem 0 0.5rem 0; }
    h3 { font-size: 1.08rem; margin: 0.8rem 0 0.45rem 0; }
    p, li { color: var(--ink-soft); line-height: 1.58; }

    .workspace-hero {
        background: linear-gradient(180deg, #ffffff 0%, #f9fbfa 100%);
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
        box-shadow: var(--shadow-soft);
    }

    .workspace-hero h2 {
        margin: 0;
        font-size: 1.18rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .workspace-hero p {
        margin: 0.35rem 0 0;
        font-size: 0.9rem;
        color: var(--ink-muted);
    }

    .workspace-tile {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: var(--radius-md);
        padding: 0.9rem;
        min-height: 120px;
        margin-bottom: 0.45rem;
        transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
    }

    .workspace-tile:hover {
        transform: translateY(-2px);
        border-color: var(--line-strong);
        box-shadow: 0 8px 22px rgba(12, 18, 12, 0.08);
    }

    .workspace-tile-title {
        font-weight: 750;
        font-size: 0.98rem;
        color: var(--ink);
        margin-bottom: 0.3rem;
    }

    .workspace-tile-copy {
        color: var(--ink-muted);
        font-size: 0.86rem;
        line-height: 1.5;
    }

    .card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin: 0.7rem 0;
    }

    .card-header {
        margin-bottom: 0.6rem;
        padding-bottom: 0.45rem;
        border-bottom: 1px solid var(--line);
        color: var(--ink);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-size: 0.74rem;
        font-weight: 750;
    }

    .info-card, .warning-card, .success-card, .error-card {
        border-radius: var(--radius-sm);
        border: 1px solid var(--line);
        padding: 0.78rem 0.9rem;
        margin: 0.7rem 0;
        color: var(--ink);
    }

    .info-card { background: #f4f9fc; border-left: 4px solid var(--info); }
    .warning-card { background: #fff8e9; border-left: 4px solid var(--warning); }
    .success-card { background: #edf8f1; border-left: 4px solid var(--success); }
    .error-card { background: #fff1f1; border-left: 4px solid var(--error); }

    /* High-contrast buttons across Streamlit button variants */
    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        border-radius: 999px !important;
        border: 1px solid #171717 !important;
        background: #171717 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.03em !important;
        min-height: 2.12rem !important;
        padding: 0.34rem 0.82rem !important;
        text-shadow: none !important;
        opacity: 1 !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover {
        background: #000000 !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }

    .stButton > button:focus-visible,
    .stFormSubmitButton > button:focus-visible,
    .stDownloadButton > button:focus-visible,
    button[kind="primary"]:focus-visible,
    button[kind="secondary"]:focus-visible {
        outline: 2px solid #111111 !important;
        outline-offset: 2px;
        box-shadow: 0 0 0 2px rgba(17, 17, 17, 0.12) !important;
    }

    .stButton > button[kind="secondary"],
    button[kind="secondary"] {
        background: #ffffff !important;
        color: #121212 !important;
        border: 1px solid #111111 !important;
    }

    .stButton > button[kind="secondary"]:hover,
    button[kind="secondary"]:hover {
        background: #f1f4f1 !important;
        color: #111111 !important;
    }

    .stButton > button:disabled,
    .stFormSubmitButton > button:disabled,
    .stDownloadButton > button:disabled {
        background: #c9ceca !important;
        color: #2a2a2a !important;
        border-color: #b7bcb8 !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input,
    [data-baseweb="select"] > div {
        border-radius: 10px;
        border: 1px solid var(--line-strong);
        background: #ffffff;
        color: var(--ink);
        font-size: 0.92rem;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stDateInput > div > div > input:focus {
        border-color: var(--focus);
        box-shadow: 0 0 0 3px rgba(15, 23, 32, 0.08);
        outline: none;
    }

    label {
        color: var(--ink-soft);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-weight: 750;
    }

    .stFileUploader > div {
        border: 1px dashed var(--line-strong);
        border-radius: var(--radius-md);
        background: #fcfdfc;
        padding: 1.2rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        border-bottom: 1px solid var(--line);
        padding-bottom: 0.3rem;
        margin-bottom: 0.7rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        border: 1px solid transparent;
        color: var(--ink-muted);
        background: transparent;
        font-size: 0.7rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 750;
        padding: 0.35rem 0.72rem;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        border-color: var(--line-strong);
        color: var(--ink);
        background: #ffffff;
    }

    .stChatMessage {
        border: 1px solid var(--line);
        border-radius: 11px;
    }

    .stChatMessage[data-testid="user"] {
        background: #151515;
        color: #ffffff;
    }

    .stChatMessage[data-testid="assistant"] {
        background: #ffffff;
        color: var(--ink);
    }

    [data-testid="stMetric"] {
        border: 1px solid var(--line);
        border-radius: var(--radius-sm);
        background: #ffffff;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--ink);
        font-weight: 800;
    }

    .doc-card, .doc-type-grid-card, .landing-card {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: var(--radius-md);
    }

    .doc-type-tag {
        border: 1px solid var(--line-strong);
        border-radius: 999px;
        padding: 0.2rem 0.56rem;
        font-size: 0.65rem;
        font-weight: 750;
        color: var(--ink-soft);
        background: #f2f4f2;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.34rem 0.56rem;
        border-radius: 999px;
        border: 1px solid var(--line-strong);
        font-size: 0.68rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        background: #ffffff;
    }

    .status-success { color: #155b30; }
    .status-warning { color: #6f5200; }
    .status-error { color: #822222; }
    .status-info { color: #0f4f75; }

    .connection-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .connection-success { background: var(--success); }
    .connection-warning { background: var(--warning); }
    .connection-error { background: var(--error); }

    .stProgress > div > div {
        background: #1a1a1a;
        border-radius: 999px;
    }

    .stAlert { border-radius: 10px; }

    .app-footer {
        margin-top: 2.4rem;
        border-top: 1px solid var(--line);
        padding-top: 0.95rem;
        text-align: center;
        color: var(--ink-muted);
        font-size: 0.74rem;
    }

    .app-footer .version {
        color: var(--ink-soft);
        font-weight: 700;
    }

    .text-center { text-align: center; }
    .text-muted { color: var(--ink-muted); }
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

    @media (max-width: 920px) {
        .main .block-container { padding-top: 1.15rem; }
        .workspace-tile { min-height: auto; }
    }

    @media (max-width: 640px) {
        h1 { font-size: 1.55rem; }
        h2 { font-size: 1.2rem; }
        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button { width: 100%; }
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
        <div style="color: var(--ink-soft); font-weight: 700;">Corporate Law Document Generator</div>
        <div class="mt-1">Powered by AI | Built with Streamlit</div>
        <div class="mt-1 text-muted">
            For attorney use only | All generated documents require legal review
        </div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(label: str, status: str = "success") -> str:
    """Generate a status badge HTML."""
    return f'<span class="status-badge status-{status}">{label}</span>'


def connection_indicator(connected: bool) -> str:
    """Generate a connection indicator dot."""
    status = "success" if connected else "error"
    return f'<span class="connection-indicator connection-{status}"></span>'


def card(content: str, header: str = None) -> str:
    """Generate a card layout."""
    header_html = f'<div class="card-header">{header}</div>' if header else ""
    return f"""
    <div class="card">
        {header_html}
        {content}
    </div>
    """

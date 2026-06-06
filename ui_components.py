import streamlit as st


def apply_premium_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

        :root {
            --bg-dark: #050508;
            --card-bg: #0f0f14;
            --card-bg-hover: #16161e;
            --border-color: #1e1e2e;
            --border-hover: #3b3b55;
            --text-main: #e2e8f0;
            --text-muted: #64748b;
            --accent: #7c3aed;
            --accent-glow: rgba(124, 58, 237, 0.25);
            --accent-light: #a78bfa;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }

        /* ───── Base ───── */
        .stApp {
            background: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Inter', 'Outfit', sans-serif;
        }

        /* ───── Sidebar ───── */
        section[data-testid="stSidebar"] {
            background: #08080d !important;
            border-right: 1px solid var(--border-color);
        }

        /* ───── Premium Header ───── */
        .main-title {
            font-family: 'Outfit', sans-serif;
            font-size: 3.5rem;
            font-weight: 800;
            letter-spacing: -2px;
            background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-top: -10px;
            margin-bottom: 5px;
        }

        /* ───── Metric Cards ───── */
        .metric-container {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .metric-container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            opacity: 0;
            transition: opacity 0.25s ease;
        }
        .metric-container:hover {
            border-color: var(--border-hover);
            box-shadow: 0 0 24px var(--accent-glow);
            transform: translateY(-2px);
        }
        .metric-container:hover::before { opacity: 1; }

        [data-testid="stMetricValue"] {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700;
            font-size: 1.8rem !important;
            color: #ffffff !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--text-muted) !important;
            font-size: 0.8rem !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* ───── Chat Messages ───── */
        [data-testid="stChatMessage"] {
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 14px !important;
            padding: 1rem 1.4rem !important;
            margin-bottom: 0.8rem !important;
            transition: border-color 0.2s ease;
        }
        [data-testid="stChatMessage"]:hover {
            border-color: var(--border-hover) !important;
        }

        /* User message accent */
        [data-testid="stChatMessage"][data-role="user"] {
            border-left: 3px solid var(--accent) !important;
        }
        /* Assistant message accent */
        [data-testid="stChatMessage"][data-role="assistant"] {
            border-left: 3px solid var(--success) !important;
        }

        /* ───── Chat Input ───── */
        [data-testid="stChatInput"] {
            border-radius: 12px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--card-bg) !important;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px var(--accent-glow) !important;
        }

        /* ───── Buttons ───── */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent) 0%, #6d28d9 100%);
            color: #ffffff !important;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            transition: all 0.2s ease;
            letter-spacing: 0.3px;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 20px var(--accent-glow);
            filter: brightness(1.1);
        }
        .stButton > button:active {
            transform: translateY(0);
        }

        /* ───── Select / Input boxes ───── */
        .stSelectbox > div, .stTextInput > div > div {
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 10px !important;
            color: var(--text-main) !important;
        }

        /* ───── Data Table ───── */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        /* ───── Expander ───── */
        [data-testid="stExpander"] {
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
        }

        /* ───── Scrollbar ───── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb {
            background: var(--border-hover);
            border-radius: 99px;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

        /* ───── Animations ───── */
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(24px); }
            to   { opacity: 1; transform: translateY(0);    }
        }
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 0px var(--accent-glow); }
            50%       { box-shadow: 0 0 20px var(--accent-glow); }
        }
        .animate-up { animation: slideUp 0.7s cubic-bezier(0.4, 0, 0.2, 1); }

        /* ───── Success / Warning / Info boxes ───── */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
            border: none !important;
        }

        /* ───── Toast ───── */
        [data-testid="stToast"] {
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 10px !important;
        }

        /* ───── Spinner ───── */
        [data-testid="stSpinner"] > div {
            border-top-color: var(--accent) !important;
        }

        /* ───── Hide Streamlit Branding ───── */
        #MainMenu { visibility: hidden; }
        footer     { visibility: hidden; }
        header     { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)


def init_session():
    defaults = {
        "messages": [],
        "df": None,
        "file_path": None,
        "profiling": None,
        "auto_insights": None,
        "is_cleaned": False,
        "selected_model": "gemini-2.0-flash-lite",
        "session_id": None,   # Set properly in app.py with uuid
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

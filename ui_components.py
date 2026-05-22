import streamlit as st

def apply_premium_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --bg-dark: #000000;
            --card-bg: #111111;
            --border-color: #222222;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        .stApp {
            background: #000000;
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
        }
        
        /* Sidebar Overhaul */
        section[data-testid="stSidebar"] {
            background: #000000 !important;
            border-right: 1px solid var(--border-color);
        }

        /* Premium Header */
        .main-title {
            font-family: 'Outfit', sans-serif;
            font-size: 3.5rem;
            font-weight: 600;
            letter-spacing: -1px;
            color: #ffffff;
            margin-top: -20px;
            margin-bottom: 5px;
        }

        /* Dashboard Metric Cards */
        [data-testid="stMetricValue"] {
            font-family: 'Inter', sans-serif !important;
            font-weight: 500;
            color: #ffffff !important;
        }
        
        .metric-container {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease-in-out;
        }
        
        .metric-container:hover {
            border-color: #444444;
        }

        /* Chat Bubbles Upgrade */
        .chat-bubble {
            padding: 1.2rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        .user-bubble {
            background: #111111;
            border: 1px solid var(--border-color);
        }
        
        .bot-bubble {
            background: transparent;
            border: 1px solid transparent;
            border-left: 3px solid #444444;
            border-radius: 0;
            padding-left: 1rem;
        }

        /* Custom Input Box */
        [data-testid="stChatInput"] {
            border-radius: 8px !important;
            border: 1px solid var(--border-color) !important;
            background: #111111 !important;
        }

        /* Buttons */
        .stButton>button {
            width: 100%;
            background: #ffffff;
            color: #000000 !important;
            font-weight: 500;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            transition: background 0.2s;
        }
        .stButton>button:hover {
            background: #e5e5e5;
        }

        /* Expanding code/tables */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        
        /* Hide specific Streamlit defaults */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Animations */
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-up { animation: slideUp 0.8s ease-out; }
        </style>
    """, unsafe_allow_html=True)

def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "df" not in st.session_state:
        st.session_state.df = None
    if "file_path" not in st.session_state:
        st.session_state.file_path = None
    if "profiling" not in st.session_state:
        st.session_state.profiling = None
    if "auto_insights" not in st.session_state:
        st.session_state.auto_insights = None
    if "is_cleaned" not in st.session_state:
        st.session_state.is_cleaned = False
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemini-flash-lite-latest"

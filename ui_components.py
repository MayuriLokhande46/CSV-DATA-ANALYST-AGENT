import streamlit as st

def apply_premium_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --bg-dark: #05070a;
            --card-bg: rgba(17, 25, 40, 0.75);
            --accent-blue: #00f2fe;
            --accent-purple: #764ba2;
            --text-main: #e2e8f0;
        }

        .stApp {
            background: radial-gradient(circle at 0% 0%, #0d1117 0%, #05070a 100%);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
        }
        
        /* Sidebar Overhaul */
        section[data-testid="stSidebar"] {
            background: rgba(10, 15, 25, 0.8) !important;
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* Premium Header */
        .main-title {
            font-family: 'Outfit', sans-serif;
            font-size: 4.5rem;
            font-weight: 800;
            letter-spacing: -2px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: -20px;
            text-shadow: 0 10px 30px rgba(0, 242, 254, 0.2);
        }

        /* Dashboard Metric Cards */
        [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600;
            color: var(--accent-blue) !important;
        }
        
        .metric-container {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .metric-container:hover {
            transform: translateY(-8px);
            border-color: var(--accent-blue);
            box-shadow: 0 15px 35px rgba(0, 242, 254, 0.15);
        }

        /* Chat Bubbles Upgrade */
        .chat-bubble {
            padding: 1.5rem;
            border-radius: 24px;
            margin-bottom: 1.5rem;
            line-height: 1.6;
            font-size: 1rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .user-bubble {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom-right-radius: 4px;
        }
        
        .bot-bubble {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(0, 242, 254, 0.3);
            border-bottom-left-radius: 4px;
            backdrop-filter: blur(10px);
        }

        /* Custom Input Box */
        [data-testid="stChatInput"] {
            border-radius: 50px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: rgba(15, 23, 42, 0.8) !important;
        }

        /* Buttons */
        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            color: #05070a !important;
            font-weight: 700;
            border: none;
            border-radius: 12px;
            padding: 10px 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
        }

        /* Expanding code/tables */
        .stDataFrame {
            border-radius: 15px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
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

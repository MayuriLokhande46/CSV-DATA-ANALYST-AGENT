import streamlit as st
import pandas as pd
import os
import uuid

from ui_components import apply_premium_css, init_session
from data_utils import get_data_profiling, generate_auto_insights
import database
from dotenv import load_dotenv

# Load env variables
load_dotenv()
database.init_db()

# App Page Config
st.set_page_config(
    page_title="StatBot Pro - Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS styling
apply_premium_css()
init_session()

# Ensure session_id is always initialized
if not st.session_state.get("session_id"):
    st.session_state.session_id = str(uuid.uuid4())

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
    
    api_key = st.text_input("Google AI API Key", type="password", placeholder="Paste your API key here...", value=os.getenv("GOOGLE_API_KEY", ""))
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        
    st.markdown("---")
    st.info("👈 Use the menu above to switch between Home and the Chatbot.")

# --- MAIN UI ---
st.markdown("<div class='animate-up'>", unsafe_allow_html=True)
st.markdown("<h1 class='main-title'>StatBot Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.4rem; color: #94a3b8; font-weight: 300; margin-top: -15px;'>Your Private Autonomous Analyst</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# File Upload Section
st.markdown("### 📂 Upload Dataset")
uploaded_file = st.file_uploader("Drop your data here to begin analysis", type=["csv", "xlsx"])

if uploaded_file:
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Save to session
        st.session_state.df = df
        st.session_state.file_path = file_path
        st.session_state.profiling = get_data_profiling(df)
        
        with st.spinner("Generating initial insights..."):
            st.session_state.auto_insights = generate_auto_insights(file_path)
        
        # Reset chat if a new file is uploaded
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        
        welcome_msg = {
            "role": "assistant",
            "content": f"👋 **Welcome!** I've analyzed `{uploaded_file.name}`.\n\n{st.session_state.auto_insights['summary']}"
        }
        st.session_state.messages.append(welcome_msg)
        database.save_message(st.session_state.session_id, welcome_msg["role"], welcome_msg["content"])
        
        st.success("✅ Data successfully ingested!")
        st.info("Click the button below to start analyzing your data.")
            
    except Exception as e:
        st.error(f"Error reading file: {e}")

if st.session_state.df is not None:
    if st.button("🚀 Proceed to Chatbot", use_container_width=True):
        st.switch_page("pages/1_Chatbot.py")

# Empty State Visual
if st.session_state.df is None and not uploaded_file:
    st.markdown("""
    <div style='text-align: center; padding: 8rem 2rem; background: #111111; border-radius: 12px; border: 1px dashed #444444; margin-top: 2rem;'>
        <h2 style='color: #ffffff; font-weight: 500;'>Ready to get started?</h2>
        <p style='color: #9ca3af;'>Upload a CSV or Excel file above to begin autonomous exploration.</p>
    </div>
    """, unsafe_allow_html=True)
elif st.session_state.df is not None and not uploaded_file:
    st.success(f"Dataset already loaded: **{os.path.basename(st.session_state.file_path)}**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Return to Chatbot", use_container_width=True):
            st.switch_page("pages/1_Chatbot.py")
    with col2:
        if st.button("🗑️ Clear Current Data", use_container_width=True):
            st.session_state.df = None
            st.session_state.messages = []
            st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>StatBot Pro v3.0 | Powered by Gemini & LangChain</p>", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import os
import uuid
import streamlit.components.v1 as components

from sandbox_agent import get_sandbox_agent
from sandbox_executor import ExecutionSandbox
from dotenv import load_dotenv

# Modular Imports
from ui_components import apply_premium_css, init_session
from data_utils import smart_clean_dataframe, get_data_profiling, generate_auto_insights
from report_generator import generate_pdf_report
import database

# Load environment variables
load_dotenv()

# Init Database
database.init_db()

# App Page Config
st.set_page_config(
    page_title="StatBot Pro - Premium AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS styling
apply_premium_css()

# Session State Initialization
init_session()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    # Load history if a specific session_id is provided via query params (optional)
    # For now, starts a fresh session or relies on DB
    
# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
    
    api_key = st.text_input("Google AI API Key", type="password", placeholder="Paste your API key here...")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.markdown("---")
    st.markdown("### 🤖 Model Selection")
    model_map = {
        "⚡ Flash Lite (Ultra Fast)": "gemini-flash-lite-latest",
        "⚖️ Flash (Balanced)": "gemini-2.5-flash",
        "🧠 Pro (Expert Reasoning)": "gemini-2.5-pro"
    }
    choice = st.selectbox(
        "Choose Intelligence Level",
        options=list(model_map.keys()),
        index=0
    )
    st.session_state.selected_model = model_map[choice]
    
    st.markdown("---")
    
    # Sandbox Status
    sandbox = ExecutionSandbox()
    if sandbox.is_docker_available:
        st.success("✅ Docker Sandbox Active")
    else:
        st.warning("⚠️ Docker Not Found - Running in Local Mode")
        st.caption("Install Docker for enhanced safety.")
    
    st.markdown("---")
    st.markdown("### 📊 Dataset Overview")
    if st.session_state.df is not None:
        st.write(f"**Rows:** {st.session_state.df.shape[0]}")
        st.write(f"**Cols:** {st.session_state.df.shape[1]}")
        
        if st.button("Reset Session"):
            st.session_state.messages = []
            st.session_state.df = None
            st.session_state.file_path = None
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
        
        # Export Analysis to PDF
        if st.session_state.messages:
            st.markdown("### 📄 Export")
            pdf_buffer = generate_pdf_report(st.session_state.messages)
            
            st.download_button(
                label="Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name="statbot_analysis_report.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Upload a file to see details")

# --- MAIN UI ---
st.markdown("<div class='animate-up'>", unsafe_allow_html=True)
st.markdown("<h1 class='main-title'>StatBot Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.4rem; color: #94a3b8; font-weight: 300; margin-top: -15px;'>Your Private Autonomous Analyst</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# File Upload Section
if st.session_state.df is None:
    uploaded_file = st.file_uploader("Drop your data here", type=["csv", "xlsx"])
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
            
            st.session_state.df = df
            st.session_state.file_path = file_path
            st.session_state.profiling = get_data_profiling(df)
            
            with st.spinner("Generating initial insights..."):
                st.session_state.auto_insights = generate_auto_insights(file_path)
            
            welcome_msg = {
                "role": "assistant", 
                "content": f"👋 **Welcome!** I've analyzed your data.\\n\\n{st.session_state.auto_insights['summary']}"
            }
            st.session_state.messages.append(welcome_msg)
            database.save_message(st.session_state.session_id, welcome_msg["role"], welcome_msg["content"])
            
            st.success("Data successfully ingested!")
            st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# Analysis Interface
if st.session_state.df is not None:
    # Action Bar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🛠️ Data Tools")
        if not st.session_state.is_cleaned:
            if st.button("✨ Smart Clean Data", use_container_width=True):
                with st.spinner("Cleaning and optimizing dataset..."):
                    st.session_state.df = smart_clean_dataframe(st.session_state.df)
                    st.session_state.is_cleaned = True
                    if st.session_state.file_path.endswith(".csv"):
                        st.session_state.df.to_csv(st.session_state.file_path, index=False)
                    else:
                        st.session_state.df.to_excel(st.session_state.file_path, index=False)
                    st.toast("Data cleaned successfully!")
                    st.rerun()
        else:
            st.success("✨ Data is Clean & Optimized")
            
        if st.session_state.messages:
            if st.button("↩️ Clear History", use_container_width=True):
                st.session_state.messages = []
                database.clear_session(st.session_state.session_id)
                st.rerun()
                
    # Top Metrics / Preview
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        with st.expander("🔍 Data Preview"):
            st.dataframe(st.session_state.df.head(10), use_container_width=True)
    
    if st.session_state.profiling:
        with col2:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.metric("Missing Values", st.session_state.profiling["missing"])
            st.metric("Memory Footprint", st.session_state.profiling["memory"])
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.metric("Duplicate Rows", st.session_state.profiling["duplicates"])
            st.metric("Data Features", st.session_state.profiling["num_cols"])
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat History
    st.markdown("### 💬 Analysis Chat")
    chat_container = st.container(height=400)
    
    # Reload messages from DB if session state is empty but DB has data
    # (Assuming we might want to reload a past session, but for now session_id is transient)
    # If we wanted to load history, we would query database.get_session_history(st.session_state.session_id)
    
    for message in st.session_state.messages:
        with chat_container:
            role_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
            content = message["content"]
            if isinstance(content, list):
                text_parts = [part["text"] for part in content if isinstance(part, dict) and "text" in part]
                content = "\\n".join(text_parts) if text_parts else str(content)
            
            st.markdown(f"<div class='chat-bubble {role_class}'>{content}</div>", unsafe_allow_html=True)
            
            if "plots" in message:
                for plot in message["plots"]:
                    if plot.endswith(".html"):
                        try:
                            with open(plot, 'r', encoding='utf-8') as f:
                                html_data = f.read()
                            components.html(html_data, height=500, scrolling=True)
                        except Exception as e:
                            st.error(f"Could not load interactive chart: {e}")
                    else:
                        st.image(plot, use_container_width=True)

    # Suggested Questions
    if st.session_state.df is not None and st.session_state.auto_insights:
        st.markdown("---")
        st.markdown("💡 **Suggested Analysis:**")
        cols = st.columns(3)
        for i, q in enumerate(st.session_state.auto_insights["questions"]):
            if cols[i%3].button(q, key=f"suggest_{i}"):
                # Append question, save to DB, and process in the chat flow
                msg = {"role": "user", "content": q}
                st.session_state.messages.append(msg)
                database.save_message(st.session_state.session_id, msg["role"], msg["content"])
                # Setting a placeholder in session state to auto-run is tricky in Streamlit without st.rerun(), 
                # but we'll let it be handled by a slight workaround or just let the user copy it.
                st.info(f"You asked: {q}. Please copy and paste it into the chat below!")
                # In Streamlit, native buttons don't trigger chat_input natively yet.

    # User Input
    if prompt := st.chat_input("Ask StatBot Pro about your data..."):
        user_msg = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_msg)
        database.save_message(st.session_state.session_id, user_msg["role"], user_msg["content"])
        
        with chat_container:
            st.markdown(f"<div class='chat-bubble user-bubble'>{prompt}</div>", unsafe_allow_html=True)
        
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("Please provide a Google API Key in the sidebar.")
        else:
            with st.spinner("StatBot is analyzing your request..."):
                try:
                    figures_dir = "exports/figures"
                    if os.path.exists(figures_dir):
                        for f in os.listdir(figures_dir):
                            if not f.startswith("shot_"):
                                try:
                                    os.remove(os.path.join(figures_dir, f))
                                except:
                                    pass
                    os.makedirs(figures_dir, exist_ok=True)
                    
                    history_messages = []
                    for msg in st.session_state.messages:
                        role = "user" if msg["role"] == "user" else "assistant"
                        history_messages.append({"role": role, "content": msg["content"]})

                    agent = get_sandbox_agent(st.session_state.file_path, st.session_state.selected_model)
                    pre_files = set(os.listdir("exports/figures"))
                    
                    result = agent.invoke({"messages": history_messages})
                    
                    bot_response = result["messages"][-1].content
                    new_message = {"role": "assistant", "content": bot_response}
                    
                    post_files = set(os.listdir("exports/figures"))
                    new_plot_files = post_files - pre_files
                    
                    new_plots = []
                    for f in new_plot_files:
                        if f.endswith(".png") or f.endswith(".html"):
                            fpath = os.path.join("exports/figures", f)
                            hist_plot = f"exports/figures/shot_{uuid.uuid4().hex[:6]}_{f}"
                            import shutil
                            shutil.copy(fpath, hist_plot)
                            new_plots.append(hist_plot)
                    
                    if new_plots:
                        new_message["plots"] = new_plots
                    
                    st.session_state.messages.append(new_message)
                    database.save_message(st.session_state.session_id, new_message["role"], new_message["content"], new_message.get("plots"))
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Exploration failed: {str(e)}")

else:
    # Empty State
    st.markdown("""
    <div style='text-align: center; padding: 5rem; background: #1a1c24; border-radius: 20px; border: 2px dashed #4facfe;'>
        <h2 style='color: #4facfe;'>Ready to get started?</h2>
        <p>StatBot Pro is waiting for your dataset. Upload a CSV or Excel file to begin autonomous exploration.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>StatBot Pro v2.1 | Powered by Gemini & LangChain</p>", unsafe_allow_html=True)

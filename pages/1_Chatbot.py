import streamlit as st
import pandas as pd
import os
import uuid
import streamlit.components.v1 as components

from sandbox_agent import get_sandbox_agent
from dotenv import load_dotenv

from ui_components import apply_premium_css, init_session
from data_utils import smart_clean_dataframe
from report_generator import generate_pdf_report
import database

# Load environment variables
load_dotenv()

# App Page Config
st.set_page_config(
    page_title="StatBot Pro - Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS styling
apply_premium_css()
init_session()

# Check if data is loaded
if st.session_state.df is None:
    st.warning("⚠️ No dataset found. Please go to the Home page to upload a file.")
    if st.button("⬅️ Go to Home"):
        st.switch_page("app.py")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
    
    api_key = st.text_input("Google AI API Key", type="password", placeholder="Paste your API key here...", value=os.getenv("GOOGLE_API_KEY", ""))
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.markdown("---")
    st.markdown("### 🤖 Model Selection")
    model_map = {
        "⚡ Flash Lite (Ultra Fast)": "gemini-flash-lite-latest",
        "⚖️ Flash (Balanced)": "gemini-2.5-flash",
        "🧠 Pro (Expert Reasoning)": "gemini-2.5-pro"
    }
    # Pre-select based on session state
    idx = list(model_map.values()).index(st.session_state.selected_model) if st.session_state.selected_model in model_map.values() else 0
    choice = st.selectbox("Choose Intelligence Level", options=list(model_map.keys()), index=idx)
    st.session_state.selected_model = model_map[choice]
    
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
        if st.button("↩️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            database.clear_session(st.session_state.session_id)
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 📄 Export")
    if st.session_state.messages:
        pdf_buffer = generate_pdf_report(st.session_state.messages)
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer.getvalue(),
            file_name="statbot_analysis_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("Ask some questions to generate a report.")

# --- MAIN UI ---
st.markdown("<h2 class='main-title' style='font-size: 3rem;'>Analysis Chat</h2>", unsafe_allow_html=True)

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
st.markdown("### 💬 Chat")
chat_container = st.container(height=500)

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
            msg = {"role": "user", "content": q}
            st.session_state.messages.append(msg)
            database.save_message(st.session_state.session_id, msg["role"], msg["content"])
            st.info(f"You asked: {q}. Please copy and paste it into the chat below!")

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

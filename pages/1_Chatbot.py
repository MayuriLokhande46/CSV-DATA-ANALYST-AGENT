import streamlit as st
import pandas as pd
import os
import uuid
import shutil
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

# --- Handle suggested question trigger from session state ---
auto_prompt = st.session_state.pop("auto_prompt", None)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ Configuration</h2>", unsafe_allow_html=True)

    api_key = st.text_input(
        "Google AI API Key",
        type="password",
        placeholder="Paste your API key here...",
        value=os.getenv("GOOGLE_API_KEY", "")
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    st.markdown("---")
    st.markdown("### 🤖 Model Selection")
    model_map = {
        "⚡ Flash (Balanced)": "gemini-flash-latest",
        "🧠 Pro (Expert Reasoning)": "gemini-pro-latest",
    }
    idx = list(model_map.values()).index(st.session_state.selected_model) \
        if st.session_state.selected_model in model_map.values() else 0
    choice = st.selectbox("Choose Intelligence Level", options=list(model_map.keys()), index=idx)
    st.session_state.selected_model = model_map[choice]

    # Docker status badge
    st.markdown("---")
    from sandbox_executor import ExecutionSandbox
    _sb = ExecutionSandbox()
    if _sb.is_docker_available:
        st.success("🐳 Docker Sandbox: Active")
    else:
        st.warning("⚠️ Docker not found — running locally (less secure).")

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
                st.toast("✅ Data cleaned successfully!")
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
            label="📥 Download PDF Report",
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

# --- Suggested Questions (now auto-trigger on click) ---
if st.session_state.df is not None and st.session_state.auto_insights:
    st.markdown("---")
    st.markdown("💡 **Suggested Analysis — click to instantly analyze:**")
    cols = st.columns(3)
    for i, q in enumerate(st.session_state.auto_insights.get("questions", [])):
        if cols[i % 3].button(q, key=f"suggest_{i}"):
            # Store in session state so it triggers AFTER rerun
            st.session_state["auto_prompt"] = q
            st.rerun()

# Chat History
st.markdown("### 💬 Chat")
chat_container = st.container(height=520)

with chat_container:
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]

        # Normalize content if it's a list (multi-part LLM response)
        if isinstance(content, list):
            text_parts = [
                part["text"] for part in content
                if isinstance(part, dict) and "text" in part
            ]
            content = "\n".join(text_parts) if text_parts else str(content)

        with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
            st.markdown(content)

            # Render plots attached to this message
            if "plots" in message:
                for plot in message["plots"]:
                    if not os.path.exists(plot):
                        continue
                    if plot.endswith(".html"):
                        try:
                            with open(plot, "r", encoding="utf-8") as f:
                                html_data = f.read()
                            components.html(html_data, height=520, scrolling=True)
                        except Exception as e:
                            st.error(f"Could not load interactive chart: {e}")
                    elif plot.endswith(".png") or plot.endswith(".jpg"):
                        st.image(plot, use_container_width=True)


def _run_agent(prompt: str):
    """Core function: run agent, capture response + plots, save to session."""
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("❌ Please provide a Google AI API Key in the sidebar.")
        return

    session_id = st.session_state.session_id
    figures_dir = os.path.join("exports", "figures", session_id)
    os.makedirs(figures_dir, exist_ok=True)

    with st.spinner("🔍 StatBot is analyzing your request..."):
        try:
            # Build conversation history for the agent
            history_messages = []
            for msg in st.session_state.messages:
                role = "user" if msg["role"] == "user" else "assistant"
                c = msg["content"]
                if isinstance(c, list):
                    c = "\n".join(
                        p["text"] for p in c if isinstance(p, dict) and "text" in p
                    )
                history_messages.append({"role": role, "content": str(c)})

            # Snapshot files before agent runs
            pre_files = set(os.listdir(figures_dir))

            agent = get_sandbox_agent(
                st.session_state.file_path,
                st.session_state.selected_model,
                session_id=session_id,
            )
            result = agent.invoke({"messages": history_messages})

            bot_response = result["messages"][-1].content
            new_message = {"role": "assistant", "content": bot_response}

            # Detect newly created plots
            post_files = set(os.listdir(figures_dir))
            new_plot_files = post_files - pre_files

            new_plots = []
            for f in new_plot_files:
                if f.endswith(".png") or f.endswith(".html"):
                    src = os.path.join(figures_dir, f)
                    # Keep a persistent copy prefixed with shot_ so it survives future cleans
                    dest = os.path.join(figures_dir, f"shot_{uuid.uuid4().hex[:6]}_{f}")
                    shutil.copy(src, dest)
                    new_plots.append(dest)

            if new_plots:
                new_message["plots"] = new_plots

            st.session_state.messages.append(new_message)
            database.save_message(
                session_id,
                new_message["role"],
                new_message["content"],
                new_message.get("plots"),
            )
            st.rerun() # Move rerun here so it only happens on success

        except Exception as e:
            st.error(f"❌ Exploration failed: {str(e)}")


# --- User Chat Input ---
if prompt := st.chat_input("Ask StatBot Pro about your data..."):
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    database.save_message(st.session_state.session_id, user_msg["role"], user_msg["content"])
    _run_agent(prompt)

# --- Auto prompt from suggested question button ---
if auto_prompt:
    user_msg = {"role": "user", "content": auto_prompt}
    st.session_state.messages.append(user_msg)
    database.save_message(st.session_state.session_id, user_msg["role"], user_msg["content"])
    _run_agent(auto_prompt)

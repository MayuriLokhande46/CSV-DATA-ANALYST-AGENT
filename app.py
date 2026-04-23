import streamlit as st
import pandas as pd
import os
import uuid
from sandbox_agent import get_sandbox_agent
from sandbox_executor import ExecutionSandbox
from dotenv import load_dotenv
import zipfile
import io
import shutil

# Load environment variables
load_dotenv()

# App Page Config
st.set_page_config(
    page_title="StatBot Pro - Premium AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM CSS STYLING ---
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

# Helper function to initialize session state
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

def smart_clean_dataframe(df):
    """Performs non-destructive cleaning on the dataframe."""
    new_df = df.copy()
    
    # 1. Clean Column Names
    new_df.columns = [str(c).strip().replace(" ", "_").lower() for c in new_df.columns]
    
    # 2. Handle Numeric Missing Values
    num_cols = new_df.select_dtypes(include=['number']).columns
    for col in num_cols:
        new_df[col] = new_df[col].fillna(new_df[col].median())
    
    # 3. Handle Categorical Missing Values
    cat_cols = new_df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        if not new_df[col].empty:
            new_df[col] = new_df[col].fillna(new_df[col].mode()[0] if not new_df[col].mode().empty else "Unknown")
            
    return new_df

def get_data_profiling(df):
    """Generates a quick profiling report for the dataframe."""
    profile = {
        "missing": df.isnull().sum().sum(),
        "duplicates": df.duplicated().sum(),
        "memory": f"{df.memory_usage().sum() / 1024**2:.2f} MB",
        "types": df.dtypes.value_counts().to_dict(),
        "num_cols": df.shape[1],
        "num_rows": df.shape[0]
    }
    return profile

def generate_auto_insights(file_path):
    """Generates initial data insights using the LLM."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-flash-lite-latest", temperature=0.7)
    
    # Get a tiny sample for context
    df = st.session_state.df
    sample = df.head(5).to_string()
    columns = ", ".join(df.columns)
    
    prompt = f"""
    You are StatBot Pro. Analyze this dataset overview and provide:
    1. A 2-sentence sophisticated summary of what this data likely represents.
    2. 3 highly diverse, advanced analytical questions the user could ask (e.g., correlations, trends, forecasts).
    
    DATA OVERVIEW:
    Columns: {columns}
    Sample Data:
    {sample}
    
    FORMAT:
    Summary: [Your summary]
    Questions:
    - [Question 1]
    - [Question 2]
    - [Question 3]
    """
    
    try:
        response = llm.invoke(prompt)
        text = response.content
        summary = text.split("Questions:")[0].replace("Summary:", "").strip()
        questions = text.split("Questions:")[1].strip().split("\n")
        questions = [q.strip("- ").strip() for q in questions if q.strip()]
        return {"summary": summary, "questions": questions[:3]}
    except:
        return {
            "summary": "Data loaded successfully. I'm ready to analyze your columns and trends.",
            "questions": ["What is the overall trend?", "Show me a correlation heatmap", "Which category performs best?"]
        }

init_session()

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
            st.rerun()
        
        # Export Analysis
        if st.session_state.messages:
            st.markdown("### 📄 Export")
            
            # Generate MD Report
            report_md = "# StatBot Pro Analysis Report\n\n"
            for msg in st.session_state.messages:
                report_md += f"**{msg['role'].capitalize()}**: {msg['content']}\n\n"
            
            # Create ZIP in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # Add report
                zf.writestr("report.md", report_md)
                # Add plots
                for msg in st.session_state.messages:
                    if "plots" in msg:
                        for plot_path in msg["plots"]:
                            if os.path.exists(plot_path):
                                zf.write(plot_path, os.path.basename(plot_path))
            
            st.download_button(
                label="Download Full Analysis (.zip)",
                data=zip_buffer.getvalue(),
                file_name="statbot_analysis_bundle.zip",
                mime="application/zip"
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
        # Save temp file
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
            
            # Add initial bot message
            welcome_msg = {
                "role": "assistant", 
                "content": f"👋 **Welcome!** I've analyzed your data.\n\n{st.session_state.auto_insights['summary']}"
            }
            st.session_state.messages.append(welcome_msg)
            
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
                    original_rows, original_cols = st.session_state.df.shape
                    st.session_state.df = smart_clean_dataframe(st.session_state.df)
                    st.session_state.is_cleaned = True
                    # Re-save the cleaned dataframe to the file path so the agent sees it
                    if st.session_state.file_path.endswith(".csv"):
                        st.session_state.df.to_csv(st.session_state.file_path, index=False)
                    else:
                        st.session_state.df.to_excel(st.session_state.file_path, index=False)
                    
                    st.toast("Data cleaned successfully!")
                    st.rerun()
        else:
            st.success("✨ Data is Clean & Optimized")
            
        if st.session_state.messages:
            if st.button("↩️ Undo Last Question", use_container_width=True):
                if len(st.session_state.messages) >= 2:
                    st.session_state.messages.pop() # Remove bot response
                    st.session_state.messages.pop() # Remove user question
                    st.rerun()
                elif len(st.session_state.messages) == 1:
                    st.session_state.messages.pop()
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
    
    for message in st.session_state.messages:
        with chat_container:
            role_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
            content = message["content"]
            # Handle structured content from modern LLMs
            if isinstance(content, list):
                text_parts = [part["text"] for part in content if isinstance(part, dict) and "text" in part]
                content = "\n".join(text_parts) if text_parts else str(content)
            
            st.markdown(f"<div class='chat-bubble {role_class}'>{content}</div>", unsafe_allow_html=True)
            if "plots" in message:
                for plot in message["plots"]:
                    st.image(plot, use_container_width=True)

    # Suggested Questions
    if st.session_state.df is not None and st.session_state.auto_insights:
        st.markdown("---")
        st.markdown("💡 **Suggested Analysis:**")
        cols = st.columns(3)
        for i, q in enumerate(st.session_state.auto_insights["questions"]):
            if cols[i%3].button(q, key=f"suggest_{i}"):
                # This doesn't trigger the chat_input block, so we handle it by setting a query param or re-triggering logic
                # For simplicity in Streamlit, we'll just set the prompt and rerun or handle it as a new input
                st.session_state.messages.append({"role": "user", "content": q})
                st.rerun()

    # User Input
    if prompt := st.chat_input("Ask StatBot Pro about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.markdown(f"<div class='chat-bubble user-bubble'>{prompt}</div>", unsafe_allow_html=True)
        
        # Process with Agent
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("Please provide a Google API Key in the sidebar.")
        else:
            with st.spinner("StatBot is analyzing your request..."):
                try:
                    # Clear previous plots to ensure new ones are detected
                    figures_dir = "exports/figures"
                    if os.path.exists(figures_dir):
                        for f in os.listdir(figures_dir):
                            # Only clear files that aren't 'shot_' (which are history copies)
                            if not f.startswith("shot_"):
                                try:
                                    os.remove(os.path.join(figures_dir, f))
                                except:
                                    pass
                    os.makedirs(figures_dir, exist_ok=True)
                    
                    # Format history for LangChain 1.x (List of dicts or BaseMessages)
                    history_messages = []
                    for msg in st.session_state.messages:
                        role = "user" if msg["role"] == "user" else "assistant"
                        history_messages.append({"role": role, "content": msg["content"]})

                    agent = get_sandbox_agent(st.session_state.file_path, st.session_state.selected_model)
                    os.makedirs("exports/figures", exist_ok=True)
                    
                    # Track files before execution
                    pre_files = set(os.listdir("exports/figures"))
                    
                    # LangChain 1.x Graph invocation
                    result = agent.invoke({"messages": history_messages})
                    
                    # Extract the last message from the assistant
                    bot_response = result["messages"][-1].content
                    new_message = {"role": "assistant", "content": bot_response}
                    
                    # Capture new plots
                    post_files = set(os.listdir("exports/figures"))
                    new_plot_files = post_files - pre_files
                    
                    new_plots = []
                    for f in new_plot_files:
                        if f.endswith(".png"):
                            fpath = os.path.join("exports/figures", f)
                            # Save unique copy for history to avoid overwriting issues
                            hist_plot = f"exports/figures/shot_{uuid.uuid4().hex[:6]}_{f}"
                            import shutil
                            shutil.copy(fpath, hist_plot)
                            new_plots.append(hist_plot)
                    
                    if new_plots:
                        new_message["plots"] = new_plots
                    
                    st.session_state.messages.append(new_message)
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
st.markdown("<p style='text-align: center; color: #666;'>StatBot Pro v2.0 | Powered by Gemini 1.5 Flash & LangChain</p>", unsafe_allow_html=True)

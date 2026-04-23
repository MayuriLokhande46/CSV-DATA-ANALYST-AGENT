# StatBot Pro: Autonomous CSV Data Analyst Agent

StatBot Pro is an AI-powered data analyst that uses LangGraph Agents to perform complex queries on CSV/Excel files. It can write its own Python code, execute it, and return both textual insights and visualizations.

## Quick Start
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup Sandbox (Optional but Recommended)**:
   Ensure Docker is running and execute:
   ```bash
   python setup_sandbox.py
   ```
3. **Setup API Key**:
   Create a `.env` file with `GOOGLE_API_KEY=...` or provide it in the UI.
4. **Run the App**:
   ```bash
   streamlit run app.py
   ```

## Features
- **Smart Data Cleaning**: Normalize columns and handle missing values with one click.
- **Autonomous Reasoning**: Uses Gemini 2.x/3.x to understand business questions.
- **Data Visualization**: Generates professional Matplotlib/Seaborn charts.
- **Sandboxed Execution**: Runs code inside Docker containers for safety.
- **Full Export**: Download analysis reports and charts as a single ZIP bundle.

## Technical Details
- **Architecture**: LangGraph-based RAG-Agent.
- **AI Model**: Gemini Flash (Optimized for 2026 stack).
- **Backend**: Python 3.9+ with Docker isolation.
- **Frontend**: Streamlit with custom Glassmorphism UI.

## Project Structure
- `app.py`: Main UI & State Management
- `sandbox_agent.py`: Agent logic & Tool definitions
- `sandbox_executor.py`: Local/Docker execution logic
- `setup_sandbox.py`: Automation script for Docker setup
- `exports/figures/`: Storage for generated visualizations

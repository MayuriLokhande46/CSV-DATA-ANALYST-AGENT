import os
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from sandbox_executor import ExecutionSandbox

load_dotenv()

# Global sandbox instance
sandbox = ExecutionSandbox()

# We use a mutable dict so the tool closure can access the current session_id
_session_context = {"session_id": "default"}


@tool
def python_sandbox(code: str):
    """
    Executes Python code for data analysis and plotting.
    Use this tool to interact with the dataframe 'df' and create visualizations.
    The code runs in a secure, sandboxed environment.

    IMPORTANT RULES:
    1. Always save interactive Plotly plots: fig.write_html('exports/figures/your_plot_name.html')
    2. For static matplotlib/seaborn plots: plt.savefig('exports/figures/your_plot_name.png', dpi=150, bbox_inches='tight')
    3. NEVER call plt.show() or fig.show() — they are automatically suppressed.
    4. Give every plot a unique, descriptive filename.
    5. All saved plots are automatically displayed to the user.
    """
    session_id = _session_context.get("session_id", "default")

    # Strip potential markdown fences that LLM might include
    clean_code = code.strip()
    if clean_code.startswith("```python"):
        clean_code = clean_code[9:]
    if clean_code.startswith("```"):
        clean_code = clean_code[3:]
    if clean_code.endswith("```"):
        clean_code = clean_code[:-3]
    clean_code = clean_code.strip()

    result = sandbox.execute_code(clean_code, session_id=session_id)

    # Build structured feedback for the LLM
    feedback_parts = []

    if result.get("blocked"):
        feedback_parts.append(f"🚫 SECURITY BLOCKED:\n{result['stderr']}")
        return "\n".join(feedback_parts)

    if result["stdout"]:
        feedback_parts.append(f"STDOUT:\n{result['stdout']}")

    if result["stderr"]:
        feedback_parts.append(f"STDERR (warnings/errors):\n{result['stderr']}")

    if result["artifacts"]:
        feedback_parts.append(
            f"✅ SUCCESS: Generated {len(result['artifacts'])} plot(s): "
            + ", ".join(result["artifacts"])
        )
    else:
        if result["success"]:
            feedback_parts.append("✅ Code executed successfully (no plots generated).")
        else:
            feedback_parts.append("❌ Execution failed. See STDERR above for details.")

    feedback_parts.append(f"Sandbox Mode: {'Docker 🐳' if result['is_sandbox'] else 'Local ⚠️'}")

    return "\n\n".join(feedback_parts)


def get_sandbox_agent(df_path: str, model_name: str = "gemini-2.0-flash", session_id: str = "default"):
    """
    Creates a StatBot Pro agent using the modern LangGraph create_react_agent.
    Session ID is used to isolate per-user figure outputs.
    """
    # Update session context so the tool closure picks up the right session
    _session_context["session_id"] = session_id

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    # Determine correct read command
    read_cmd = "pd.read_csv" if df_path.endswith(".csv") else "pd.read_excel"
    # Use forward slashes for cross-platform compatibility
    df_path_safe = df_path.replace("\\", "/")

    system_prompt = f"""You are StatBot Pro, a world-class autonomous data analyst.
Your mission: answer user questions by writing and executing precise Python code.

━━━━━━━━━━━━━━━━━━━━━━━━━━
DATASET CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━
- File Path : '{df_path_safe}'
- DataFrame : 'df'

━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CODE STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━
Always start your code with:
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import matplotlib.pyplot as plt
    import seaborn as sns
    df = {read_cmd}('{df_path_safe}')

━━━━━━━━━━━━━━━━━━━━━━━━━━
VISUALIZATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━
- PREFER Plotly for all interactive charts.
- Save Plotly: fig.write_html('exports/figures/descriptive_name.html')
- Save Matplotlib: plt.savefig('exports/figures/descriptive_name.png', dpi=150, bbox_inches='tight')
- Template: use template="plotly_dark" for all plotly charts.
- NEVER call plt.show() or fig.show() — they are blocked.

━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━
1. For complex questions, break them into steps and call python_sandbox multiple times.
2. After execution, provide a concise, professional business summary of your findings.
3. If code fails, diagnose the error from STDERR and retry with a corrected version.
4. Always explain your findings in plain English after the analysis.
"""

    # create_react_agent returns a compiled LangGraph StateGraph
    graph = create_react_agent(
        model=llm,
        tools=[python_sandbox],
        prompt=system_prompt,
    )

    return graph


if __name__ == "__main__":
    # Quick smoke test
    test_csv = "test_data.csv"
    pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}).to_csv(test_csv, index=False)
    agent = get_sandbox_agent(test_csv, session_id="smoke_test")
    result = agent.invoke({"messages": [{"role": "user", "content": "What is the average of column A?"}]})
    print(result["messages"][-1].content)
    os.remove(test_csv)

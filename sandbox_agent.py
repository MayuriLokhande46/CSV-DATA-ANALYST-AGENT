import os
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from sandbox_executor import ExecutionSandbox

load_dotenv()

# Global sandbox instance
sandbox = ExecutionSandbox()

@tool
def python_sandbox(code: str):
    """
    Executes Python code for data analysis and plotting. 
    Use this tool to interact with the dataframe 'df' and create visualizations.
    The code runs in a sandboxed environment.
    
    IMPORTANT RULES:
    1. Always save plots using: plt.savefig('exports/figures/your_plot_name.png')
    2. You can save multiple plots with unique names.
    3. All plots are automatically captured and shown to the user.
    """
    # We strip any potential markdown code blocks if the LLM includes them
    clean_code = code.strip()
    if clean_code.startswith("```python"):
        clean_code = clean_code[9:]
    if clean_code.endswith("```"):
        clean_code = clean_code[:-3]
    
    result = sandbox.execute_code(clean_code)
    
    feedback = f"STDOUT:\n{result['stdout']}"
    if result["stderr"]:
        feedback += f"\nSTDERR:\n{result['stderr']}"
    
    if result["artifacts"]:
        feedback += f"\n\nSUCCESS: Generated {len(result['artifacts'])} plot(s): {', '.join(result['artifacts'])}"
    
    return f"{feedback}\nSandbox Mode: {result['is_sandbox']}"

from langchain.agents import create_agent

def get_sandbox_agent(df_path: str, model_name: str = "gemini-flash-lite-latest"):
    """
    Creates a StatBot Pro agent using the LangChain 1.x graph factory.
    """
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Simple logic to determine read command
    read_cmd = "pd.read_csv" if df_path.endswith(".csv") else "pd.read_excel"

    system_prompt = f"""You are StatBot Pro, a premium autonomous data analyst. 
Your goal is to answer user questions by writing and executing Python code.

DATASET CONTEXT:
- File Path: '{df_path}'
- Primary DataFrame Name: 'df'

CORE INSTRUCTIONS:
1. START your code with:
   import pandas as pd
   import matplotlib.pyplot as plt
   import seaborn as sns
   df = {read_cmd}('{df_path}')

2. VISUALIZATION:
   - ALWAYS save plots to 'exports/figures/'.
   - Format: plt.savefig('exports/figures/unique_plot_name.png')
   - NEVER use plt.show().
   - Use professional styles (e.g., sns.set_theme(style="darkgrid")).

3. MULTI-STEP EXECUTION:
   - Handle complex, multi-part questions (e.g., "Analyze A AND plot B").
   - You can call the 'python_sandbox' tool multiple times if needed.
   - For multiple charts, give them unique names: 'exports/figures/sales_trend.png', 'exports/figures/category_dist.png', etc.
   - Always conclude with a sophisticated business summary of ALL tasks performed.
"""

    # create_agent in 1.x returns a compiled graph
    graph = create_agent(
        model=llm,
        tools=[python_sandbox],
        system_prompt=system_prompt
    )

    return graph

if __name__ == "__main__":
    # Quick test
    test_csv = "test_data.csv"
    pd.DataFrame({'A': [1, 2], 'B': [3, 4]}).to_csv(test_csv, index=False)
    
    agent = get_sandbox_agent(test_csv)
    # result = agent.invoke({"input": "What is the average of column A?"})
    # print(result["output"])
    os.remove(test_csv)

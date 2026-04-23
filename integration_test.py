import os
import pandas as pd
from sandbox_agent import get_sandbox_agent
from dotenv import load_dotenv

load_dotenv()

def test_agent():
    # 1. Create dummy data
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'David'],
        'Age': [25, 30, 35, 40],
        'Salary': [50000, 60000, 70000, 80000]
    }
    df = pd.DataFrame(data)
    test_csv = "integration_test.csv"
    df.to_csv(test_csv, index=False)
    
    print(f"Created test data: {test_csv}")
    
    # 2. Initialize Agent
    agent = get_sandbox_agent(test_csv, "gemini-flash-lite-latest")
    
    # 3. Invoke Agent
    print("Invoking agent...")
    try:
        result = agent.invoke({
            "messages": [
                {"role": "user", "content": "1. What is the average salary? 2. Create a bar chart for Salaries. 3. Show a pie chart of the Name distribution (fake count of 1 for each)."}
            ]
        })
        
        print("\n--- AGENT RESPONSE ---")
        last_msg = result["messages"][-1]
        # In modern LangChain, result['messages'] contains BaseMessage objects
        print(f"Content: {last_msg.content}")
        
        # Check for plots
        if os.path.exists("exports/figures"):
            plots = os.listdir("exports/figures")
            print(f"\nGenerated plots: {plots}")
        else:
            print("\nNo plots directory found.")
            
    except Exception as e:
        print(f"\nError during invocation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(test_csv):
            os.remove(test_csv)
            print(f"Cleaned up {test_csv}")

if __name__ == "__main__":
    test_agent()

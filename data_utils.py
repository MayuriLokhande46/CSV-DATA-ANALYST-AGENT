import pandas as pd
import streamlit as st

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
        questions = text.split("Questions:")[1].strip().split("\\n")
        questions = [q.strip("- ").strip() for q in questions if q.strip()]
        return {"summary": summary, "questions": questions[:3]}
    except:
        return {
            "summary": "Data loaded successfully. I'm ready to analyze your columns and trends.",
            "questions": ["What is the overall trend?", "Show me a correlation heatmap", "Which category performs best?"]
        }

import pandas as pd
import streamlit as st
import os


def smart_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs robust, non-destructive cleaning on the dataframe.
    Steps:
      1. Clean column names (strip, lowercase, spaces → underscores)
      2. Remove fully duplicate rows
      3. Fill numeric missing values with median
      4. Fill categorical missing values with mode (or 'Unknown')
      5. Strip leading/trailing whitespace from string columns
    """
    new_df = df.copy()

    # 1. Clean column names
    new_df.columns = [
        str(c).strip().replace(" ", "_").replace("-", "_").lower()
        for c in new_df.columns
    ]

    # 2. Drop exact duplicate rows
    before = len(new_df)
    new_df.drop_duplicates(inplace=True)
    dropped = before - len(new_df)
    if dropped > 0:
        st.toast(f"🗑️ Removed {dropped} duplicate row(s).")

    # 3. Fill numeric missing values with median
    num_cols = new_df.select_dtypes(include=["number"]).columns
    for col in num_cols:
        if new_df[col].isnull().any():
            new_df[col] = new_df[col].fillna(new_df[col].median())

    # 4. Fill categorical missing values with mode
    cat_cols = new_df.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        if new_df[col].isnull().any():
            mode_vals = new_df[col].mode()
            fill_val = mode_vals[0] if not mode_vals.empty else "Unknown"
            new_df[col] = new_df[col].fillna(fill_val)

    # 5. Strip whitespace from all string columns
    for col in new_df.select_dtypes(include=["object"]).columns:
        new_df[col] = new_df[col].astype(str).str.strip()

    return new_df


def get_data_profiling(df: pd.DataFrame) -> dict:
    """Generates a rich profiling snapshot for the dataframe."""
    total_cells = df.shape[0] * df.shape[1]
    missing_count = int(df.isnull().sum().sum())
    missing_pct = round((missing_count / total_cells) * 100, 1) if total_cells else 0

    profile = {
        "missing": f"{missing_count} ({missing_pct}%)",
        "duplicates": int(df.duplicated().sum()),
        "memory": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB",
        "types": {str(k): int(v) for k, v in df.dtypes.value_counts().items()},
        "num_cols": df.shape[1],
        "num_rows": df.shape[0],
    }
    return profile


def generate_auto_insights(file_path: str) -> dict:
    """
    Generates initial data insights using the LLM.
    Returns a dict with 'summary' (str) and 'questions' (list of str).
    Falls back gracefully if the API call fails.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        return {
            "summary": "API key not set. Please add your Google AI API Key in the sidebar.",
            "questions": [
                "What is the overall trend in this data?",
                "Show me a correlation heatmap of all numeric columns.",
                "Which category has the highest average value?",
            ],
        }

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0.7,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

        df = st.session_state.df
        sample = df.head(5).to_string(max_cols=20)
        columns = ", ".join(str(c) for c in df.columns)
        shape_info = f"{df.shape[0]:,} rows × {df.shape[1]} columns"

        prompt = f"""You are StatBot Pro, a world-class data analyst.
Analyze this dataset overview and provide a structured response.

DATASET METADATA:
- Shape: {shape_info}
- Columns: {columns}
- Sample Data:
{sample}

YOUR RESPONSE FORMAT (follow exactly):
Summary: [Write 2 concise sentences: what this data likely represents and what key patterns exist]
Questions:
- [Advanced analytical question 1 — e.g., trend, time-series, or growth analysis]
- [Advanced analytical question 2 — e.g., correlation, segmentation, or outlier detection]
- [Advanced analytical question 3 — e.g., top/bottom ranking, forecasting, or comparison]

RULES:
- Questions must be specific to the actual column names present.
- Avoid generic questions. Make them insightful and business-relevant.
- Do NOT include any extra text, headers, or explanations outside the format above.
"""

        response = llm.invoke(prompt)
        text = response.content.strip()

        # Parse summary
        summary = ""
        questions = []

        if "Summary:" in text and "Questions:" in text:
            summary_part = text.split("Questions:")[0].replace("Summary:", "").strip()
            summary = summary_part

            questions_part = text.split("Questions:")[1].strip()
            raw_questions = questions_part.split("\n")
            questions = [
                q.lstrip("- •*").strip()
                for q in raw_questions
                if q.strip() and q.strip() not in ("-", "•", "*")
            ]
            questions = [q for q in questions if len(q) > 10][:3]
        else:
            # Fallback: use full text as summary
            summary = text[:300]

        # Ensure we always have 3 questions
        while len(questions) < 3:
            fallbacks = [
                "What is the overall trend in this data?",
                "Show me a correlation heatmap of all numeric columns.",
                "Which category has the highest average value?",
            ]
            for fb in fallbacks:
                if fb not in questions:
                    questions.append(fb)
                if len(questions) >= 3:
                    break

        return {"summary": summary, "questions": questions[:3]}

    except Exception as e:
        return {
            "summary": f"Data loaded successfully. Ready to analyze your {st.session_state.df.shape[0]:,} rows.",
            "questions": [
                "What is the overall trend in this data?",
                "Show me a correlation heatmap of all numeric columns.",
                "Which category has the highest average value?",
            ],
        }

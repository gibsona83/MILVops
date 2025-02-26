import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np
import sqlite3

# 🎨 MILV Branded Colors
MILV_COLORS = ["#003366", "#00509e", "#007acc", "#66a3d2", "#cfe2f3"]

# ---------------------------
# Page Configuration & Header
# ---------------------------
st.set_page_config(page_title="MILV Diagnostic Radiology", layout="wide")
st.title("MILV Diagnostic Radiology")
st.caption("*excludes mammo and IR modalities*")

# ---------------------------
# 🔧 Configuration: Data Source Selection
# ---------------------------
DATA_SOURCE = "sqlite"  # Options: "csv", "sqlite"
DB_PATH = "data/milv_data.db"  # Path to SQLite database
DATA_FOLDER = "data/"  # Folder where CSV/Excel files are stored

# ---------------------------
# 📥 Load Data from SQLite or CSV/Excel
# ---------------------------
@st.cache_data
def load_data():
    """Loads data from SQLite or CSV/Excel based on the configuration."""
    if DATA_SOURCE == "sqlite":
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql("SELECT * FROM provider_data", conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading SQLite database: {e}")
            return pd.DataFrame()
    else:
        all_files = os.listdir(DATA_FOLDER)
        data_files = [f for f in all_files if f.lower().endswith((".csv", ".xlsx"))]

        if not data_files:
            st.error(f"No CSV or Excel files found in '{DATA_FOLDER}'.")
            return pd.DataFrame()

        df_list = []
        for filename in data_files:
            file_path = os.path.join(DATA_FOLDER, filename)
            try:
                if filename.lower().endswith(".csv"):
                    temp_df = pd.read_csv(file_path)
                else:
                    temp_df = pd.read_excel(file_path)
                temp_df["source_file"] = filename
                df_list.append(temp_df)
            except Exception as e:
                st.warning(f"Skipping file '{filename}' due to error: {e}")

        non_empty = [df for df in df_list if not df.empty]
        if not non_empty:
            st.error("All files are empty or invalid.")
            return pd.DataFrame()

        common_columns = set(non_empty[0].columns)
        for d in non_empty[1:]:
            common_columns = common_columns.intersection(set(d.columns))
        common_columns = list(common_columns)

        merged = [d[common_columns] for d in non_empty]
        return pd.concat(merged, ignore_index=True)

df = load_data()
if df.empty:
    st.stop()  # Ends execution if no data loaded

# ---------------------------
# Data Preprocessing
# ---------------------------
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

required_cols = ["created_date", "final_date", "modality", "section", "finalizing_provider", "rvu"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Required columns missing: {missing}")
    st.stop()

df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
df["final_date"] = pd.to_datetime(df["final_date"], errors="coerce")
df["tat"] = (df["final_date"] - df["created_date"]).dt.total_seconds() / 60

def get_milv_quarter(date):
    if pd.isna(date):
        return None
    return {
        4: "Q1", 5: "Q1", 6: "Q1",
        7: "Q2", 8: "Q2", 9: "Q2",
        10: "Q3", 11: "Q3", 12: "Q3",
        1: "Q4", 2: "Q4", 3: "Q4"
    }.get(date.month, None)

df["quarter"] = df["created_date"].apply(get_milv_quarter)
df["rvu"] = pd.to_numeric(df["rvu"], errors="coerce").fillna(0)
df["rvu_per_exam"] = df["rvu"] / df["tat"].replace(0, 1)

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.image("milv.png", width=250)
st.sidebar.header("📊 Filters")

# Quarter Selection
quarter_options = ["ALL"] + sorted(df["quarter"].dropna().unique())
selected_quarters = st.sidebar.multiselect("📆 Select Quarters", quarter_options, default=["ALL"])
if "ALL" not in selected_quarters:
    df = df[df["quarter"].isin(selected_quarters)]

# Date Range Filter
default_min_date, default_max_date = df["created_date"].min(), df["created_date"].max()
date_range = st.sidebar.date_input("📆 Select Date Range", [default_min_date, default_max_date])
if isinstance(date_range, list) and len(date_range) == 2:
    df = df[(df["created_date"] >= pd.to_datetime(date_range[0])) & (df["created_date"] <= pd.to_datetime(date_range[1]))]

# Section Filter
section_options = ["ALL"] + sorted(df["section"].dropna().unique())
selected_sections = st.sidebar.multiselect("🏥 Select Sections", section_options, default=["ALL"])
if "ALL" not in selected_sections:
    df = df[df["section"].isin(selected_sections)]

# Download CSV
csv_data = df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(label=f"📥 Download {len(df):,} rows as CSV", data=csv_data, file_name="filtered_data.csv", mime="text/csv")

if df.empty:
    st.warning("No data after current filtering. Adjust filters to see results.")
    st.stop()

# ---------------------------
# Aggregated KPIs Display
# ---------------------------
st.markdown("## 📊 Aggregated KPIs")
col1, col2, col3, col4 = st.columns(4)
col1.metric("📝 Total Exams", f"{len(df):,}")
col2.metric("⚖️ Total RVU", f"{df['rvu'].sum():,.2f}")
col3.metric("📊 Avg RVU/Exam", f"{df['rvu_per_exam'].mean():,.2f}")
col4.metric("⏳ Avg TAT (mins)", f"{df['tat'].mean():,.2f}")

# ---------------------------
# Deployment Instructions
# ---------------------------
st.markdown(
    """
    ### 📌 Deployment Instructions
    1. **Push to GitHub**:
       ```
       git init
       git add .
       git commit -m "Initial commit"
       git branch -M main
       git remote add origin https://github.com/gibsona83/MILVops.git
       git push -u origin main
       ```
    2. **Deploy on Streamlit Cloud**:
       - Go to **[Streamlit Cloud](https://share.streamlit.io/)**
       - Connect your GitHub repository
       - Set `app.py` as the main entry point.
       - Ensure `data/milv_data.db` or CSV files are in the repo.
    """
)

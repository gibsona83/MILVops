import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 🎨 MILV Branded Colors
MILV_COLORS = ["#003366", "#00509e", "#007acc", "#66a3d2", "#cfe2f3"]

# ---------------------------
# Page Configuration & Header
# ---------------------------
st.set_page_config(page_title="MILV Diagnostic Radiology", layout="wide")
st.title("MILV Diagnostic Radiology")
st.caption("*Excludes mammo and IR modalities*")

# ---------------------------
# 📥 Load Data from CSV/Excel (Root Directory)
# ---------------------------
DATA_FOLDER = "."  # Main directory (no 'data/' folder)

@st.cache_data
def load_csv_data():
    """Loads all CSV files from the main directory and merges them."""
    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

    if not csv_files:
        st.error("❌ No CSV files found in the main directory.")
        return pd.DataFrame()

    df_list = []
    for file in csv_files:
        file_path = os.path.join(DATA_FOLDER, file)
        try:
            temp_df = pd.read_csv(file_path)
            temp_df["source_file"] = file  # Track source file
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"⚠️ Skipping {file} due to error: {e}")

    if not df_list:
        st.error("❌ All CSV files are empty or invalid.")
        return pd.DataFrame()

    # Standardize column names (remove spaces, lowercase)
    for df in df_list:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Expected Columns
    expected_columns = ["created_date", "final_date", "modality", "section", "finalizing_provider", "rvu"]

    # Check if all expected columns exist
    missing_cols = [col for col in expected_columns if col not in df_list[0].columns]
    if missing_cols:
        st.error(f"❌ Missing required columns: {missing_cols}")
        st.write("🔍 Found columns in CSV:", list(df_list[0].columns))  # Show available columns
        return pd.DataFrame()

    # Merge only common columns
    merged_df = pd.concat([df[expected_columns] for df in df_list], ignore_index=True)
    return merged_df

df = load_csv_data()

# Stop execution if no data
if df.empty:
    st.stop()

# ---------------------------
# Data Preprocessing
# ---------------------------
df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
df["final_date"] = pd.to_datetime(df["final_date"], errors="coerce")

# Calculate Turnaround Time (TAT) in minutes
df["tat"] = (df["final_date"] - df["created_date"]).dt.total_seconds() / 60

# Standardize RVU values
df["rvu"] = pd.to_numeric(df["rvu"], errors="coerce").fillna(0)
df["rvu_per_exam"] = df["rvu"] / df["tat"].replace(0, 1)

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.image("milv.png", width=250)
st.sidebar.header("📊 Filters")

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
    st.warning("No data after applying filters. Adjust filters to see results.")
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
       git commit -m "Updated app to handle missing columns"
       git branch -M main
       git remote add origin https://github.com/gibsona83/MILVops.git
       git push -u origin main
       ```
    2. **Deploy on Streamlit Cloud**:
       - Go to **[Streamlit Cloud](https://share.streamlit.io/)**
       - Connect your GitHub repository
       - Set `app.py` as the main entry point.
       - Ensure CSV files are **in the main directory** (not inside `data/`).
    """
)

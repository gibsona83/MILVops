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
# 📥 Load Data from CSV/Excel
# ---------------------------
DATA_FOLDER = "data/"  # Folder where CSV files are stored

@st.cache_data
def load_csv_data():
    """Loads all CSV files from the data folder, merges them into a single DataFrame."""
    if not os.path.exists(DATA_FOLDER):
        st.error(f"Data folder '{DATA_FOLDER}' not found.")
        return pd.DataFrame()

    # Get all CSV files
    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

    if not csv_files:
        st.error("No CSV files found in the data folder.")
        return pd.DataFrame()

    df_list = []
    for file in csv_files:
        file_path = os.path.join(DATA_FOLDER, file)
        try:
            temp_df = pd.read_csv(file_path)
            temp_df["source_file"] = file  # Track source file
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"Skipping {file} due to error: {e}")

    # Ensure we have valid data
    if not df_list:
        st.error("All CSV files are empty or invalid.")
        return pd.DataFrame()

    # Standardize column names (remove spaces, lowercase)
    for df in df_list:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Find common columns
    common_columns = set(df_list[0].columns)
    for df in df_list[1:]:
        common_columns &= set(df.columns)

    if not common_columns:
        st.error("No common columns found across CSV files.")
        return pd.DataFrame()

    # Merge only common columns
    merged_df = pd.concat([df[list(common_columns)] for df in df_list], ignore_index=True)
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

import streamlit as st
import pandas as pd
import sqlite3
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
# 📥 Load Data from CSV/SQLite (GitHub Source)
# ---------------------------
DATA_SOURCE = "sqlite"  # Options: "csv" or "sqlite"
DB_PATH = "data.db"  # SQLite database file

@st.cache_data
def load_data():
    """Loads data from SQLite or CSV based on configuration."""
    if DATA_SOURCE == "sqlite":
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql("SELECT * FROM provider_data", conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"🚨 Error loading SQLite database: {e}")
            return pd.DataFrame()
    else:
        return load_csv_data()

@st.cache_data
def load_csv_data():
    """Loads CSV files from the main directory, limits rows for large files."""
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv") or f.endswith(".csv.gz")]

    if not csv_files:
        st.error("❌ No CSV files found in the main directory.")
        return pd.DataFrame()

    df_list = []
    for file in csv_files:
        file_path = os.path.join(".", file)
        try:
            temp_df = pd.read_csv(file_path, nrows=100000, compression='infer')  # Loads compressed & uncompressed CSVs
            temp_df["source_file"] = file  # Track source file
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"⚠️ Skipping {file} due to error: {e}")

    if not df_list:
        st.error("❌ All CSV files are empty or invalid.")
        return pd.DataFrame()

    # Standardize column names
    for df in df_list:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Expected Columns (Based on Your CSV Structure)
    expected_columns = ["finalizing_provider", "total_exams", "total_rvu", "total_points"]

    # Check if required columns exist
    missing_cols = [col for col in expected_columns if col not in df_list[0].columns]
    if missing_cols:
        st.error(f"❌ Missing required columns: {missing_cols}")
        st.write("🔍 Found columns in CSV:", list(df_list[0].columns))
        return pd.DataFrame()

    # Merge only common columns
    merged_df = pd.concat([df[expected_columns] for df in df_list], ignore_index=True)
    return merged_df

df = load_data()

# Allow Manual File Upload
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV File (Optional)", type=["csv", "gz"])
if uploaded_file:
    df = pd.read_csv(uploaded_file, compression='infer')

# Stop execution if no data
if df.empty:
    st.warning("⚠️ No data available. Please check your CSV files.")
    st.stop()

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.image("milv.png", width=250)
st.sidebar.header("📊 Filters")

# Provider Filter
provider_options = ["ALL"] + sorted(df["finalizing_provider"].dropna().unique())
selected_providers = st.sidebar.multiselect("👨‍⚕️ Select Providers", provider_options, default=["ALL"])
if "ALL" not in selected_providers:
    df = df[df["finalizing_provider"].isin(selected_providers)]

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
col1, col2, col3 = st.columns(3)
col1.metric("📝 Total Exams", f"{df['total_exams'].sum():,}")
col2.metric("⚖️ Total RVU", f"{df['total_rvu'].sum():,.2f}")
col3.metric("🔢 Total Points", f"{df['total_points'].sum():,.2f}")

# ---------------------------
# Pagination for Large Datasets
# ---------------------------
st.markdown("## 🔍 Data Preview")
page_size = 50  # Show 50 rows per page
num_pages = len(df) // page_size + 1
page = st.slider("📖 Select Page", 1, num_pages, 1)

start_idx = (page - 1) * page_size
end_idx = start_idx + page_size

st.dataframe(df.iloc[start_idx:end_idx])  # Display paginated data

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
       git commit -m "Optimized app for large CSV files"
       git branch -M main
       git remote add origin https://github.com/gibsona83/MILVops.git
       git push -u origin main
       ```
    2. **Deploy on Streamlit Cloud**:
       - Go to **[Streamlit Cloud](https://share.streamlit.io/)**
       - Connect your GitHub repository
       - Set `app.py` as the main entry point.
       - Ensure CSV files are **in the main directory** (or use manual upload).
    """
)

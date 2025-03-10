import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---- Page Configuration ----
st.set_page_config(page_title="MILV Productivity", layout="wide", page_icon="📊")

# ---- Constants ----
UPLOAD_FOLDER = "uploaded_data"
FILE_PATH = os.path.join(UPLOAD_FOLDER, "latest_upload.xlsx")
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", "points/half day", "procedure/half"}
COLOR_SCALE = 'Viridis'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(filepath):
    """Load and preprocess data from a saved Excel file."""
    try:
        xls = pd.ExcelFile(filepath)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Validate required columns
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None
        
        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df.dropna(subset=["date"], inplace=True)
        
        # Convert numeric columns
        numeric_cols = list(REQUIRED_COLUMNS - {"date", "author"})
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Format author names
        df["author"] = df["author"].astype(str).str.strip().str.title()

        # Ensure shift is numeric
        df["shift"] = pd.to_numeric(df["shift"], errors='coerce').fillna(0).astype(int)

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

# ---- Main Application ----
def main():
    with st.sidebar:
        st.image("milv.png", width=200)
        uploaded_file = st.file_uploader("📤 Upload File", type=["xlsx"], help="XLSX files only")

        if uploaded_file:
            # Save file to disk
            with open(FILE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state["file_uploaded"] = True  # Mark session as having a new file uploaded
            st.success("✅ File uploaded successfully!")

    # Load persisted file if available
    if os.path.exists(FILE_PATH):
        with st.spinner("📊 Loading data..."):
            df = load_data(FILE_PATH)
    else:
        st.info("📁 No file found. Please upload one.")
        return

    if df is None:
        return

    # Date range
    min_date, max_date = df["date"].min().date(), df["date"].max().date()

    # Main interface
    st.title("📈 MILV Productivity Dashboard")
    st.write(f"📂 Latest Uploaded File: `{FILE_PATH}`")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Daily Performance", "📊 Shift Analysis", "🏆 Leaderboard", 
        "⏳ Turnaround Efficiency", "📅 Trends & Reports"
    ])

    # --- 📅 Daily Performance ---
    with tab1:
        st.subheader("📅 Daily Performance")

        # Date & Provider Filters
        date_range = st.date_input("📆 Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date, key="daily_performance_date")
        selected_providers = st.multiselect("👤 Select Providers", df["author"].unique(), key="daily_performance_providers")

        # Apply Filters
        df_filtered = df[(df["date"] >= pd.Timestamp(date_range[0])) & (df["date"] <= pd.Timestamp(date_range[1]))]
        if selected_providers:
            df_filtered = df_filtered[df_filtered["author"].isin(selected_providers)]

        st.metric("Total Providers", df_filtered["author"].nunique())
        st.metric("Avg Points/HD", f"{df_filtered['points/half day'].mean():.1f}")
        st.metric("Avg Procedures/HD", f"{df_filtered['procedure/half'].mean():.1f}")

    # --- 📊 Shift-Based Productivity ---
    with tab2:
        st.subheader("📊 Shift Performance Overview")

        # Date & Provider Filters
        date_range = st.date_input("📆 Select Date Range", [min_date, max_date], key="shift_analysis_date")
        selected_providers = st.multiselect("👤 Select Providers", df["author"].unique(), key="shift_analysis_providers")

        # Apply Filters
        df_filtered = df[(df["date"] >= pd.Timestamp(date_range[0])) & (df["date"] <= pd.Timestamp(date_range[1]))]
        if selected_providers:
            df_filtered = df_filtered[df_filtered["author"].isin(selected_providers)]

        shift_avg = df_filtered.groupby("shift", as_index=False)[["points", "procedure"]].mean()
        st.plotly_chart(px.bar(shift_avg, x="shift", y=["points", "procedure"], barmode="group", title="Avg Points & Procedures per Shift"))

    # --- 🏆 Leaderboard ---
    with tab3:
        st.subheader("🏆 Top & Bottom Performers")

        # Date & Provider Filters
        date_range = st.date_input("📆 Select Date Range", [min_date, max_date], key="leaderboard_date")
        selected_providers = st.multiselect("👤 Select Providers", df["author"].unique(), key="leaderboard_providers")

    # --- ⏳ Turnaround Efficiency ---
    with tab4:
        st.subheader("⏳ Turnaround Efficiency")

        # Date & Provider Filters
        date_range = st.date_input("📆 Select Date Range", [min_date, max_date], key="turnaround_date")
        selected_providers = st.multiselect("👤 Select Providers", df["author"].unique(), key="turnaround_providers")

    # --- 📅 Trends & Reports ---
    with tab5:
        st.subheader("📅 Date-Based Trends")

        # Date & Provider Filters
        date_range = st.date_input("📆 Select Date Range", [min_date, max_date], key="trends_date")
        selected_providers = st.multiselect("👤 Select Providers", df["author"].unique(), key="trends_providers")

if __name__ == "__main__":
    main()

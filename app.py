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

    # Function to apply filters for date & provider selection
    def filter_data(df):
        col1, col2 = st.columns(2)

        # Date Selection
        with col1:
            date_range = st.date_input("📆 Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        # Provider Selection
        with col2:
            selected_providers = st.multiselect("👤 Select Providers", df["author"].unique())

        # Apply Filters
        df_filtered = df[
            (df["date"] >= pd.Timestamp(date_range[0])) & 
            (df["date"] <= pd.Timestamp(date_range[1]))
        ]
        if selected_providers:
            df_filtered = df_filtered[df_filtered["author"].isin(selected_providers)]

        return df_filtered

    # --- 📅 Daily Performance ---
    with tab1:
        st.subheader("📅 Daily Performance")
        df_filtered = filter_data(df)

        st.metric("Total Providers", df_filtered["author"].nunique())
        st.metric("Avg Points/HD", f"{df_filtered['points/half day'].mean():.1f}")
        st.metric("Avg Procedures/HD", f"{df_filtered['procedure/half'].mean():.1f}")

        st.plotly_chart(px.bar(df_filtered, x="points/half day", y="author", color="points/half day", title="Points per Half-Day"))
        st.plotly_chart(px.bar(df_filtered, x="procedure/half", y="author", color="procedure/half", title="Procedures per Half-Day"))

    # --- 📊 Shift-Based Productivity ---
    with tab2:
        st.subheader("📊 Shift-Based Performance")
        df_filtered = filter_data(df)

        shift_avg = df_filtered.groupby("shift", as_index=False)[["points", "procedure"]].mean()
        st.plotly_chart(px.bar(shift_avg, x="shift", y=["points", "procedure"], barmode="group", title="Avg Points & Procedures per Shift"))

    # --- 🏆 Leaderboard ---
    with tab3:
        st.subheader("🏆 Top & Bottom Performers")
        df_filtered = filter_data(df)

        metric = st.selectbox("📊 Select Metric:", ["points", "procedure"])
        top_5 = df_filtered.groupby("author")[metric].sum().nlargest(5).reset_index()
        bottom_5 = df_filtered.groupby("author")[metric].sum().nsmallest(5).reset_index()

        col1, col2 = st.columns(2)
        col1.subheader("🏅 Top 5 Performers")
        col1.dataframe(top_5)

        col2.subheader("📉 Bottom 5 Performers")
        col2.dataframe(bottom_5)

    # --- ⏳ Turnaround Efficiency ---
    with tab4:
        st.subheader("⏳ Turnaround Efficiency")
        df_filtered = filter_data(df)

        st.plotly_chart(px.scatter(df_filtered, x="procedure", y="points", color="shift", title="Points vs. Procedures (by Shift)"))

    # --- 📅 Trends & Reports ---
    with tab5:
        st.subheader("📅 Date-Based Trends")
        df_filtered = filter_data(df)

        df_filtered["date"] = pd.to_datetime(df_filtered["date"], errors="coerce")
        numeric_cols = df_filtered.select_dtypes(include=["number"]).columns
        df_trend = df_filtered.groupby("date")[numeric_cols].sum().reset_index()

        st.plotly_chart(px.line(df_trend, x="date", y=["points", "procedure"], title="Daily Performance Trends"))

        st.download_button("📂 Download Filtered Data", df_filtered.to_csv(index=False), file_name="filtered_data.csv", mime="text/csv")

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---- Page Configuration ----
st.set_page_config(
    page_title="MILV Productivity",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

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
    """Load and preprocess data from Excel file."""
    try:
        xls = pd.ExcelFile(filepath)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean and validate data
        df.columns = df.columns.str.strip().str.lower()
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None
        
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])
        
        numeric_cols = list(REQUIRED_COLUMNS - {"date", "author"})
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        df["author"] = df["author"].astype(str).str.strip().str.title()
        df["shift"] = pd.to_numeric(df["shift"], errors='coerce').fillna(0).astype(int)

        return df
    except Exception as e:
        st.error(f"🚨 Error processing file: {str(e)}")
        return None

def render_filters(df, min_date, max_date, key_suffix):
    """Render consistent filter components with unique keys."""
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.date_input(
            "📆 Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date,
            key=f"date_{key_suffix}"
        )
    with col2:
        selected_providers = st.multiselect(
            "👤 Providers",
            df["author"].unique(),
            key=f"providers_{key_suffix}"
        )
    return date_range, selected_providers

def filter_data(df, date_range, selected_providers):
    """Apply date and provider filters to dataframe."""
    filtered = df[
        (df["date"] >= pd.Timestamp(date_range[0])) & 
        (df["date"] <= pd.Timestamp(date_range[1]))
    ]
    if selected_providers:
        filtered = filtered[filtered["author"].isin(selected_providers)]
    return filtered

# ---- Main Application ----
def main():
    # ---- Sidebar ----
    with st.sidebar:
        st.image("milv.png", width=200)
        uploaded_file = st.file_uploader(
            "📤 Upload Excel File",
            type=["xlsx"],
            help="Upload latest productivity data"
        )

        if uploaded_file:
            with open(FILE_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state["file_uploaded"] = True
            st.success("✅ File uploaded successfully!")

    # ---- Data Loading ----
    if os.path.exists(FILE_PATH):
        with st.spinner("📊 Loading data..."):
            df = load_data(FILE_PATH)
    else:
        st.info("📁 Please upload a file to begin")
        return

    if df is None:
        return

    min_date, max_date = df["date"].min().date(), df["date"].max().date()

    # ---- Main Interface ----
    st.title("📈 MILV Productivity Dashboard")
    st.caption(f"Latest data: {max_date.strftime('%Y-%m-%d')}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Daily Performance", 
        "📊 Shift Analysis", 
        "🏆 Leaderboard", 
        "⏳ Turnaround", 
        "📈 Trends"
    ])

    # ---- Daily Performance Tab ----
    with tab1:
        st.subheader("Daily Performance Metrics")
        date_range, providers = render_filters(df, min_date, max_date, "daily")
        filtered = filter_data(df, date_range, providers)

        cols = st.columns(3)
        cols[0].metric("Total Providers", filtered["author"].nunique())
        cols[1].metric("Avg Points/HD", f"{filtered['points/half day'].mean():.1f}")
        cols[2].metric("Avg Procedures/HD", f"{filtered['procedure/half'].mean():.1f}")

        st.plotly_chart(px.scatter(
            filtered,
            x="date",
            y="points",
            color="author",
            title="Daily Points Distribution"
        ), use_container_width=True)

    # ---- Shift Analysis Tab ----
    with tab2:
        st.subheader("Shift-Based Productivity")
        date_range, providers = render_filters(df, min_date, max_date, "shift")
        filtered = filter_data(df, date_range, providers)

        shift_stats = filtered.groupby("shift").agg({
            "points": "mean",
            "procedure": "mean"
        }).reset_index()

        st.plotly_chart(px.bar(
            shift_stats,
            x="shift",
            y=["points", "procedure"],
            barmode="group",
            title="Average Productivity per Shift",
            labels={"value": "Average"}
        ), use_container_width=True)

    # ---- Leaderboard Tab ----
    with tab3:
        st.subheader("Provider Leaderboard")
        date_range, providers = render_filters(df, min_date, max_date, "leaderboard")
        filtered = filter_data(df, date_range, providers)

        if not filtered.empty:
            leaderboard = filtered.groupby("author").agg({
                "points": "sum",
                "procedure": "sum"
            }).sort_values("points", ascending=False)

            st.dataframe(
                leaderboard.style.highlight_max(axis=0),
                use_container_width=True
            )

    # ---- Remaining Tabs (Placeholder Implementation) ----
    with tab4:
        st.subheader("Turnaround Efficiency")
        date_range, providers = render_filters(df, min_date, max_date, "turnaround")
        st.info("⏳ Turnaround metrics coming soon...")

    with tab5:
        st.subheader("Long-Term Trends")
        date_range, providers = render_filters(df, min_date, max_date, "trends")
        st.info("📈 Trend analysis coming soon...")

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="MILV Daily Productivity", layout="wide")

# Constants
FILE_STORAGE_PATH = "latest_rvu.xlsx"
REQUIRED_COLUMNS = {"date", "author", "procedure", "points", "shift", 
                    "points/half day", "procedure/half"}

# ---- Helper Functions ----
@st.cache_data(show_spinner=False)
def load_data(file_path):
    """Load and preprocess data from Excel file with caching."""
    try:
        xls = pd.ExcelFile(file_path)
        df = xls.parse(xls.sheet_names[0])
        
        # Clean column names
        df.columns = df.columns.str.strip()
        lower_columns = df.columns.str.lower()
        
        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in lower_columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing).title()}")
            return None
        
        # Map actual column names
        col_map = {col.lower(): col for col in df.columns}
        
        # Process date column
        date_col = col_map["date"]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
        df.dropna(subset=[date_col], inplace=True)
        
        # Convert numeric columns
        numeric_cols = [col_map[col] for col in REQUIRED_COLUMNS if col not in ["date", "author"]]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Format author names
        author_col = col_map["author"]
        df[author_col] = df[author_col].astype(str).str.strip().str.title()
        
        return df
    except Exception as e:
        st.error(f"🚨 Error: {str(e)}")
        return None

# ---- Main Application ----
def main():
    # Sidebar with compact controls
    with st.sidebar:
        st.image("milv.png", width=200)
        st.divider()
        uploaded_file = st.file_uploader("📤 Upload RVU File", type=["xlsx"], help="Upload latest productivity data")
    
    # File handling
    if uploaded_file:
        try:
            pd.read_excel(uploaded_file).to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded successfully!")
        except Exception as e:
            st.error(f"📤 Upload failed: {str(e)}")
    
    # Load data
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("📁 Please upload a file to begin analysis")
    
    # Column mapping
    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}
    
    # Date range
    min_date, max_date = df[display_cols["date"]].min().date(), df[display_cols["date"]].max().date()
    
    # Main interface
    st.title("📊 MILV Daily Productivity Dashboard")
    tab1, tab2, tab3 = st.tabs(["📅 Daily Snapshot", "📈 Trends Explorer", "👥 Provider Analytics"])
    
    # Daily View Tab
    with tab1:
        st.subheader(f"🗓️ Daily Performance - {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df[display_cols["date"]] == pd.Timestamp(max_date)]
        
        if not df_latest.empty:
            # Compact search
            search_term = st.text_input("🔍 Search providers:", placeholder="Type to filter...")
            filtered_latest = df_latest[df_latest[display_cols["author"]].str.contains(search_term, case=False)] if search_term else df_latest
            
            # Metrics row
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Providers", len(filtered_latest[display_cols["author"]].unique()))
            m2.metric("Avg Points/HD", f"{filtered_latest[display_cols['points/half day']].mean():.1f}")
            m3.metric("Avg Procedures/HD", f"{filtered_latest[display_cols['procedure/half']].mean():.1f}")
            
            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(
                    filtered_latest.sort_values(display_cols["points/half day"], ascending=False),
                    x=display_cols["points/half day"],
                    y=display_cols["author"],
                    orientation='h',
                    color=display_cols["points/half day"],
                    color_continuous_scale='Viridis',
                    title="🏆 Points per Half-Day"
                ), use_container_width=True)
            
            with col2:
                st.plotly_chart(px.bar(
                    filtered_latest.sort_values(display_cols["procedure/half"], ascending=False),
                    x=display_cols["procedure/half"],
                    y=display_cols["author"],
                    orientation='h',
                    color=display_cols["procedure/half"],
                    color_continuous_scale='Viridis',
                    title="⚡ Procedures per Half-Day"
                ), use_container_width=True)
            
            # Data table
            with st.expander("📋 View Detailed Data", expanded=True):
                st.dataframe(filtered_latest, use_container_width=True)
    
    # Trend Analysis Tab
    with tab2:
        st.subheader("📈 Trend Explorer")
        st.caption("Analyze performance over custom time periods")
        
        # Date range picker
        col1, col2 = st.columns([1, 3])
        with col1:
            dates = st.date_input(
                "🗓️ Select Range",
                value=[max_date - pd.DateOffset(days=7), max_date],
                min_value=min_date,
                max_value=max_date
            )
        
        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date selection")
            st.stop()
        
        df_range = df[df[display_cols["date"]].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]
        
        if df_range.empty:
            st.warning("⚠️ No data in selected range")
            st.stop()
        
        # Main trend visualization
        st.plotly_chart(px.line(
            df_range,
            x=display_cols["date"],
            y=[display_cols["points/half day"], display_cols["procedure/half"]],
            title="📈 Daily Performance Trends",
            labels={"value": "Metric Value", "variable": "Metric"},
            height=400,
            markers=True
        ).update_layout(legend_title_text="Metrics"), use_container_width=True)
        
        # Provider performance
        st.subheader("👤 Provider Highlights")
        provider_summary = df_range.groupby(display_cols["author"]).agg({
            display_cols["points/half day"]: ['sum', 'mean'],
            display_cols["procedure/half"]: ['sum', 'mean']
        }).reset_index()
        provider_summary.columns = ['Author', 'Total Points', 'Avg Points/HD', 'Total Procedures', 'Avg Procedures/HD']
        
        # Compact performance cards
        tabs = st.tabs(["🏆 Points Leaders", "⚡ Procedure Leaders"])
        with tabs[0]:
            cols = st.columns(2)
            cols[0].plotly_chart(px.bar(
                provider_summary.sort_values("Total Points", ascending=False).head(5),
                x="Total Points",
                y="Author",
                orientation='h',
                title="Top 5 by Total Points"
            ), use_container_width=True)
            cols[1].plotly_chart(px.bar(
                provider_summary.sort_values("Avg Points/HD", ascending=False).head(5),
                x="Avg Points/HD",
                y="Author",
                orientation='h',
                title="Top 5 by Average Points"
            ), use_container_width=True)
        
        with tabs[1]:
            cols = st.columns(2)
            cols[0].plotly_chart(px.bar(
                provider_summary.sort_values("Total Procedures", ascending=False).head(5),
                x="Total Procedures",
                y="Author",
                orientation='h',
                title="Top 5 by Total Procedures"
            ), use_container_width=True)
            cols[1].plotly_chart(px.bar(
                provider_summary.sort_values("Avg Procedures/HD", ascending=False).head(5),
                x="Avg Procedures/HD",
                y="Author",
                orientation='h',
                title="Top 5 by Average Procedures"
            ), use_container_width=True)
    
    # Provider Analysis Tab
    with tab3:
        st.subheader("👥 Deep Dive: Provider Analytics")
        
        # Compact filter controls
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                prov_dates = st.date_input(
                    "📅 Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            with col2:
                all_providers = df[display_cols["author"]].unique()
                with st.popover("👥 Select Providers", help="Choose providers to analyze"):
                    selected_providers = st.multiselect(
                        "Providers:",
                        options=all_providers,
                        default=all_providers[:3],  # Default first 3
                        label_visibility="collapsed"
                    )
                st.caption(f"🔍 {len(selected_providers)} providers selected")
        
        # Date validation
        try:
            start_date, end_date = pd.Timestamp(prov_dates[0]), pd.Timestamp(prov_dates[1])
        except IndexError:
            st.error("❌ Please select a valid date range")
            st.stop()
        
        # Data filtering
        prov_filtered = df[
            (df[display_cols["date"]] >= start_date) & 
            (df[display_cols["date"]] <= end_date) &
            (df[display_cols["author"]].isin(selected_providers))
        ]
        
        if prov_filtered.empty:
            st.warning("⚠️ No data for selected filters")
            st.stop()
        
        # Summary metrics
        with st.container():
            cols = st.columns(4)
            cols[0].metric("Total Days", len(prov_filtered))
            cols[1].metric("📈 Avg Points/HD", f"{prov_filtered[display_cols['points/half day']].mean():.1f}")
            cols[2].metric("⚡ Avg Procedures/HD", f"{prov_filtered[display_cols['procedure/half']].mean():.1f}")
            cols[3].metric("🏅 Peak Points", prov_filtered[display_cols['points/half day']].max())
        
        # Visualizations
        with st.expander("📊 Performance Charts", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(
                    prov_filtered.groupby(display_cols["author"])[display_cols["points/half day"]].mean()
                    .sort_values(ascending=False).reset_index(),
                    x=display_cols["points/half day"],
                    y=display_cols["author"],
                    orientation='h',
                    title="🏆 Average Points per Half-Day",
                    color=display_cols["points/half day"],
                    color_continuous_scale='Viridis'
                ), use_container_width=True)
            
            with col2:
                st.plotly_chart(px.bar(
                    prov_filtered.groupby(display_cols["author"])[display_cols["procedure/half"]].mean()
                    .sort_values(ascending=False).reset_index(),
                    x=display_cols["procedure/half"],
                    y=display_cols["author"],
                    orientation='h',
                    title="⚡ Average Procedures per Half-Day",
                    color=display_cols["procedure/half"],
                    color_continuous_scale='Viridis'
                ), use_container_width=True)
        
        # Detailed data
        with st.expander("📋 View Detailed Records", expanded=False):
            search_term = st.text_input("🔍 Filter within results:", key="prov_search")
            final_data = prov_filtered[prov_filtered[display_cols["author"]].str.contains(search_term, case=False)] if search_term else prov_filtered
            st.dataframe(final_data, use_container_width=True)

if __name__ == "__main__":
    main()
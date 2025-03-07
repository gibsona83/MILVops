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
        
        # Clean column names (case-insensitive)
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
    st.sidebar.image("milv.png", width=250)
    uploaded_file = st.sidebar.file_uploader("Upload RVU File", type=["xlsx"])
    
    if uploaded_file:
        try:
            pd.read_excel(uploaded_file).to_excel(FILE_STORAGE_PATH, index=False)
            st.success("✅ File uploaded!")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
    
    df = load_data(FILE_STORAGE_PATH) if os.path.exists(FILE_STORAGE_PATH) else None
    if df is None:
        return st.info("ℹ️ Please upload a file")
    
    col_map = {col.lower(): col for col in df.columns}
    display_cols = {k: col_map[k] for k in REQUIRED_COLUMNS}
    
    min_date, max_date = df[display_cols["date"]].min().date(), df[display_cols["date"]].max().date()
    st.title("MILV Daily Productivity")
    tab1, tab2, tab3 = st.tabs(["📅 Daily View", "📈 Trend Analysis", "👤 Provider Analysis"])
    
    with tab1:
        st.subheader(f"Data for {max_date.strftime('%b %d, %Y')}")
        df_latest = df[df[display_cols["date"]] == pd.Timestamp(max_date)]
        
        if not df_latest.empty:
            st.subheader("📊 Performance")
            search = st.text_input("Search providers:")
            filtered_latest = df_latest[df_latest[display_cols["author"]].str.contains(search, case=False)] if search else df_latest
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(filtered_latest.sort_values(display_cols["points/half day"], ascending=False),
                                       x=display_cols["points/half day"],
                                       y=display_cols["author"], orientation='h',
                                       text=display_cols["points/half day"],
                                       color=display_cols["points/half day"],
                                       color_continuous_scale='Viridis',
                                       title="Points per Half-Day"),
                                use_container_width=True)
            with col2:
                st.plotly_chart(px.bar(filtered_latest.sort_values(display_cols["procedure/half"], ascending=False),
                                       x=display_cols["procedure/half"],
                                       y=display_cols["author"], orientation='h',
                                       text=display_cols["procedure/half"],
                                       color=display_cols["procedure/half"],
                                       color_continuous_scale='Viridis',
                                       title="Procedures per Half-Day"),
                                use_container_width=True)
            
            st.subheader("🔍 Detailed Data")
            st.dataframe(filtered_latest, use_container_width=True)
    
    with tab2:
        st.subheader("Date Range Analysis")
        
        if 'date_range' not in st.session_state:
            st.session_state.date_range = [max_date - pd.DateOffset(days=7), max_date]
        
        dates = st.date_input("Select Range (Start - End)", value=st.session_state.date_range,
                              min_value=min_date, max_value=max_date)
        if len(dates) != 2 or dates[0] > dates[1]:
            st.error("❌ Invalid date range")
            return
        
        df_range = df[df[display_cols["date"]].between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]
        if df_range.empty:
            st.warning("⚠️ No data in selected range")
            return
        
        st.subheader("📈 Trends")
        fig = px.line(df_range, x=display_cols["date"], y=[display_cols["points/half day"], display_cols["procedure/half"]],
                      title="Performance Trends by Date",
                      labels={display_cols["date"]: "Date", "value": "Value"},
                      height=400, markers=True)
        fig.update_layout(legend_title_text="Metrics")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📊 Provider Performance")
        provider_summary = df_range.groupby(display_cols["author"]).agg({
            display_cols["points/half day"]: ['sum', 'mean'],
            display_cols["procedure/half"]: ['sum', 'mean']
        }).reset_index()
        provider_summary.columns = ['Author', 'Total Points', 'Avg Points/HD', 'Total Procedures', 'Avg Procedures/HD']
        
        for col_name, title in [("Total Points", "Total Points per Provider"),
                                 ("Avg Points/HD", "Avg Points per Half-Day per Provider"),
                                 ("Total Procedures", "Total Procedures per Provider"),
                                 ("Avg Procedures/HD", "Avg Procedures per Half-Day per Provider")]:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(provider_summary.sort_values(col_name, ascending=True),
                                       x=col_name, y="Author", orientation='h',
                                       text=col_name, color=col_name,
                                       color_continuous_scale='Viridis',
                                       title=title),
                                use_container_width=True)
        
        st.subheader("🔍 Detailed Data")
        search_trend = st.text_input("Search providers (Trends):")
        filtered_range = df_range[df_range[display_cols["author"]].str.contains(search_trend, case=False)] if search_trend else df_range
        st.dataframe(filtered_range, use_container_width=True)

    with tab3:  # Provider Analysis Tab
        st.subheader("Provider Performance Analysis")
        
        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            prov_dates = st.date_input(
                "Select Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="prov_date_range"
            )
        with col2:
            all_providers = df[display_cols["author"]].unique()
            selected_providers = st.multiselect(
                "Select Providers:",
                options=all_providers,
                default=all_providers,
                key="prov_select"
            )
        
        # Data filtering
        try:
            start_date, end_date = pd.Timestamp(prov_dates[0]), pd.Timestamp(prov_dates[1])
        except IndexError:
            st.error("❌ Please select a valid date range")
            return
        
        prov_filtered = df[
            (df[display_cols["date"]] >= start_date) & 
            (df[display_cols["date"]] <= end_date) &
            (df[display_cols["author"]].isin(selected_providers))
        ]
        
        if prov_filtered.empty:
            return st.warning("⚠️ No data for selected filters")
        
        # Metrics
        st.markdown("### 📊 Summary Statistics")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Providers", len(selected_providers))
        with m2:
            st.metric("Avg Points/HD", f"{prov_filtered[display_cols['points/half day']].mean():.1f}")
        with m3:
            st.metric("Avg Procedures/HD", f"{prov_filtered[display_cols['procedure/half']].mean():.1f}")
        
        # Visualizations
        st.markdown("### 📈 Performance Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.bar(
                prov_filtered.groupby(display_cols["author"])[display_cols["points/half day"]].mean()
                .reset_index().sort_values(display_cols["points/half day"], ascending=False),
                x=display_cols["points/half day"],
                y=display_cols["author"],
                orientation='h',
                color=display_cols["points/half day"],
                color_continuous_scale='Viridis',
                title="Average Points per Half-Day"
            ), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(
                prov_filtered.groupby(display_cols["author"])[display_cols["procedure/half"]].mean()
                .reset_index().sort_values(display_cols["procedure/half"], ascending=False),
                x=display_cols["procedure/half"],
                y=display_cols["author"],
                orientation='h',
                color=display_cols["procedure/half"],
                color_continuous_scale='Viridis',
                title="Average Procedures per Half-Day"
            ), use_container_width=True)
        
        # Detailed data
        st.markdown("### 🔍 Detailed Provider Data")
        prov_search = st.text_input("Search within results:", key="prov_search")
        final_data = prov_filtered[prov_filtered[display_cols["author"]].str.contains(
            prov_search, case=False)] if prov_search else prov_filtered
        st.dataframe(final_data, use_container_width=True)

if __name__ == "__main__":
    main()
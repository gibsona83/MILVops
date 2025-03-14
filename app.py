import streamlit as st
import pandas as pd
import plotly.express as px

# Configuration
st.set_page_config(
    page_title="MILV Productivity Dashboard",
    layout="wide",
    page_icon="📊"
)

# Constants
DATA_CONFIG = {
    'csv_url': "https://raw.githubusercontent.com/gibsona83/MILVops/main/YTD2025PS.csv",
    'excel_url': "https://raw.githubusercontent.com/gibsona83/MILVops/main/2025_YTD.xlsx",
    'excel_sheet': 'Productivity'
}

# Cache data loading
@st.cache_data
def load_data():
    """Load and merge datasets from GitHub"""
    try:
        ps_data = pd.read_csv(DATA_CONFIG['csv_url'], encoding='latin1')
        ytd_data = pd.read_excel(DATA_CONFIG['excel_url'], sheet_name=DATA_CONFIG['excel_sheet'])
        
        # Convert datetime columns
        ps_data[['Created', 'Signed']] = ps_data[['Created', 'Signed']].apply(pd.to_datetime, errors='coerce')
        ytd_data['Final Date'] = pd.to_datetime(ytd_data['Final Date'], errors='coerce')
        
        # Calculate Turnaround Time (TAT)
        ps_data['TAT (Minutes)'] = (ps_data['Signed'] - ps_data['Created']).dt.total_seconds() / 60
        
        return ps_data, ytd_data
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return None, None

# Sidebar filters with dynamic updates
def create_sidebar_filters(df):
    """Create dynamically updating sidebar filters"""
    st.sidebar.header("🛠️ Dashboard Controls")
    with st.sidebar.expander("🔍 Filter Options", expanded=True):
        providers = st.multiselect("Select Providers:", options=sorted(df['Finalizing Provider'].dropna().unique()))
        modalities = st.multiselect("Select Modalities:", options=sorted(df['Modality'].dropna().unique()))
        shifts = st.multiselect("Select Shifts:", options=sorted(df['Shift Time Final'].dropna().unique()))
        groups = st.multiselect("Select Groups:", options=sorted(df['Radiologist Group'].dropna().unique()))
        
        date_col = 'Final Date'
        min_date, max_date = df[date_col].min(), df[date_col].max()
        start_date, end_date = st.date_input("Date Range:", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    return {
        'providers': providers,
        'modalities': modalities,
        'shifts': shifts,
        'groups': groups,
        'start_date': pd.to_datetime(start_date),
        'end_date': pd.to_datetime(end_date)
    }

# Apply filters dynamically
def apply_filters(df, filters):
    """Apply dynamic filters to the dataset"""
    filtered_df = df.copy()
    
    if filters['providers']:
        filtered_df = filtered_df[filtered_df['Finalizing Provider'].isin(filters['providers'])]
    if filters['modalities']:
        filtered_df = filtered_df[filtered_df['Modality'].isin(filters['modalities'])]
    if filters['shifts']:
        filtered_df = filtered_df[filtered_df['Shift Time Final'].isin(filters['shifts'])]
    if filters['groups']:
        filtered_df = filtered_df[filtered_df['Radiologist Group'].isin(filters['groups'])]
    
    # Date range filter
    filtered_df = filtered_df[(filtered_df['Final Date'] >= filters['start_date']) & (filtered_df['Final Date'] <= filters['end_date'])]
    
    return filtered_df

# Main app
def main():
    st.title("🏥 MILV Radiology Productivity Dashboard")
    
    with st.spinner("Loading data..."):
        ps_data, ytd_data = load_data()
    
    if ps_data is None or ytd_data is None:
        st.warning("⚠️ Data not available. Please check your connection.")
        return
    
    # Create dynamically updating sidebar filters
    filters = create_sidebar_filters(ytd_data)
    filtered_data = apply_filters(ytd_data, filters)
    
    if filtered_data.empty:
        st.warning("No data matching selected filters")
        return
    
    # Weekly Trends Adjustment: Sunday-Saturday Order
    day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    filtered_data['Day of Week'] = pd.Categorical(
        filtered_data['Final Date'].dt.day_name(), categories=day_order, ordered=True
    )
    
    weekly_summary = filtered_data.groupby('Day of Week', observed=False).agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    
    # Sorting Weekly Data by Correct Order
    weekly_summary = weekly_summary.sort_values(by='Day of Week')
    
    # Key Metrics
    st.header("📊 Performance Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", filtered_data['Accession'].nunique())
    with col2:
        st.metric("Total RVUs", f"{filtered_data['RVU'].sum():,.1f}")
    with col3:
        st.metric("Total Points", f"{filtered_data['Points'].sum():,.1f}")
    
    # Weekly Case Trends
    with st.expander("📅 Weekly Trends Analysis", expanded=True):
        fig_weekly = px.line(weekly_summary, x='Day of Week', y='Cases', title="Weekly Case Trends", markers=True)
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Modality Insights (Sorted Descending)
    st.subheader("📊 Modality Insights")
    modality_summary = filtered_data.groupby('Modality').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index().sort_values(by='Cases', ascending=False)
    fig_modality = px.bar(modality_summary, x='Modality', y='Cases', title="Case Distribution by Modality", color='Total_RVU')
    st.plotly_chart(fig_modality, use_container_width=True)
    
if __name__ == "__main__":
    main()
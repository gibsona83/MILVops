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
        
        # Data processing
        time_cols = {'ps': ['Created', 'Signed'], 'ytd': ['Final Date']}
        ps_data[time_cols['ps']] = ps_data[time_cols['ps']].apply(pd.to_datetime, errors='coerce')
        ytd_data[time_cols['ytd']] = ytd_data[time_cols['ytd']].apply(pd.to_datetime, errors='coerce')
        ps_data['TAT (Minutes)'] = (ps_data['Signed'] - ps_data['Created']).dt.total_seconds() / 60
        
        return ps_data, ytd_data
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return None, None

def create_summary(df, group_col, metrics):
    """Create aggregated summary statistics"""
    return df.groupby(group_col).agg(**{
        'Cases': ('Accession', 'count'),
        'Total RVUs': ('RVU', 'sum'),
        'Total Points': ('Points', 'sum')
    }).reset_index()

def create_visualization(df, x_col, y_col, title, viz_type='bar', color_col=None):
    """Create Plotly visualization with consistent styling"""
    color_scale = px.colors.sequential.Blues
    fig = None
    
    if viz_type == 'bar':
        fig = px.bar(df, x=x_col, y=y_col, title=title,
                     color=color_col or y_col, color_continuous_scale=color_scale)
    elif viz_type == 'line':
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
    elif viz_type == 'pie':
        fig = px.pie(df, names=x_col, values=y_col, title=title)
    
    if fig:
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2c3e50'),
            height=500
        )
    return fig

def create_sidebar_filters(df):
    """Create sidebar filters and return filter parameters"""
    st.sidebar.header("🛠️ Dashboard Controls")
    
    with st.sidebar.expander("🔍 Filter Options", expanded=True):
        providers = st.multiselect("Select Providers:", df['Finalizing Provider'].unique())
        modalities = st.multiselect("Select Modalities:", df['Modality'].unique())
        shifts = st.multiselect("Select Shifts:", df['Shift Time Final'].unique())
        groups = st.multiselect("Select Groups:", df['Radiologist Group'].unique())
        
        date_col = 'Final Date'
        min_date, max_date = df[date_col].min(), df[date_col].max()
        start_date, end_date = st.date_input("Date Range:", [min_date, max_date])
    
    return {
        'providers': providers,
        'modalities': modalities,
        'shifts': shifts,
        'groups': groups,
        'start_date': pd.to_datetime(start_date),
        'end_date': pd.to_datetime(end_date)
    }

def apply_filters(df, filters):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    # Provider filter
    if filters['providers']:
        filtered_df = filtered_df[filtered_df['Finalizing Provider'].isin(filters['providers'])]
    
    # Modality filter
    if filters['modalities']:
        filtered_df = filtered_df[filtered_df['Modality'].isin(filters['modalities'])]
    
    # Shift filter
    if filters['shifts']:
        filtered_df = filtered_df[filtered_df['Shift Time Final'].isin(filters['shifts'])]
    
    # Group filter
    if filters['groups']:
        filtered_df = filtered_df[filtered_df['Radiologist Group'].isin(filters['groups'])]
    
    # Date filter
    filtered_df = filtered_df[
        (filtered_df['Final Date'] >= filters['start_date']) & 
        (filtered_df['Final Date'] <= filters['end_date'])
    ]
    
    return filtered_df

# Main app
def main():
    st.title("🏥 MILV Radiology Productivity Dashboard")
    
    with st.spinner("Loading data..."):
        ps_data, ytd_data = load_data()
    
    if ps_data is None or ytd_data is None:
        st.warning("⚠️ Data not available. Please check your connection.")
        return
    
    # Create sidebar filters
    filters = create_sidebar_filters(ytd_data)
    filtered_data = apply_filters(ytd_data, filters)
    
    if filtered_data.empty:
        st.warning("No data matching selected filters")
        return
    
    # Key Metrics
    st.header("📊 Performance Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", filtered_data['Accession'].nunique())
    with col2:
        st.metric("Total RVUs", f"{filtered_data['RVU'].sum():,.1f}")
    with col3:
        st.metric("Total Points", f"{filtered_data['Points'].sum():,.1f}")
    
    # Main visualizations
    tab1, tab2, tab3 = st.tabs(["Provider Analysis", "Modality Trends", "Group Comparison"])
    
    with tab1:
        st.subheader("🧑⚕️ Provider Performance")
        provider_summary = create_summary(filtered_data, 'Finalizing Provider', ['RVU', 'Points'])
        st.dataframe(
            provider_summary.style.format({'Total RVUs': '{:,.1f}', 'Total Points': '{:,.1f}'}),
            use_container_width=True
        )
        
    with tab2:
        st.subheader("📷 Modality Insights")
        modality_summary = create_summary(filtered_data, 'Modality', ['RVU', 'Points'])
        fig = create_visualization(modality_summary, 'Modality', 'Cases', 
                                  "Case Distribution by Modality", color_col='Total RVUs')
        st.plotly_chart(fig, use_container_width=True)
        
    with tab3:
        st.subheader("👥 Group Comparison")
        group_summary = create_summary(filtered_data, 'Radiologist Group', ['RVU', 'Points'])
        fig = create_visualization(group_summary, 'Radiologist Group', 'Cases',
                                  "Case Distribution by Group", viz_type='pie')
        st.plotly_chart(fig, use_container_width=True)
    
    # Additional insights
    with st.expander("📅 Weekly Trends Analysis", expanded=True):
        filtered_data['Day of Week'] = filtered_data['Final Date'].dt.day_name()
        weekly_summary = create_summary(filtered_data, 'Day of Week', ['RVU', 'Points'])
        fig = create_visualization(weekly_summary, 'Day of Week', 'Cases', 
                                  "Weekly Case Trends", viz_type='line')
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
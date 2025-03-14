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

# Custom styling
COLOR_SCALE = px.colors.sequential.Blues
TEMPLATE = 'plotly_white'
DAY_ORDER = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

@st.cache_data
def load_data():
    """Load and process data from GitHub"""
    try:
        ps_data = pd.read_csv(DATA_CONFIG['csv_url'], encoding='latin1')
        ytd_data = pd.read_excel(DATA_CONFIG['excel_url'], sheet_name=DATA_CONFIG['excel_sheet'])
        
        # Convert datetime columns
        ps_data[['Created', 'Signed']] = ps_data[['Created', 'Signed']].apply(pd.to_datetime, errors='coerce')
        ytd_data['Final Date'] = pd.to_datetime(ytd_data['Final Date'], errors='coerce')
        
        # Calculate TAT
        ps_data['TAT (Minutes)'] = (ps_data['Signed'] - ps_data['Created']).dt.total_seconds() / 60
        
        return ps_data, ytd_data
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return None, None

def create_visualization(df, x, y, title, viz_type='bar', sort=True, color=None):
    """Create styled visualization with proper sorting"""
    # Sort data for bar charts
    if sort and viz_type == 'bar':
        df = df.sort_values(by=y, ascending=False)
    
    # Create chart
    if viz_type == 'bar':
        fig = px.bar(df, x=x, y=y, title=title, color=color or y,
                     color_continuous_scale=COLOR_SCALE, text=y)
        # Add text labels only for bar charts
        fig.update_traces(
            texttemplate='%{text:,.0f}', 
            textposition='outside',
            marker_line_color='rgba(0,0,0,0.3)',
            marker_line_width=1
        )
    elif viz_type == 'line':
        fig = px.line(df, x=x, y=y, title=title, markers=True)
    else:
        fig = px.pie(df, names=x, values=y, title=title)
    
    # Apply universal styling
    fig.update_layout(
        template=TEMPLATE,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12, color="#2c3e50"),
        height=500,
        margin=dict(r=40)
    )
    
    # Axis formatting
    if viz_type in ['bar', 'line']:
        fig.update_yaxes(title_text="", showgrid=False)
        fig.update_xaxes(title_text="", categoryorder='array' if sort else None)
    
    return fig

def main():
    st.title("🏥 MILV Radiology Productivity Dashboard")
    
    # Load data
    with st.spinner("Loading data..."):
        ps_data, ytd_data = load_data()
    
    if ps_data is None or ytd_data is None:
        st.warning("⚠️ Data not available. Please check your connection.")
        return
    
    # Sidebar filters
    st.sidebar.header("🛠️ Dashboard Controls")
    with st.sidebar.expander("🔍 Filter Options", expanded=True):
        providers = st.multiselect("Select Providers:", 
                                  options=sorted(ytd_data['Finalizing Provider'].dropna().unique()))
        modalities = st.multiselect("Select Modalities:",
                                  options=sorted(ytd_data['Modality'].dropna().unique()))
        shifts = st.multiselect("Select Shifts:",
                              options=sorted(ytd_data['Shift Time Final'].dropna().unique()))
        groups = st.multiselect("Select Groups:",
                               options=sorted(ytd_data['Radiologist Group'].dropna().unique()))
        
        date_range = st.date_input("Date Range:", 
                                 [ytd_data['Final Date'].min(), ytd_data['Final Date'].max()],
                                 min_value=ytd_data['Final Date'].min(),
                                 max_value=ytd_data['Final Date'].max())
    
    # Filter data
    filtered_data = ytd_data[
        (ytd_data['Final Date'] >= pd.to_datetime(date_range[0])) &
        (ytd_data['Final Date'] <= pd.to_datetime(date_range[1]))
    ].copy()
    
    if providers:
        filtered_data = filtered_data[filtered_data['Finalizing Provider'].isin(providers)]
    if modalities:
        filtered_data = filtered_data[filtered_data['Modality'].isin(modalities)]
    if shifts:
        filtered_data = filtered_data[filtered_data['Shift Time Final'].isin(shifts)]
    if groups:
        filtered_data = filtered_data[filtered_data['Radiologist Group'].isin(groups)]
    
    if filtered_data.empty:
        st.warning("No data matching selected filters")
        return
    
    # Weekly processing
    filtered_data['Day of Week'] = pd.Categorical(
        filtered_data['Final Date'].dt.day_name(),
        categories=DAY_ORDER,
        ordered=True
    )
    
    # Key Metrics
    st.header("📊 Performance Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", f"{filtered_data['Accession'].nunique():,}")
    with col2:
        st.metric("Total RVUs", f"{filtered_data['RVU'].sum():,.1f}")
    with col3:
        st.metric("Total Points", f"{filtered_data['Points'].sum():,.1f}")
    
    # Main Visualizations
    with st.container():
        st.subheader("📈 Core Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            # Weekly Trends
            weekly_summary = filtered_data.groupby('Day of Week', observed=False).agg(
                Cases=('Accession', 'count')
            ).reset_index()
            
            fig_weekly = create_visualization(
                weekly_summary,
                x='Day of Week',
                y='Cases',
                title="<b>Weekly Trends</b> (Sunday-Saturday)",
                viz_type='line',
                sort=False
            )
            fig_weekly.update_xaxes(categoryorder='array', categoryarray=DAY_ORDER)
            st.plotly_chart(fig_weekly, use_container_width=True)
        
        with col2:
            # Modality Distribution
            modality_summary = filtered_data.groupby('Modality').agg(
                Cases=('Accession', 'count'),
                Total_RVU=('RVU', 'sum')
            ).reset_index()
            
            fig_modality = create_visualization(
                modality_summary,
                x='Modality',
                y='Cases',
                color='Total_RVU',
                title="<b>Modality Distribution</b>"
            )
            fig_modality.update_layout(coloraxis_colorbar=dict(title="RVUs"))
            st.plotly_chart(fig_modality, use_container_width=True)
    
    # Provider Performance
    with st.expander("🧑⚕️ Detailed Provider Performance", expanded=True):
        provider_summary = filtered_data.groupby('Finalizing Provider').agg(
            Cases=('Accession', 'count'),
            Avg_RVU=('RVU', 'mean')
        ).reset_index()
        
        fig_providers = create_visualization(
            provider_summary,
            x='Finalizing Provider',
            y='Cases',
            color='Avg_RVU',
            title="<b>Provider Performance</b> (Cases with Average RVUs)"
        )
        fig_providers.update_layout(
            xaxis_tickangle=-45,
            coloraxis_colorbar=dict(title="Avg RVUs")
        )
        st.plotly_chart(fig_providers, use_container_width=True)

if __name__ == "__main__":
    main()
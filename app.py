import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Page Configuration
st.set_page_config(
    page_title="Radiology Productivity Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = pd.DataFrame()

# Helper Functions
@st.cache_data(ttl=3600)
def load_data(uploaded_file, file_type):
    """Load and cache data files"""
    try:
        if file_type == 'csv':
            return pd.read_csv(uploaded_file)
        elif file_type == 'excel':
            return pd.read_excel(uploaded_file, sheet_name="Productivity")
    except Exception as e:
        st.error(f"Error loading {file_type} file: {str(e)}")
        return pd.DataFrame()

def merge_data(csv_df, excel_df):
    """Merge CSV and Excel data with validation"""
    required_columns = {'Accession', 'Created', 'Signed', 'Final Date', 
                       'RVU', 'Modality', 'Finalizing Provider', 'Shift Time Final'}
    
    for df, name in [(csv_df, 'CSV'), (excel_df, 'Excel')]:
        missing = required_columns - set(df.columns)
        if missing:
            st.error(f"Missing columns in {name} data: {', '.join(missing)}")
            return pd.DataFrame()
    
    merged = pd.merge(csv_df, excel_df, on="Accession", how="inner")
    merged = merged.loc[:,~merged.columns.duplicated()]  # Remove duplicate columns
    
    # Convert datetime columns
    date_cols = ['Created', 'Signed', 'Final Date']
    merged[date_cols] = merged[date_cols].apply(pd.to_datetime, errors='coerce')
    
    # Calculate turnaround time
    merged['Turnaround Time (min)'] = (merged['Final Date'] - merged['Created']).dt.total_seconds() / 60
    merged['Final Date'] = merged['Final Date'].dt.date
    
    return merged

# Sidebar File Upload
with st.sidebar:
    st.header("Data Management")
    csv_file = st.file_uploader("Upload CSV File", type=["csv"])
    excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if csv_file and excel_file:
        csv_df = load_data(csv_file, 'csv')
        excel_df = load_data(excel_file, 'excel')
        st.session_state.merged_data = merge_data(csv_df, excel_df)
    
    st.header("Filters")
    if not st.session_state.merged_data.empty:
        modalities = st.multiselect(
            "Select Modalities",
            options=st.session_state.merged_data['Modality'].unique(),
            default=st.session_state.merged_data['Modality'].unique()
        )
        providers = st.multiselect(
            "Select Providers",
            options=st.session_state.merged_data['Finalizing Provider'].unique(),
            default=st.session_state.merged_data['Finalizing Provider'].unique()
        )
        date_range = st.date_input(
            "Date Range",
            value=(
                st.session_state.merged_data['Final Date'].min(),
                st.session_state.merged_data['Final Date'].max()
            )
        )

# Main Dashboard
st.title("🏥 Radiology Productivity Dashboard")

if not st.session_state.merged_data.empty:
    # Apply Filters
    filtered_df = st.session_state.merged_data[
        (st.session_state.merged_data['Modality'].isin(modalities)) &
        (st.session_state.merged_data['Finalizing Provider'].isin(providers)) &
        (st.session_state.merged_data['Final Date'].between(*date_range))
    ]

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Cases", filtered_df.shape[0], help="Total number of radiology cases")
    with col2:
        avg_time = filtered_df['Turnaround Time (min)'].mean()
        st.metric("Avg Turnaround", f"{avg_time:.1f} min", help="Average time from creation to finalization")
    with col3:
        total_rvu = filtered_df['RVU'].sum()
        st.metric("Total RVUs", f"{total_rvu:,.1f}", help="Total Relative Value Units")
    with col4:
        avg_points = filtered_df['Points'].mean()
        st.metric("Avg Points/Case", f"{avg_points:.1f}", help="Average points per case")

    # Visualization Tabs
    tab1, tab2, tab3 = st.tabs(["Trend Analysis", "Provider Performance", "Modality Insights"])

    with tab1:
        # Time Series Analysis
        st.subheader("Case Volume Over Time")
        daily_cases = filtered_df.groupby('Final Date').size().reset_index(name='Cases')
        fig = px.area(daily_cases, x='Final Date', y='Cases',
                     template="plotly_white",
                     labels={'Final Date': 'Date', 'Cases': 'Number of Cases'},
                     height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Provider Performance
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("RVU by Provider")
            provider_rvu = filtered_df.groupby('Finalizing Provider')['RVU'].sum().nlargest(10)
            fig = px.bar(provider_rvu, orientation='h',
                        labels={'value': 'Total RVU', 'index': 'Provider'},
                        color=provider_rvu.values,
                        color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Turnaround Time Distribution")
            fig = px.box(filtered_df, x='Finalizing Provider', y='Turnaround Time (min)',
                        points="all", hover_data=['Accession'])
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Modality Analysis
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Modality Distribution")
            modality_counts = filtered_df['Modality'].value_counts()
            fig = px.pie(modality_counts, names=modality_counts.index,
                        values=modality_counts.values,
                        hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Shift Productivity")
            shift_perf = filtered_df.groupby('Shift Time Final')['Points'].sum()
            fig = px.bar(shift_perf, color=shift_perf.index,
                        labels={'value': 'Total Points', 'index': 'Shift Time'},
                        title="Productivity by Shift")
            st.plotly_chart(fig, use_container_width=True)

    # Data Export
    st.divider()
    st.subheader("Data Export")
    csv = filtered_df.to_csv(index=False).encode()
    st.download_button(
        "📥 Download Filtered Data",
        data=csv,
        file_name="radiology_data.csv",
        mime="text/csv",
        help="Export filtered data as CSV file"
    )

else:
    st.info("👋 Please upload both CSV and Excel files to begin analysis")

# Style Enhancements
st.markdown("""
<style>
    [data-testid=stMetric] {
        background-color: #F0F2F6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    [data-testid=stMetricLabel] {
        font-size: 1.1rem !important;
    }
    [data-testid=stMetricValue] {
        font-size: 1.4rem !important;
        font-weight: bold !important;
    }
    .stPlotlyChart {
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)
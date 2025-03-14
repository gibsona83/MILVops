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
        fig = px.bar(df, x=x, y=y, title=title, color=color or y
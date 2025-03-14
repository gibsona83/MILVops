import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# GitHub raw file URLs
GITHUB_CSV_URL = "https://raw.githubusercontent.com/gibsona83/MILVops/main/YTD2025PS.csv"
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/gibsona83/MILVops/main/2025_YTD.xlsx"

# Title and layout setup
st.set_page_config(page_title="MILV Productivity Dashboard", layout="wide")
st.title("📊 MILV Radiology Productivity Dashboard")

# Load data from GitHub
def load_data():
    try:
        df_ps = pd.read_csv(GITHUB_CSV_URL, encoding='latin1')
        df_ytd = pd.read_excel(GITHUB_EXCEL_URL, sheet_name='Productivity')
        return df_ps, df_ytd
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

# Fetch data
df_ps, df_ytd = load_data()

if df_ps is not None and df_ytd is not None:
    # Convert time columns to datetime
    df_ps['Created'] = pd.to_datetime(df_ps['Created'], errors='coerce')
    df_ps['Signed'] = pd.to_datetime(df_ps['Signed'], errors='coerce')
    df_ytd['Final Date'] = pd.to_datetime(df_ytd['Final Date'], errors='coerce')
    
    # Calculate Turnaround Time (TAT)
    df_ps['TAT (Minutes)'] = (df_ps['Signed'] - df_ps['Created']).dt.total_seconds() / 60
    
    # Sidebar filters
    st.sidebar.header("Filters")
    provider_filter = st.sidebar.multiselect("Select Providers", df_ytd['Finalizing Provider'].unique())
    modality_filter = st.sidebar.multiselect("Select Modalities", df_ytd['Modality'].unique())
    shift_filter = st.sidebar.multiselect("Select Shifts", df_ytd['Shift Time Final'].unique())
    group_filter = st.sidebar.multiselect("Select Radiologist Group", df_ytd['Radiologist Group'].unique())
    
    # Date filter
    start_date = st.sidebar.date_input("Start Date", df_ytd['Final Date'].min())
    end_date = st.sidebar.date_input("End Date", df_ytd['Final Date'].max())
    
    # Apply filters
    df_filtered = df_ytd.copy()
    if provider_filter:
        df_filtered = df_filtered[df_filtered['Finalizing Provider'].isin(provider_filter)]
    if modality_filter:
        df_filtered = df_filtered[df_filtered['Modality'].isin(modality_filter)]
    if shift_filter:
        df_filtered = df_filtered[df_filtered['Shift Time Final'].isin(shift_filter)]
    if group_filter:
        df_filtered = df_filtered[df_filtered['Radiologist Group'].isin(group_filter)]
    df_filtered = df_filtered[(df_filtered['Final Date'] >= pd.to_datetime(start_date)) & (df_filtered['Final Date'] <= pd.to_datetime(end_date))]
    
    # Productivity summary
    st.subheader("📈 Provider Productivity Overview")
    provider_summary = df_filtered.groupby('Finalizing Provider').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    st.dataframe(provider_summary, use_container_width=True)
    
    # Modality analysis
    st.subheader("🔍 Modality Statistics")
    modality_summary = df_filtered.groupby('Modality').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_modality = px.bar(modality_summary, x='Modality', y='Cases', title="Case Volume by Modality", color='Total_RVU')
    st.plotly_chart(fig_modality, use_container_width=True)
    
    # Shift-based analysis
    st.subheader("⏳ Productivity by Shift")
    shift_summary = df_filtered.groupby('Shift Time Final').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_shift = px.bar(shift_summary, x='Shift Time Final', y='Cases', title="Case Volume by Shift", color='Total_RVU')
    st.plotly_chart(fig_shift, use_container_width=True)
    
    # Weekly trends
    df_filtered['Day of Week'] = df_filtered['Final Date'].dt.day_name()
    weekly_summary = df_filtered.groupby('Day of Week').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_weekly = px.line(weekly_summary, x='Day of Week', y='Cases', title="Weekly Case Trends", markers=True)
    st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Group comparison (MILV vs. vRad)
    st.subheader("🏥 Radiologist Group Comparison")
    group_summary = df_filtered.groupby('Radiologist Group').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_group = px.pie(group_summary, names='Radiologist Group', values='Cases', title="Case Distribution by Group")
    st.plotly_chart(fig_group, use_container_width=True)
else:
    st.warning("Unable to load data. Please check the GitHub repository.")

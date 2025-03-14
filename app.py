import streamlit as st
import pandas as pd
import plotly.express as px

# Title and layout setup
st.set_page_config(page_title="MILV Productivity Dashboard", layout="wide")
st.title("📊 MILV Radiology Productivity Dashboard")
st.sidebar.header("Upload Data Files")

# File uploaders
ps_file = st.sidebar.file_uploader("Upload YTD2025PS.csv", type=["csv"])
ytd_file = st.sidebar.file_uploader("Upload 2025_YTD.xlsx", type=["xlsx"])

if ps_file and ytd_file:
    # Load data
    df_ps = pd.read_csv(ps_file, encoding='latin1')
    df_ytd = pd.read_excel(ytd_file, sheet_name='Productivity')
    
    # Convert time columns to datetime
    df_ps['Created'] = pd.to_datetime(df_ps['Created'], errors='coerce')
    df_ps['Signed'] = pd.to_datetime(df_ps['Signed'], errors='coerce')
    df_ytd['Final Date'] = pd.to_datetime(df_ytd['Final Date'], errors='coerce')
    
    # Calculate Turnaround Time (TAT)
    df_ps['TAT (Minutes)'] = (df_ps['Signed'] - df_ps['Created']).dt.total_seconds() / 60
    
    # Sidebar filters
    provider_filter = st.sidebar.multiselect("Select Providers", df_ytd['Finalizing Provider'].unique())
    modality_filter = st.sidebar.multiselect("Select Modalities", df_ytd['Modality'].unique())
    shift_filter = st.sidebar.multiselect("Select Shifts", df_ytd['Shift Time Final'].unique())
    
    # Apply filters
    if provider_filter:
        df_ytd = df_ytd[df_ytd['Finalizing Provider'].isin(provider_filter)]
    if modality_filter:
        df_ytd = df_ytd[df_ytd['Modality'].isin(modality_filter)]
    if shift_filter:
        df_ytd = df_ytd[df_ytd['Shift Time Final'].isin(shift_filter)]
    
    # Productivity summary
    st.subheader("📈 Provider Productivity Overview")
    provider_summary = df_ytd.groupby('Finalizing Provider').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    st.dataframe(provider_summary, use_container_width=True)
    
    # Modality analysis
    st.subheader("🔍 Modality Statistics")
    modality_summary = df_ytd.groupby('Modality').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_modality = px.bar(modality_summary, x='Modality', y='Cases', title="Case Volume by Modality", color='Total_RVU')
    st.plotly_chart(fig_modality, use_container_width=True)
    
    # Shift-based analysis
    st.subheader("⏳ Productivity by Shift")
    shift_summary = df_ytd.groupby('Shift Time Final').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_shift = px.bar(shift_summary, x='Shift Time Final', y='Cases', title="Case Volume by Shift", color='Total_RVU')
    st.plotly_chart(fig_shift, use_container_width=True)
    
    # Weekly trends
    df_ytd['Day of Week'] = df_ytd['Final Date'].dt.day_name()
    weekly_summary = df_ytd.groupby('Day of Week').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_weekly = px.line(weekly_summary, x='Day of Week', y='Cases', title="Weekly Case Trends", markers=True)
    st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Group comparison (MILV vs. vRad)
    st.subheader("🏥 Radiologist Group Comparison")
    group_summary = df_ytd.groupby('Radiologist Group').agg(
        Cases=('Accession', 'count'),
        Total_RVU=('RVU', 'sum'),
        Total_Points=('Points', 'sum')
    ).reset_index()
    fig_group = px.pie(group_summary, names='Radiologist Group', values='Cases', title="Case Distribution by Group")
    st.plotly_chart(fig_group, use_container_width=True)
else:
    st.warning("Please upload both data files to generate insights.")

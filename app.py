import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set Streamlit Page Config (MUST be the first Streamlit command)
st.set_page_config(page_title="MILV Executive Dashboard", layout="wide")

# Load data files with absolute paths
@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)  # Get current directory where app.py is
    data_files = {
        "physician_kpi": os.path.join(base_path, "physician_kpi.csv"),
        "physician_time_series": os.path.join(base_path, "physician_time_series.csv"),
        "modality_distribution": os.path.join(base_path, "modality_distribution.csv"),
        "physician_modality": os.path.join(base_path, "physician_modality.csv"),
        "day_of_week_workload": os.path.join(base_path, "day_of_week_workload.csv"),
        "hourly_workload": os.path.join(base_path, "hourly_workload.csv"),
    }
    
    data = {}
    for key, file in data_files.items():
        if os.path.exists(file):
            data[key] = pd.read_csv(file)
    
    # Ensure correct data types
    for key, df in data.items():
        if "Total_Exams" in df.columns:
            df["Total_Exams"] = pd.to_numeric(df["Total_Exams"], errors="coerce")
        if "Total_RVU" in df.columns:
            df["Total_RVU"] = pd.to_numeric(df["Total_RVU"], errors="coerce")
        if "Total_Points" in df.columns:
            df["Total_Points"] = pd.to_numeric(df["Total_Points"], errors="coerce")
        if "Month" in df.columns:
            df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
    
    return data

data = load_data()

# Apply MILV theme and logo
logo_path = os.path.join(os.path.dirname(__file__), "milv.png")
st.sidebar.image(logo_path, use_container_width=True)
st.sidebar.title("Navigation")

# Sidebar Navigation
page = st.sidebar.radio("Go to", ["Overview", "Physician Performance", "Modality Analysis", "Workload Trends", "Data Explorer"])

if page == "Overview":
    st.title("📊 Executive Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Exams", f"{data['physician_kpi']['Total_Exams'].sum():,}")
    col2.metric("Total RVU", f"{data['physician_kpi']['Total_RVU'].sum():,.2f}")
    col3.metric("Total Points", f"{data['physician_kpi']['Total_Points'].sum():,.2f}")
    
    st.subheader("Workload Trends by Day of Week")
    fig = px.bar(data['day_of_week_workload'].sort_values(by="Total Exams", ascending=False), x="Day of Week", y="Total Exams", text="Total Exams", color="Total Exams")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Hourly Workload Distribution")
    fig = px.line(data['hourly_workload'].sort_values(by="Hour", ascending=True), x="Hour", y="Total Exams", markers=True)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Physician Performance":
    st.title("👨‍⚕️ Physician Performance")
    
    physician_filter = st.multiselect("Select Physicians", data['physician_kpi']['Finalizing Provider'].unique(), default=[])
    filtered_data = data['physician_kpi'][data['physician_kpi']['Finalizing Provider'].isin(physician_filter)] if physician_filter else data['physician_kpi']
    
    st.subheader("Top Physicians by Total RVU")
    fig = px.bar(filtered_data.nlargest(10, 'Total_RVU'), x="Finalizing Provider", y="Total_RVU", text="Total_RVU", color="Total_RVU")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Physician Workload Over Time")
    time_series_filtered = data['physician_time_series'][data['physician_time_series']['Month'].dt.year == 2024]  # Ensure only CY2024 data
    fig = px.line(time_series_filtered.sort_values(by="Month", ascending=True), x="Month", y="Total_RVU", color="Finalizing Provider", markers=True)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Workload Trends":
    st.title("📈 Workload Trends")
    
    start_date, end_date = st.sidebar.date_input("Select Date Range", [data['physician_time_series']['Month'].min(), data['physician_time_series']['Month'].max()])
    workload_filtered = data['physician_time_series'][(data['physician_time_series']['Month'] >= pd.to_datetime(start_date)) & (data['physician_time_series']['Month'] <= pd.to_datetime(end_date))]
    
    st.subheader("Exams Over Time (CY2024 Monthly)")
    fig = px.line(workload_filtered.sort_values(by="Month", ascending=True), x="Month", y="Total_Exams", color="Finalizing Provider", markers=True)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Data Explorer":
    st.title("🔍 Data Explorer")
    
    st.subheader("Physician KPI Data")
    st.dataframe(data['physician_kpi'].style.set_sticky())
    search_term = st.text_input("Search Physician")
    if search_term:
        filtered_df = data['physician_kpi'][data['physician_kpi']['Finalizing Provider'].str.contains(search_term, case=False, na=False)]
        st.dataframe(filtered_df)
    else:
        st.dataframe(data['physician_kpi'])

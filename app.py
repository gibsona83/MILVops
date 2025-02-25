
import streamlit as st
import pandas as pd
import plotly.express as px

# Load data files
@st.cache_data
def load_data():
    data_files = {
        "physician_kpi": "physician_kpi.csv",
        "physician_time_series": "physician_time_series.csv",
        "modality_distribution": "modality_distribution.csv",
        "physician_modality": "physician_modality.csv",
        "day_of_week_workload": "day_of_week_workload.csv",
        "hourly_workload": "hourly_workload.csv",
    }
    
    data = {}
    for key, file in data_files.items():
        data[key] = pd.read_csv(file)
    return data

data = load_data()

# Streamlit UI Configuration
st.set_page_config(page_title="MILV Executive Dashboard", layout="wide")

# Apply MILV theme and logo
logo_path = "milv.png"
st.sidebar.image(logo_path, use_column_width=True)
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
    fig = px.bar(data['day_of_week_workload'], x="Day of Week", y="Total Exams", text="Total Exams", color="Total Exams")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Hourly Workload Distribution")
    fig = px.line(data['hourly_workload'], x="Hour", y="Total Exams", markers=True)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Physician Performance":
    st.title("👨‍⚕️ Physician Performance")
    
    st.subheader("Top Physicians by Total RVU")
    top_physicians = data['physician_kpi'].nlargest(10, 'Total_RVU')
    fig = px.bar(top_physicians, x="Finalizing Provider", y="Total_RVU", text="Total_RVU", color="Total_RVU")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Physician Workload Over Time")
    fig = px.line(data['physician_time_series'], x="Month", y="Total_RVU", color="Finalizing Provider", markers=True)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Modality Analysis":
    st.title("📟 Modality Analysis")
    
    st.subheader("Total Exams by Modality")
    fig = px.pie(data['modality_distribution'], names="Modality", values="Total Exams", title="Modality Distribution")
    st.plotly_chart(fig)
    
    st.subheader("Physician-Specific Modality Breakdown")
    fig = px.bar(data['physician_modality'], x="Physician", y="Exam Count", color="Modality", text="Exam Count")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Workload Trends":
    st.title("📈 Workload Trends")
    
    st.subheader("Exams Over Time")
    fig = px.line(data['physician_time_series'], x="Month", y="Total_Exams", color="Finalizing Provider", markers=True)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Data Explorer":
    st.title("🔍 Data Explorer")
    
    st.subheader("Physician KPI Data")
    st.dataframe(data['physician_kpi'])
    
    st.subheader("Physician Time Series Data")
    st.dataframe(data['physician_time_series'])
    
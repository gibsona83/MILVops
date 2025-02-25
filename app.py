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
        if not os.path.exists(file):
            st.error(f"⚠️ Missing file: {file}")
        else:
            data[key] = pd.read_csv(file)
            st.success(f"✅ Loaded {file} successfully!")
            
    # Ensure correct data types
    for key, df in data.items():
        if "Total_Exams" in df.columns:
            df["Total_Exams"] = pd.to_numeric(df["Total_Exams"], errors="coerce")
        if "Total_RVU" in df.columns:
            df["Total_RVU"] = pd.to_numeric(df["Total_RVU"], errors="coerce")
        if "Total_Points" in df.columns:
            df["Total_Points"] = pd.to_numeric(df["Total_Points"], errors="coerce")
    
    return data

data = load_data()

# Debugging: Display loaded data
for key, df in data.items():
    st.write(f"📊 **{key} Data Preview:**")
    st.dataframe(df.head())

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

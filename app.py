import streamlit as st
import pandas as pd
import plotly.express as px

# Set Streamlit Page Config (MUST be the first Streamlit command)
st.set_page_config(page_title="MILV Executive Dashboard", layout="wide")

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

# Apply MILV theme and logo
logo_path = "milv.png"
st.sidebar.image(logo_path, use_container_width=True)  # Fix: use_container_width instead of use_column_width
st.sidebar.title("Navigation")

# Sidebar Navigation
page = st.sidebar.radio("Go to", ["Overview", "Physician Performance", "Modality Analysis", "Workload Trends", "Data Explorer"])

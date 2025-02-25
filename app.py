import streamlit as st
import pandas as pd
import os

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
    return data

data = load_data()

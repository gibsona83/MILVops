import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Ensure set_page_config is the first Streamlit command
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
        if "Year-Month" in df.columns:
            df["Year-Month"] = pd.to_datetime(df["Year-Month"], errors="coerce", format='%Y-%m')
    
    return data

data = load_data()

# Apply MILV theme and logo
logo_path = os.path.join(os.path.dirname(__file__), "milv.png")
st.sidebar.image(logo_path, use_container_width=True)
st.sidebar.title("Filters")

# Sidebar Filters
physician_filter = st.sidebar.multiselect("Select Physicians", data['physician_kpi']['Finalizing Provider'].unique(), default=[])
modality_filter = st.sidebar.multiselect("Select Modality", data['modality_distribution']['Modality'].unique(), default=[])
start_date, end_date = st.sidebar.date_input("Select Date Range", [data['physician_time_series']['Year-Month'].min(), data['physician_time_series']['Year-Month'].max()])

# Apply Filters
filtered_kpi = data['physician_kpi'][data['physician_kpi']['Finalizing Provider'].isin(physician_filter)] if physician_filter else data['physician_kpi']
filtered_modality = data['modality_distribution'][data['modality_distribution']['Modality'].isin(modality_filter)] if modality_filter else data['modality_distribution']
filtered_workload = data['physician_time_series'][(data['physician_time_series']['Year-Month'] >= pd.to_datetime(start_date)) & (data['physician_time_series']['Year-Month'] <= pd.to_datetime(end_date))]

# Convert workload trends to Year-Month format
filtered_workload['Year-Month'] = filtered_workload['Year-Month'].dt.strftime('%Y-%m')

# Main Dashboard
st.title("📊 MILV Executive Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Exams", f"{filtered_kpi['Total_Exams'].sum():,}")
col2.metric("Total RVU", f"{filtered_kpi['Total_RVU'].sum():,.2f}")
col3.metric("Total Points", f"{filtered_kpi['Total_Points'].sum():,.2f}")

st.subheader("Workload Trends by Month")
fig = px.line(filtered_workload.sort_values(by="Year-Month", ascending=True), x="Year-Month", y="Total_Exams", color="Finalizing Provider", markers=True)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Total Exams by Modality")
fig = px.pie(filtered_modality, names="Modality", values="Total Exams", title="Modality Distribution")
st.plotly_chart(fig)

st.subheader("Top Physicians by Total RVU")
fig = px.bar(filtered_kpi.nlargest(10, 'Total_RVU'), x="Finalizing Provider", y="Total_RVU", text="Total_RVU", color="Total_RVU")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Physician-Specific Modality Breakdown")
fig = px.bar(data['physician_modality'], x="Physician", y="Exam Count", color="Modality", text="Exam Count")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Data Explorer")
search_term = st.text_input("Search Physician")
if search_term:
    filtered_df = filtered_kpi[filtered_kpi['Finalizing Provider'].str.contains(search_term, case=False, na=False)]
    st.dataframe(filtered_df)
else:
    st.dataframe(filtered_kpi)

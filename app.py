import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Set Streamlit Page Configuration
st.set_page_config(page_title="MILV Executive Dashboard", layout="wide")

# Load the original dataset
@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "MILVCY2024.csv")
    df = pd.read_csv(file_path)
    
    # Convert 'Final Date' to datetime
    df["Final Date"] = pd.to_datetime(df["Final Date"], errors="coerce")
    
    # Extract 'Year-Month' for trends
    df["Year-Month"] = df["Final Date"].dt.to_period("M").astype(str)
    
    # Extract IMG codes from Exam
    df["IMG"] = df["Exam"].str.extract(r"\[IMG(\d+)\]")
    df["Exam"] = df["Exam"].str.replace(r"\s*\[IMG\d+\]\s*", "", regex=True)
    
    # Standardize modality names
    df["Modality"] = df["Modality"].replace({"CR": "XR"})
    
    # Convert RVU & Points to numeric
    df["RVU"] = pd.to_numeric(df["RVU"], errors="coerce")
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    
    return df

data = load_data()

# Apply MILV theme and logo
logo_path = os.path.join(os.path.dirname(__file__), "milv.png")
st.sidebar.image(logo_path, use_container_width=True)
st.sidebar.title("Filters")

# Sidebar Filters
physician_filter = st.sidebar.multiselect("Select Physicians", data['Finalizing Provider'].unique(), default=[])
modality_filter = st.sidebar.multiselect("Select Modality", data['Modality'].unique(), default=[])
group_filter = st.sidebar.multiselect("Select Radiologist Group", data['Radiologist Group'].unique(), default=[])

# Date Range Filter
min_date = data["Final Date"].min().date()
max_date = data["Final Date"].max().date()
start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# Apply Filters
filtered_data = data.copy()
if physician_filter:
    filtered_data = filtered_data[filtered_data['Finalizing Provider'].isin(physician_filter)]
if modality_filter:
    filtered_data = filtered_data[filtered_data['Modality'].isin(modality_filter)]
if group_filter:
    filtered_data = filtered_data[filtered_data['Radiologist Group'].isin(group_filter)]
filtered_data = filtered_data[(filtered_data['Final Date'] >= pd.to_datetime(start_date)) & (filtered_data['Final Date'] <= pd.to_datetime(end_date))]

# Dashboard Overview
st.title("📊 MILV Executive Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Exams", f"{filtered_data['Accession'].count():,}")
col2.metric("Total RVU", f"{filtered_data['RVU'].sum():,.2f}")
col3.metric("Total Points", f"{filtered_data['Points'].sum():,.2f}")

# Workload Trends by Month
st.subheader("Workload Trends by Month")
workload_trends = filtered_data.groupby("Year-Month").agg(Total_Exams=("Accession", "count")).reset_index()
fig = px.line(workload_trends, x="Year-Month", y="Total_Exams", markers=True)
st.plotly_chart(fig, use_container_width=True)

# Modality Distribution
st.subheader("Total Exams by Modality")
modality_chart = px.pie(filtered_data, names="Modality", title="Modality Distribution")
st.plotly_chart(modality_chart)

# vRad vs MILV Comparison
st.subheader("vRad vs MILV Workload")
vrad_milv_comparison = filtered_data.groupby("Radiologist Group").agg(Total_Exams=("Accession", "count")).reset_index()
fig = px.bar(vrad_milv_comparison, x="Radiologist Group", y="Total_Exams", text="Total_Exams", color="Radiologist Group")
st.plotly_chart(fig, use_container_width=True)

# Top Physicians by RVU
st.subheader("Top Physicians by RVU")
top_physicians = filtered_data.groupby("Finalizing Provider").agg(Total_RVU=("RVU", "sum")).reset_index().nlargest(10, "Total_RVU")
fig = px.bar(top_physicians, x="Finalizing Provider", y="Total_RVU", text="Total_RVU", color="Total_RVU")
st.plotly_chart(fig, use_container_width=True)

# Data Explorer
st.subheader("Data Explorer")
search_term = st.text_input("Search Exam Description")
if search_term:
    filtered_df = filtered_data[filtered_data['Exam'].str.contains(search_term, case=False, na=False)]
    st.dataframe(filtered_df)
else:
    st.dataframe(filtered_data)

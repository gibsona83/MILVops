import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Set page title and layout
st.set_page_config(page_title="RVU Dashboard", layout="wide")

# Add logo from GitHub
logo_url = "https://raw.githubusercontent.com/gibsona83/MILVops/main/logo.png"
st.image(logo_url, width=250)

# Upload data file
st.sidebar.header("Upload New Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv", "xlsx"])

if uploaded_file is not None:
    file_extension = os.path.splitext(uploaded_file.name)[1]
    if file_extension == ".csv":
        df = pd.read_csv(uploaded_file)
    elif file_extension in [".xls", ".xlsx"]:
        df = pd.read_excel(uploaded_file, sheet_name='powerscribe Data')
    
    # Data Cleaning
    df.drop(columns=[col for col in df.columns if "Unnamed" in col], inplace=True, errors='ignore')
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.dropna(subset=["Date"])  # Remove rows without a date
    
    # Sidebar filters
    st.sidebar.subheader("Filters")
    selected_authors = st.sidebar.multiselect("Select Radiologists", df["Author"].unique(), default=df["Author"].unique())
    date_range = st.sidebar.date_input("Select Date Range", [df["Date"].min(), df["Date"].max()])
    
    # Apply Filters
    df_filtered = df[(df["Author"].isin(selected_authors)) & 
                      (df["Date"] >= pd.to_datetime(date_range[0])) &
                      (df["Date"] <= pd.to_datetime(date_range[1]))]
    
    # KPIs
    total_procedures = df_filtered["Procedure"].sum()
    total_points = df_filtered["Points"].sum()
    avg_turnaround = pd.to_timedelta(df_filtered["Turnaround"]).mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Procedures", total_procedures)
    col2.metric("Total Points", total_points)
    col3.metric("Avg Turnaround Time", str(avg_turnaround).split('.')[0])
    
    # Visualization - Trends
    st.subheader("Procedure and Points Trends")
    fig, ax = plt.subplots(figsize=(10, 4))
    df_filtered.groupby("Date")["Procedure"].sum().plot(ax=ax, label="Procedures")
    df_filtered.groupby("Date")["Points"].sum().plot(ax=ax, label="Points")
    ax.set_title("Daily Trends")
    ax.legend()
    st.pyplot(fig)
    
    # Visualization - Radiologist Performance
    st.subheader("Performance by Radiologist")
    fig, ax = plt.subplots(figsize=(10, 4))
    df_filtered.groupby("Author")["Points"].sum().sort_values().plot(kind='barh', ax=ax)
    ax.set_title("Total Points by Radiologist")
    st.pyplot(fig)
    
    # Efficiency Scatter Plot
    st.subheader("Efficiency: Turnaround Time vs. Points")
    df_filtered["Turnaround_minutes"] = pd.to_timedelta(df_filtered["Turnaround"]).dt.total_seconds() / 60
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df_filtered["Turnaround_minutes"], df_filtered["Points"], alpha=0.6)
    ax.set_xlabel("Turnaround Time (Minutes)")
    ax.set_ylabel("Points")
    ax.set_title("Turnaround Time vs. Productivity")
    st.pyplot(fig)
else:
    st.warning("Please upload a CSV or Excel file to view the dashboard.")

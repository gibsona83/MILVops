import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Page configuration
st.set_page_config(page_title="Radiology Productivity Dashboard", layout="wide")

# Sidebar for file upload
st.sidebar.header("Upload Files")
csv_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])
excel_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

if csv_file and excel_file:
    # Load CSV File
    csv_df = pd.read_csv(csv_file)

    # Load Excel File
    excel_data = pd.ExcelFile(excel_file)
    sheet_name = "Productivity"
    excel_df = excel_data.parse(sheet_name)

    # Merge DataFrames on 'Accession'
    merged_df = pd.merge(csv_df, excel_df, on="Accession", how="inner")

    # Convert date columns to datetime
    merged_df["Created"] = pd.to_datetime(merged_df["Created"])
    merged_df["Signed"] = pd.to_datetime(merged_df["Signed"])
    merged_df["Final Date"] = pd.to_datetime(merged_df["Final Date"])

    # Calculate Turnaround Time (minutes)
    merged_df["Turnaround Time (min)"] = (merged_df["Final Date"] - merged_df["Created"]).dt.total_seconds() / 60

    # Sidebar Filters
    st.sidebar.subheader("Filters")
    modality_filter = st.sidebar.multiselect("Select Modality", merged_df["Modality"].unique())
    provider_filter = st.sidebar.multiselect("Select Provider", merged_df["Finalizing Provider"].unique())

    # Apply Filters
    if modality_filter:
        merged_df = merged_df[merged_df["Modality"].isin(modality_filter)]
    if provider_filter:
        merged_df = merged_df[merged_df["Finalizing Provider"].isin(provider_filter)]

    # KPIs
    st.title("📊 Radiology Productivity Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", len(merged_df))
    col2.metric("Avg Turnaround Time (min)", round(merged_df["Turnaround Time (min)"].mean(), 2))
    col3.metric("Total RVU", round(merged_df["RVU"].sum(), 2))

    # Time Series Analysis
    st.subheader("📅 Cases Over Time")
    time_series = merged_df.groupby(merged_df["Final Date"].dt.date).size().reset_index(name="Case Count")
    fig1 = px.line(time_series, x="Final Date", y="Case Count", title="Cases Processed Over Time")
    st.plotly_chart(fig1)

    # Provider Performance
    st.subheader("👨‍⚕️ Provider Performance")
    provider_performance = merged_df.groupby("Finalizing Provider")["RVU"].sum().reset_index()
    fig2 = px.bar(provider_performance, x="Finalizing Provider", y="RVU", title="Radiologist RVU Performance")
    st.plotly_chart(fig2)

    # Modality Usage
    st.subheader("📡 Modality Trends")
    modality_count = merged_df["Modality"].value_counts().reset_index()
    modality_count.columns = ["Modality", "Count"]
    fig3 = px.pie(modality_count, names="Modality", values="Count", title="Modality Distribution")
    st.plotly_chart(fig3)

    # Shift Productivity
    st.subheader("🕒 Shift-Based Productivity")
    shift_performance = merged_df.groupby("Shift Time Final")["Points"].sum().reset_index()
    fig4 = px.bar(shift_performance, x="Shift Time Final", y="Points", title="Shift Productivity (Points)")
    st.plotly_chart(fig4)

    # Download Processed Data
    st.subheader("📥 Download Processed Data")
    output = io.BytesIO()
    merged_df.to_csv(output, index=False)
    st.download_button("Download Processed CSV", output.getvalue(), file_name="processed_data.csv", mime="text/csv")

else:
    st.warning("Please upload both CSV and Excel files to proceed.")


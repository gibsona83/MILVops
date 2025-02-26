import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit Page Config
st.set_page_config(page_title="RVU Daily Master Dashboard", layout="wide")

st.title("📊 RVU Daily Master Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload RVU Daily Master File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="powerscribe Data")
    
    # Data Cleaning
    df = df.drop(columns=[col for col in df.columns if "Unnamed" in col], errors='ignore')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Ensure the column is treated as a string before conversion
    df['Turnaround'] = df['Turnaround'].astype(str).str.strip()
    
    # Replace invalid formats
    df['Turnaround'] = df['Turnaround'].apply(lambda x: x if ':' in x else None)
    
    # Convert to timedelta, setting invalid values to NaT
    df['Turnaround'] = pd.to_timedelta(df['Turnaround'], errors='coerce')
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    all_radiologists = ['All'] + sorted(df['Author'].unique())
    selected_authors = st.sidebar.multiselect("Select Radiologists", all_radiologists, default=['All'])
    date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
    shifts = st.sidebar.multiselect("Select Shifts", df['shift'].dropna().unique(), default=df['shift'].dropna().unique())
    
    # Apply Filters
    filtered_df = df[(df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))]
    if 'All' not in selected_authors:
        filtered_df = filtered_df[filtered_df['Author'].isin(selected_authors)]
    if shifts:
        filtered_df = filtered_df[filtered_df['shift'].isin(shifts)]
    
    # Display Data Summary
    st.subheader("📌 Data Summary")
    st.write(filtered_df.describe())
    
    # Visualization 1: Daily Productivity
    st.subheader("📈 Daily Productivity")
    fig, ax = plt.subplots(figsize=(12, 5))
    for author in filtered_df['Author'].unique():
        subset = filtered_df[filtered_df['Author'] == author]
        ax.plot(subset['Date'], subset['Points'], marker="o", linestyle='-', label=author, alpha=0.7)
    ax.set_title("Points by Date")
    ax.set_ylabel("Points")
    ax.set_xlabel("Date")
    ax.legend(loc='upper left', bbox_to_anchor=(1,1))
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 2: Turnaround Time Analysis
    st.subheader("⏳ Turnaround Time Analysis")
    fig, ax = plt.subplots(figsize=(12, 5))
    box_data = [filtered_df.loc[filtered_df['Author'] == author, 'Turnaround'].dt.total_seconds()/60 for author in filtered_df['Author'].unique()]
    ax.boxplot(box_data, labels=filtered_df['Author'].unique(), vert=True, patch_artist=True)
    ax.set_title("Turnaround Time per Radiologist (Minutes)")
    ax.set_ylabel("Turnaround Time (Minutes)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 3: Shift-based Performance
    st.subheader("🌙 Shift-Based Performance")
    shift_summary = filtered_df.groupby('shift')['Points'].sum().sort_values()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.barh(shift_summary.index, shift_summary.values, color='skyblue')
    ax.set_title("Total Points per Shift")
    ax.set_xlabel("Total Points")
    ax.set_ylabel("Shift")
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 4: Points per Procedure Trends
    st.subheader("📊 Points per Procedure Trends")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.scatter(filtered_df['Procedure'], filtered_df['Points'], c='blue', alpha=0.5, edgecolors='black')
    ax.set_title("Points vs. Procedures")
    ax.set_xlabel("Procedures")
    ax.set_ylabel("Points")
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    st.success("Dashboard updated successfully! ✅")

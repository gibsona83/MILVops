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
    df['shift'] = pd.to_numeric(df['shift'], errors='coerce')
    
    # Ensure the column is treated as a string before conversion
    df['Turnaround'] = df['Turnaround'].astype(str).str.strip()
    
    # Replace invalid formats
    df['Turnaround'] = df['Turnaround'].apply(lambda x: x if ':' in x else None)
    
    # Convert to timedelta, setting invalid values to NaT
    df['Turnaround'] = pd.to_timedelta(df['Turnaround'], errors='coerce')
    
    # Calculate Points per Half-Day and Procedures per Half-Day
    df['Points per Half-Day'] = df['Points'] / (df['shift'] * 2)
    df['Procedures per Half-Day'] = df['Procedure'] / (df['shift'] * 2)
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    all_radiologists = ['All'] + sorted(df['Author'].unique())
    selected_authors = st.sidebar.multiselect("Select Radiologists", all_radiologists, default=['All'])
    date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
    
    # Apply Filters
    filtered_df = df[(df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))]
    if 'All' not in selected_authors:
        filtered_df = filtered_df[filtered_df['Author'].isin(selected_authors)]
    
    # Shorten Provider Names for Visualization
    filtered_df['Short Name'] = filtered_df['Author'].apply(lambda x: " ".join(x.split(", ")[-1:]))
    
    # Visualization 1: Daily Productivity
    st.subheader("📈 Daily Productivity")
    fig, ax = plt.subplots(figsize=(10, 5))
    grouped = filtered_df.groupby(['Date', 'Short Name'])['Points per Half-Day'].sum().reset_index()
    for name in grouped['Short Name'].unique():
        subset = grouped[grouped['Short Name'] == name]
        ax.plot(subset['Date'], subset['Points per Half-Day'], marker="o", linestyle='-', label=name, alpha=0.7)
    ax.set_title("Points per Half-Day by Date")
    ax.set_ylabel("Points per Half-Day")
    ax.set_xlabel("Date")
    ax.legend(loc='upper left', bbox_to_anchor=(1,1), fontsize=8, frameon=False)
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 2: Procedures per Half-Day Trends
    st.subheader("📊 Procedures per Half-Day Trends")
    fig, ax = plt.subplots(figsize=(10, 5))
    grouped_proc = filtered_df.groupby(['Date', 'Short Name'])['Procedures per Half-Day'].sum().reset_index()
    for name in grouped_proc['Short Name'].unique():
        subset = grouped_proc[grouped_proc['Short Name'] == name]
        ax.plot(subset['Date'], subset['Procedures per Half-Day'], marker="o", linestyle='-', label=name, alpha=0.7)
    ax.set_title("Procedures per Half-Day by Date")
    ax.set_ylabel("Procedures per Half-Day")
    ax.set_xlabel("Date")
    ax.legend(loc='upper left', bbox_to_anchor=(1,1), fontsize=8, frameon=False)
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 3: Shift-based Performance
    st.subheader("🌙 Shift-Based Performance")
    shift_summary = filtered_df.groupby('shift')['Points'].sum().sort_values()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(shift_summary.index, shift_summary.values, color='skyblue')
    ax.set_title("Total Points per Shift")
    ax.set_xlabel("Total Points")
    ax.set_ylabel("Shift")
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    st.success("Dashboard updated successfully! ✅")

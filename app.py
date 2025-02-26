import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
    df['Turnaround'] = pd.to_timedelta(df['Turnaround'], errors='coerce')
    
    # Calculate Points per Half-Day and Procedures per Half-Day
    df['Points per Half-Day'] = df['Points'] / (df['shift'] * 2)
    df['Procedures per Half-Day'] = df['Procedure'] / (df['shift'] * 2)
    
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
    
    # Shorten Provider Names for Visualization
    filtered_df['Short Name'] = filtered_df['Author'].apply(lambda x: x.split(", ")[-1])
    
    # Visualization 1: Daily Productivity
    st.subheader("📈 Daily Productivity")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=filtered_df, x='Date', y='Points per Half-Day', hue='Short Name', marker="o", ax=ax, palette='tab10')
    ax.set_title("Points per Half-Day by Date")
    ax.set_ylabel("Points per Half-Day")
    ax.set_xlabel("Date")
    ax.legend(title='Radiologists', bbox_to_anchor=(1,1), fontsize=8, frameon=False)
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 2: Procedures per Half-Day Trends
    st.subheader("📊 Procedures per Half-Day Trends")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=filtered_df, x='Date', y='Procedures per Half-Day', hue='Short Name', marker="o", ax=ax, palette='tab10')
    ax.set_title("Procedures per Half-Day by Date")
    ax.set_ylabel("Procedures per Half-Day")
    ax.set_xlabel("Date")
    ax.legend(title='Radiologists', bbox_to_anchor=(1,1), fontsize=8, frameon=False)
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    # Visualization 3: Shift-based Performance
    st.subheader("🌙 Shift-Based Performance")
    shift_summary = filtered_df.groupby('shift')['Points'].sum().sort_values()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=shift_summary.index, y=shift_summary.values, palette='coolwarm', ax=ax)
    ax.set_title("Total Points per Shift")
    ax.set_xlabel("Shift")
    ax.set_ylabel("Total Points")
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)
    
    st.success("Dashboard updated successfully! ✅")

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
    df['Turnaround'] = pd.to_timedelta(df['Turnaround'], errors='coerce')
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    authors = st.sidebar.multiselect("Select Radiologists", df['Author'].unique(), default=df['Author'].unique())
    date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])
    shifts = st.sidebar.multiselect("Select Shifts", df['shift'].dropna().unique(), default=df['shift'].dropna().unique())
    
    # Apply Filters
    filtered_df = df[(df['Author'].isin(authors)) &
                     (df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
                     (df['shift'].isin(shifts) if shifts else True)]
    
    # Display Data Summary
    st.subheader("📌 Data Summary")
    st.write(filtered_df.describe())
    
    # Visualization 1: Daily Productivity
    st.subheader("📈 Daily Productivity")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=filtered_df, x='Date', y='Points', hue='Author', marker="o", ax=ax)
    ax.set_title("Points by Date")
    ax.set_ylabel("Points")
    st.pyplot(fig)
    
    # Visualization 2: Turnaround Time Analysis
    st.subheader("⏳ Turnaround Time Analysis")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.boxplot(data=filtered_df, x='Author', y=filtered_df['Turnaround'].dt.total_seconds()/60, ax=ax)
    ax.set_title("Turnaround Time per Radiologist (Minutes)")
    ax.set_ylabel("Turnaround Time (Minutes)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    st.pyplot(fig)
    
    # Visualization 3: Shift-based Performance
    st.subheader("🌙 Shift-Based Performance")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(data=filtered_df, x='shift', y='Points', estimator=sum, ci=None, ax=ax)
    ax.set_title("Total Points per Shift")
    ax.set_ylabel("Total Points")
    st.pyplot(fig)
    
    # Visualization 4: Points per Procedure Trends
    st.subheader("📊 Points per Procedure Trends")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.scatterplot(data=filtered_df, x='Procedure', y='Points', hue='Author', ax=ax)
    ax.set_title("Points vs. Procedures")
    ax.set_xlabel("Procedures")
    ax.set_ylabel("Points")
    st.pyplot(fig)
    
    st.success("Dashboard updated successfully! ✅")

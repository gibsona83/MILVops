import streamlit as st
import pandas as pd

# 🚀 Load CSV File
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # ✅ Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ✅ Apply filters
    df_filtered = df.copy()

    # ✅ Ensure "Turnaround" column exists before proceeding
    if "turnaround" in df_filtered.columns:
        # Convert column to string format for safety
        df_filtered["turnaround"] = df_filtered["turnaround"].astype(str)

        # Fix formatting issue: "1.04:06:07" → Convert "1.04" days to hours properly
        df_filtered["turnaround"] = df_filtered["turnaround"].str.replace(r"\.", " days ", regex=True)

        # Convert to timedelta, replacing errors with NaT
        df_filtered["turnaround"] = pd.to_timedelta(df_filtered["turnaround"], errors="coerce")

        # Fill NaT values with zero duration to prevent calculation errors
        df_filtered["turnaround"] = df_filtered["turnaround"].fillna(pd.Timedelta(seconds=0))

        # Compute the average turnaround time in minutes
        avg_turnaround = df_filtered["turnaround"].mean().total_seconds() / 60

        st.metric("⏳ Avg Turnaround Time (mins)", round(avg_turnaround, 2))

    else:
        st.warning("⚠️ 'Turnaround' column not found in dataset.")
else:
    st.warning("⚠️ Please upload a valid CSV file.")

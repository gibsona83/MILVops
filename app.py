import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 🚀 Upload File
st.sidebar.title("Upload New Data")
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # ✅ Load Excel file
        df = pd.read_excel(uploaded_file, engine="openpyxl")  

        # ✅ Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # ✅ Sidebar Filters
        st.sidebar.title("Filters")
        
        # If the file has a "radiologist" column, allow filtering by provider
        if "radiologist" in df.columns:
            selected_radiologists = st.sidebar.multiselect(
                "Select Radiologists", df["radiologist"].unique(), default=df["radiologist"].unique()
            )
            df_filtered = df[df["radiologist"].isin(selected_radiologists)]
        else:
            df_filtered = df.copy()

        # ✅ Ensure "Turnaround" column exists
        if "turnaround" in df_filtered.columns:
            df_filtered["turnaround"] = df_filtered["turnaround"].astype(str)
            df_filtered["turnaround"] = df_filtered["turnaround"].str.replace(r"\.", " days ", regex=True)
            df_filtered["turnaround"] = pd.to_timedelta(df_filtered["turnaround"], errors="coerce")
            df_filtered["turnaround"] = df_filtered["turnaround"].fillna(pd.Timedelta(seconds=0))
            avg_turnaround = df_filtered["turnaround"].mean().total_seconds() / 60
        else:
            avg_turnaround = None

        # ✅ Display Metrics
        st.markdown("### Key Metrics")
        col1, col2 = st.columns(2)
        col1.metric("⏳ Avg Turnaround Time (mins)", round(avg_turnaround, 2))
        col2.metric("📑 Total Cases", df_filtered.shape[0])

        # ✅ Visualization
        st.markdown("### Turnaround Time Distribution")
        fig, ax = plt.subplots()
        df_filtered["turnaround"].dt.total_seconds().div(60).hist(bins=20, alpha=0.7, ax=ax)
        ax.set_xlabel("Turnaround Time (mins)")
        ax.set_ylabel("Count")
        ax.set_title("Distribution of Turnaround Time")
        st.pyplot(fig)

        # ✅ Show Data Table
        st.markdown("### Filtered Data Preview")
        st.dataframe(df_filtered)

    except Exception as e:
        st.error(f"❌ Error loading Excel file: {e}")

else:
    st.warning("⚠️ Please upload a valid Excel file.")

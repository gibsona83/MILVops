import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ✅ Set up Streamlit Page
st.set_page_config(page_title="RVU Dashboard", layout="wide")

# 🎯 Sidebar: Upload Excel File
st.sidebar.title("Upload New Data")
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # ✅ Load Excel File
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        # ✅ Standardize Column Names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # ✅ Rename 'author' → 'radiologist' for consistency
        if "author" in df.columns:
            df.rename(columns={"author": "radiologist"}, inplace=True)

        # ✅ Sidebar: Add Filters
        st.sidebar.title("Filters")

        # 📌 Filter by Radiologist (if column exists)
        if "radiologist" in df.columns:
            selected_radiologists = st.sidebar.multiselect(
                "Select Radiologists", sorted(df["radiologist"].unique()), default=df["radiologist"].unique()
            )
            df_filtered = df[df["radiologist"].isin(selected_radiologists)]
        else:
            st.warning("⚠️ 'Radiologist' column not found. Using 'Author' instead.")
            df_filtered = df.copy()

        # 📌 Convert "Turnaround" Column Properly
        if "turnaround" in df_filtered.columns:
            df_filtered["turnaround"] = df_filtered["turnaround"].astype(str)

            # ✅ Handle inconsistent formats like "an hour"
            df_filtered["turnaround"] = df_filtered["turnaround"].replace(
                {"an hour": "1:00:00", "a day": "1 day"}, regex=True
            )

            df_filtered["turnaround"] = pd.to_timedelta(df_filtered["turnaround"], errors="coerce")
            df_filtered["turnaround"] = df_filtered["turnaround"].fillna(pd.Timedelta(seconds=0))
            avg_turnaround = df_filtered["turnaround"].mean().total_seconds() / 60
        else:
            avg_turnaround = None

        # 🎯 **Key Metrics**
        st.markdown("## 📊 Key Metrics")
        col1, col2 = st.columns(2)
        col1.metric("⏳ Avg Turnaround Time (mins)", round(avg_turnaround, 2) if avg_turnaround else "N/A")
        col2.metric("📑 Total Cases", df_filtered.shape[0])

        # 📌 **Turnaround Visualization by Radiologist**
        if "radiologist" in df_filtered.columns and "turnaround" in df_filtered.columns:
            st.markdown("## 📈 Turnaround Time by Radiologist")
            avg_turnaround_per_radiologist = df_filtered.groupby("radiologist")["turnaround"].mean().dt.total_seconds().div(60)

            fig, ax = plt.subplots(figsize=(10, 5))
            avg_turnaround_per_radiologist.sort_values().plot(kind="barh", ax=ax, color="skyblue")
            ax.set_xlabel("Avg Turnaround Time (mins)")
            ax.set_title("Turnaround Time per Radiologist")
            st.pyplot(fig)

        # 📌 **Show Filtered Data Table**
        st.markdown("## 📝 Filtered Data Preview")
        st.dataframe(df_filtered)

    except Exception as e:
        st.error(f"❌ Error loading Excel file: {e}")

else:
    st.warning("⚠️ Please upload a valid Excel file.")

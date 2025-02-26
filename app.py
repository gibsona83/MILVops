import pandas as pd

# Ensure df_filtered is defined
if 'df_filtered' not in locals() and 'df_filtered' not in globals():
    st.error("❌ Data not found. Ensure your dataset is loaded before processing.")
else:
    # Ensure Turnaround column exists before proceeding
    if "Turnaround" in df_filtered.columns:
        # Convert Turnaround column to string to prevent type errors
        df_filtered["Turnaround"] = df_filtered["Turnaround"].astype(str)

        # Convert to timedelta, replacing errors with NaT
        df_filtered["Turnaround"] = pd.to_timedelta(df_filtered["Turnaround"], errors="coerce")

        # Fill NaT values with zero-duration to prevent calculation errors
        df_filtered["Turnaround"] = df_filtered["Turnaround"].fillna(pd.Timedelta(seconds=0))

        # Compute the average turnaround time in minutes
        avg_turnaround = df_filtered["Turnaround"].mean().total_seconds() / 60

    else:
        avg_turnaround = None
        st.warning("⚠️ 'Turnaround' column not found in dataset.")

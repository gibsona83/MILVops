import pandas as pd

# Ensure Turnaround column exists before proceeding
if "Turnaround" in df_filtered.columns:
    # Convert Turnaround column to string for safety
    df_filtered["Turnaround"] = df_filtered["Turnaround"].astype(str)

    # Attempt to convert to timedelta, coercing errors to NaT
    df_filtered["Turnaround"] = pd.to_timedelta(df_filtered["Turnaround"], errors="coerce")

    # Fill NaT values with zero duration to prevent calculation errors
    df_filtered["Turnaround"] = df_filtered["Turnaround"].fillna(pd.Timedelta(seconds=0))

    # Compute the average turnaround time in minutes
    avg_turnaround = df_filtered["Turnaround"].mean().total_seconds() / 60
else:
    avg_turnaround = None
    st.warning("⚠️ 'Turnaround' column not found in dataset.")

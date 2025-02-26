import sqlite3
import pandas as pd
import os

# Define the folder where CSV files are stored
DATA_FOLDER = "data/"
DB_PATH = "data/milv_data.db"  # Ensure this matches the path in app.py

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS provider_data (
    created_date TEXT,
    final_date TEXT,
    modality TEXT,
    section TEXT,
    finalizing_provider TEXT,
    rvu REAL
);
""")

# Get all CSV files from the data folder
csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

if not csv_files:
    print("No CSV files found in the data folder.")
else:
    for file in csv_files:
        file_path = os.path.join(DATA_FOLDER, file)
        
        try:
            # Read CSV file into DataFrame
            df = pd.read_csv(file_path)

            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

            # Ensure required columns exist
            required_cols = ["created_date", "final_date", "modality", "section", "finalizing_provider", "rvu"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Skipping {file} - missing columns: {missing_cols}")
                continue

            # Convert date columns to string format for SQLite
            df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce").astype(str)
            df["final_date"] = pd.to_datetime(df["final_date"], errors="coerce").astype(str)
            
            # Ensure RVU is numeric
            df["rvu"] = pd.to_numeric(df["rvu"], errors="coerce").fillna(0)

            # Append data to SQLite
            df.to_sql("provider_data", conn, if_exists="append", index=False)
            print(f"Successfully added data from {file} to SQLite database.")

        except Exception as e:
            print(f"Error processing {file}: {e}")

# Close the connection
conn.close()
print(f"Database created successfully at {DB_PATH}")

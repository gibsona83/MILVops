import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Page Configuration
st.set_page_config(
    page_title="Radiology Productivity Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = pd.DataFrame()
if 'csv_df' not in st.session_state:
    st.session_state.csv_df = pd.DataFrame()
if 'excel_df' not in st.session_state:
    st.session_state.excel_df = pd.DataFrame()

# Helper Functions
def validate_data(df, file_type):
    """Validate uploaded data structure"""
    required_columns = {
        'csv': ['Accession', 'Created', 'Signed', 'Final Date'],
        'excel': ['Accession', 'RVU', 'Modality', 'Finalizing Provider', 'Shift Time Final']
    }
    missing = [col for col in required_columns[file_type] if col not in df.columns]
    return missing

def process_dates(df):
    """Handle date columns conversion"""
    date_cols = ['Created', 'Signed', 'Final Date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

# Sidebar File Upload
with st.sidebar:
    st.header("Data Management")
    
    # CSV Upload
    csv_file = st.file_uploader("Upload CSV File", type=["csv"], key="csv_uploader")
    if csv_file:
        try:
            st.session_state.csv_df = pd.read_csv(csv_file)
            missing = validate_data(st.session_state.csv_df, 'csv')
            if missing:
                st.error(f"Missing columns in CSV: {', '.join(missing)}")
            else:
                st.session_state.csv_df = process_dates(st.session_state.csv_df)
                st.success("CSV file loaded successfully!")
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
    
    # Excel Upload
    excel_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="excel_uploader")
    if excel_file:
        try:
            st.session_state.excel_df = pd.read_excel(excel_file, sheet_name="Productivity")
            missing = validate_data(st.session_state.excel_df, 'excel')
            if missing:
                st.error(f"Missing columns in Excel: {', '.join(missing)}")
            else:
                st.success("Excel file loaded successfully!")
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")

    # Merge Data Button
    if st.button("Merge Data", help="Combine CSV and Excel data after both are uploaded"):
        if not st.session_state.csv_df.empty and not st.session_state.excel_df.empty:
            try:
                st.session_state.merged_data = pd.merge(
                    st.session_state.csv_df,
                    st.session_state.excel_df,
                    on="Accession",
                    how="inner"
                ).drop_duplicates().reset_index(drop=True)
                
                # Calculate turnaround time
                if {'Created', 'Final Date'}.issubset(st.session_state.merged_data.columns):
                    st.session_state.merged_data['Turnaround Time (min)'] = (
                        st.session_state.merged_data['Final Date'] - 
                        st.session_state.merged_data['Created']
                    ).dt.total_seconds() / 60
                
                st.success("Data merged successfully!")
            except Exception as e:
                st.error(f"Error merging data: {str(e)}")
        else:
            st.warning("Please upload both CSV and Excel files first")

    # Filters
    st.header("Filters")
    if not st.session_state.merged_data.empty:
        date_min = st.session_state.merged_data['Final Date'].min().date()
        date_max = st.session_state.merged_data['Final Date'].max().date()
        
        selected_date = st.date_input(
            "Select Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max
        )
        
        modalities = st.multiselect(
            "Select Modalities",
            options=st.session_state.merged_data['Modality'].unique(),
            default=st.session_state.merged_data['Modality'].unique()
        )
        
        providers = st.multiselect(
            "Select Providers",
            options=st.session_state.merged_data['Finalizing Provider'].unique(),
            default=st.session_state.merged_data['Finalizing Provider'].unique()
        )

# Main Dashboard
st.title("🏥 Radiology Productivity Dashboard")

if not st.session_state.merged_data.empty:
    # Apply Filters
    filtered_df = st.session_state.merged_data[
        (st.session_state.merged_data['Modality'].isin(modalities)) &
        (st.session_state.merged_data['Finalizing Provider'].isin(providers)) &
        (st.session_state.merged_data['Final Date'].dt.date.between(*selected_date))
    ]

    # Rest of the dashboard components (KPIs, visualizations, etc.)
    # ... [Keep the visualization code from previous version]

else:
    st.info("👋 Please upload both CSV and Excel files, then click 'Merge Data'")

# Add custom CSS for better error visibility
st.markdown("""
<style>
    .stAlert {padding: 20px; border-radius: 10px;}
    .stException {max-width: 80% !important;}
    .uploadedFile {background-color: #e6f7ff; padding: 10px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)
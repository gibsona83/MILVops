def validate_data(df, file_type):
    """Validate uploaded data structure with file-specific requirements"""
    required_columns = {
        'csv': ['Accession', 'Created', 'Signed', 'Final Date'],
        'excel': ['Accession', 'RVU', 'Modality', 'Finalizing Provider', 'Shift Time Final']
    }
    missing = [col for col in required_columns[file_type] if col not in df.columns]
    return missing

# In the CSV processing section:
if csv_file:
    try:
        st.session_state.csv_df = pd.read_csv(csv_file)
        missing = validate_data(st.session_state.csv_df, 'csv')  # Notice 'csv' here
        if missing:
            st.error(f"Missing columns in CSV: {', '.join(missing)}")
        else:
            st.session_state.csv_df = process_dates(st.session_state.csv_df)
            st.success("CSV file loaded successfully!")

# In the Excel processing section:
if excel_file:
    try:
        st.session_state.excel_df = pd.read_excel(excel_file, sheet_name="Productivity")
        missing = validate_data(st.session_state.excel_df, 'excel')  # Notice 'excel' here
        if missing:
            st.error(f"Missing columns in Excel: {', '.join(missing)}")
        else:
            st.success("Excel file loaded successfully!")
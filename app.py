# ... (keep all imports and constants the same) ...

def main():
    # ... (keep sidebar and file upload logic the same) ...
    
    st.title("MILV Daily Productivity")
    # Add third tab
    tab1, tab2, tab3 = st.tabs(["📅 Daily View", "📈 Trend Analysis", "👤 Provider Analysis"])
    
    # ... (keep existing tab1 and tab2 content) ...
    
    with tab3:  # New Provider Analysis Tab
        st.subheader("Provider Performance Analysis")
        
        # Compact filter controls in columns
        col1, col2 = st.columns(2)
        with col1:
            # Date range picker
            prov_dates = st.date_input(
                "Select Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="prov_date_range"
            )
        with col2:
            # Provider multi-select with search
            all_providers = df[display_cols["author"]].unique()
            selected_providers = st.multiselect(
                "Select Providers:",
                options=all_providers,
                default=all_providers,
                key="prov_select"
            )
        
        # Filter data based on selections
        start_date, end_date = pd.Timestamp(prov_dates[0]), pd.Timestamp(prov_dates[1])
        prov_filtered = df[
            (df[display_cols["date"] >= start_date) &
            (df[display_cols["date"] <= end_date) &
            (df[display_cols["author"]].isin(selected_providers))
        ]
        
        if prov_filtered.empty:
            return st.warning("⚠️ No data for selected filters")
        
        # Compact metrics display
        st.markdown("### 📊 Summary Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Providers", len(selected_providers))
        with col2:
            st.metric("Average Points/HD", round(prov_filtered[display_cols["points/half day"]].mean(), 1))
        with col3:
            st.metric("Average Procedures/HD", round(prov_filtered[display_cols["procedure/half"]].mean(), 1))
        
        # Visualizations in columns
        st.markdown("### 📈 Performance Breakdown")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(
                prov_filtered.groupby(display_cols["author"])[display_cols["points/half day"]].mean()
                .reset_index().sort_values(display_cols["points/half day"], ascending=False),
                x=display_cols["points/half day"],
                y=display_cols["author"],
                orientation='h',
                color=display_cols["points/half day"],
                color_continuous_scale='Viridis',
                title="Average Points per Half-Day"
            ), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(
                prov_filtered.groupby(display_cols["author"])[display_cols["procedure/half"]].mean()
                .reset_index().sort_values(display_cols["procedure/half"], ascending=False),
                x=display_cols["procedure/half"],
                y=display_cols["author"],
                orientation='h',
                color=display_cols["procedure/half"],
                color_continuous_scale='Viridis',
                title="Average Procedures per Half-Day"
            ), use_container_width=True)
        
        # Detailed data with search
        st.markdown("### 🔍 Detailed Provider Data")
        prov_search = st.text_input("Search within results:", key="prov_search")
        final_data = prov_filtered[prov_filtered[display_cols["author"]].str.contains(
            prov_search, case=False)] if prov_search else prov_filtered
        st.dataframe(final_data, use_container_width=True)

if __name__ == "__main__":
    main()
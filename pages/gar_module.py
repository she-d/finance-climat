import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import plotly.express as px

# ==========================================
# GAR Module Function 
# ==========================================
def run_gar_module(df):
    """
    Core function for the Green Asset Ratio (GAR) dashboard.
    Includes robust data cleaning for real-world Excel/CSV files.
    """
    st.header("Green Asset Ratio (GAR) & Portfolio Optimization")
    
    # ---------------------------------------------------------
    # 0. Data Cleaning Layer (Robustness Check)
    # ---------------------------------------------------------
    # Strip leading/trailing whitespaces from column names
    df.columns = df.columns.str.strip()
    
    # Standardize specific column names to match the engine's expectation
    if 'EU Taxonomy alignment (%)' in df.columns:
        df.rename(columns={'EU Taxonomy alignment (%)': 'EU Taxonomy alignment'}, inplace=True)
        
    # Check for mandatory columns
    required_cols = ['Company name', 'NACE Code', 'Portfolio Weight (%)', 'Taxonomy Eligibility', 'EU Taxonomy alignment']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing mandatory columns in the uploaded file: {missing_cols}")
        return

    # Convert alignment column to numeric and fill blanks (NaN) with 0
    df['EU Taxonomy alignment'] = pd.to_numeric(df['EU Taxonomy alignment'], errors='coerce').fillna(0)

    # ---------------------------------------------------------
    # 1. Pre-processing & Traceability (Data Quality)
    # ---------------------------------------------------------
    # Filter out Financials (NACE 'K') for Denominator
    df['Is_Financial'] = df['NACE Code'].astype(str).str.startswith('K')
    df_nfc = df[~df['Is_Financial']].copy()
    
    if df_nfc.empty:
        st.error("No eligible Non-Financial Corporations (NFCs) found in the dataset.")
        return

    # Normalize Weights
    total_weight = df_nfc['Portfolio Weight (%)'].sum()
    df_nfc['Normalized_Weight'] = df_nfc['Portfolio Weight (%)'] / total_weight
    
    # Traceability: Identify Proxy vs. Reported
    # Assets with 'X' or 0% alignment are treated as Proxy/Estimated for this simulation
    df_nfc['Data_Source'] = np.where(df_nfc['Taxonomy Eligibility'] == 'X', 'Proxy (Estimated)', 'Reported')
    
    # ---------------------------------------------------------
    # 2. Sidebar Parameters
    # ---------------------------------------------------------
    st.sidebar.subheader("GAR Optimization Settings")
    cap_limit = st.sidebar.slider("Max Weight Cap per Issuer (%)", 5, 30, 15, key="gar_cap") / 100.0

    # ---------------------------------------------------------
    # 3. Optimization Engine (SLSQP)
    # ---------------------------------------------------------
    current_gar = np.sum(df_nfc['Normalized_Weight'] * (df_nfc['EU Taxonomy alignment'] / 100))

    def objective_function(weights):
        return -np.sum(weights * (df_nfc['EU Taxonomy alignment'].values / 100))

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((0, cap_limit) for _ in range(len(df_nfc)))

    run_optimization = st.sidebar.button("Run GAR Optimization")

    if run_optimization:
        initial_weights = df_nfc['Normalized_Weight'].values
        result = minimize(objective_function, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            df_nfc['Optimized_Weight'] = result.x
            optimized_gar = -result.fun
            
            # ---------------------------------------------------------
            # 4. Dashboard Visualization
            # ---------------------------------------------------------
            # KPI Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Baseline GAR", f"{current_gar*100:.2f}%")
            col2.metric("Optimized GAR", f"{optimized_gar*100:.2f}%", delta=f"{(optimized_gar-current_gar)*100:.2f}%p")
            
            # Data Quality Score logic: Percentage of weight coming from Reported data
            dqs_score = df_nfc[df_nfc['Data_Source'] == 'Reported']['Normalized_Weight'].sum() * 100
            col3.metric("Data Quality Score (Reported Data)", f"{dqs_score:.0f}%")
            
            st.divider()

            # Chart 1: Capital Reallocation
            st.subheader("Capital Reallocation Strategy")
            df_chart = df_nfc.melt(id_vars=['Company name', 'EU Taxonomy alignment'], 
                                   value_vars=['Normalized_Weight', 'Optimized_Weight'], 
                                   var_name='Scenario', value_name='Weight')
            fig_bar = px.bar(df_chart, x='Company name', y='Weight', color='Scenario', barmode='group',
                             color_discrete_map={'Normalized_Weight': 'gray', 'Optimized_Weight': 'green'})
            st.plotly_chart(fig_bar, use_container_width=True)

            # Chart 2: Data Traceability (Proxy vs Reported)
            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("GAR Data Traceability")
                fig_proxy = px.pie(df_nfc, values='Optimized_Weight', names='Data_Source', hole=0.4,
                                   title="Portfolio Weight by Data Source")
                st.plotly_chart(fig_proxy, use_container_width=True)
                
            with col_right:
                st.subheader("Sector Breakdown")
                fig_sector = px.pie(df_nfc, values='Optimized_Weight', names='NACE Code', 
                                    title="Optimized Weight by NACE Sector")
                st.plotly_chart(fig_sector, use_container_width=True)
                
            # Data Table Export
            st.subheader("Detailed Portfolio Data")
            st.dataframe(df_nfc[['Company name', 'NACE Code', 'Data_Source', 'EU Taxonomy alignment', 'Normalized_Weight', 'Optimized_Weight']])
            
        else:
            st.error("Optimization failed. Check constraints.")
    else:
        st.info("Set parameters in the sidebar and click 'Run GAR Optimization'.")


# ==========================================
# Main Execution (File Ingestion)
# ==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="Team Dashboard - GAR Module", layout="wide")
    
    st.sidebar.title("Data Ingestion")
    uploaded_file = st.sidebar.file_uploader("Upload Portfolio Data (Excel/CSV)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        # Load user data
        if uploaded_file.name.endswith('.csv'):
            df_main = pd.read_csv(uploaded_file)
        else:
            df_main = pd.read_excel(uploaded_file)
            
        # Execute the GAR module
        run_gar_module(df_main)
        
    else:
        st.warning("Please upload a Portfolio file to begin.")
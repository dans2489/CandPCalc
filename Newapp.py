from __future__ import annotations
from datetime import date, timedelta
import math
import pandas as pd
import streamlit as st
import numpy as np 

# --- Import configuration data from the external file ---
from config import (
    FT2_TO_M2, RATE_INPUTS_CONFIG,
    PRISON_TO_REGION, TARIFF_BANDS
)


# ==============================================================================
# 1. HELPER FUNCTIONS (Encapsulate logic)
# ==============================================================================

def calculate_costs(tariff_band: str, editable_rates: dict, area_m2: float) -> pd.DataFrame:
    """
    Placeholder function for the core cost calculation logic.
    """
    
    # 1. Retrieve the selected intensity values
    intensities = TARIFF_BANDS[tariff_band]['intensity_per_year']
    
    # Example calculation: Annual Electricity Cost
    elec_kwh_annual = intensities['elec_kwh_per_m2'] * area_m2
    elec_unit_cost = elec_kwh_annual * editable_rates['elec_unit']
    elec_daily_cost = editable_rates['elec_daily'] * 365.25 # Annualised daily charge

    # Example Output
    data = {
        'Cost Component': ['Electricity (Unit)', 'Electricity (Daily)', 'Gas (Unit)', 'Admin'],
        'Annual Cost (£)': [
            elec_unit_cost,
            elec_daily_cost,
            intensities['gas_kwh_per_m2'] * area_m2 * editable_rates['gas_unit'],
            editable_rates['admin_monthly'] * 12
        ]
    }
    
    df = pd.DataFrame(data)
    # Add a grand total row
    df.loc[len(df)] = ['TOTAL ESTIMATED COST', df['Annual Cost (£)'].sum()]
    
    return df

def reset_rates_to_tariff():
    """Callback function to reset rates when the tariff band changes or button is clicked."""
    # Get the value *after* the change, which is accessible via the widget's key in session_state
    selected_band = st.session_state.get('tariff_band_selector', 'medium') 
    default_rates = TARIFF_BANDS[selected_band]['rates']
    for key, _, _ in RATE_INPUTS_CONFIG:
        st.session_state[f'rate_{key}'] = default_rates[key]

# ==============================================================================
# 2. PAGE CONFIG & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="💷",
    layout="centered"
)

# --- CSS Styling (kept as-is) ---
st.markdown(
    """
    <style>
    /* Typography */
    html, body, [class*="css"] {
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Ubuntu, Cantarell,
                   Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
    }

    /* Primary buttons – full width for clean alignment */
    .stButton > button {
      background: #00703C; color: #fff; border: 2px solid #005A30;
      border-radius: 4px; padding: .50rem 1rem; font-weight: 600; width: 100%;
    }
    .stButton > button:focus { outline: 3px solid #FFDD00; outline-offset: 2px; }

    /* Download buttons full width */
    .stDownloadButton > button { width: 100%; }

    /* Tables (GOV.UK-like chrome) */
    table { border-collapse: collapse; width: 100%; margin: .5rem 0 1rem; }
    th, td { border: 1px solid #b1b4b6; padding: .5rem .6rem; text-align: left; }
    thead th { background: #f3f2f1; font-weight: 700; }
    tr.grand td { font-weight: 800; border-top: 3px double #0b0c0c; }
    td.neg { color: #D4351C; }
    .muted { color: #6f777b; }

    /* ✅ Sidebar styling */
    [data-testid="stSidebar"] {
      background-color: #f3f2f1 !important;   /* neutral GOV.UK grey */
      min-height: 100vh;                       /* fill full height */
      min-width: 420px;                        /* wider sidebar */
    }

    /* Ensure inner wrappers don't override the background back to white */
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div,
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
      background: transparent !important;
    }

    /* Keep inner content wide enough (older Streamlit builds) */
    [data-testid="stSidebar"] > div:first-child {
      max-width: 480px;
      padding-right: 8px;
    }

    /* Optional neutral callout inside the sidebar (if you keep it) */
    .sb-callout {
      background: #f3f2f1; border-left: 6px solid #b1b4b6;
      padding: 8px 10px; margin-bottom: 6px; font-weight: 700;
    }

    /* 🔒 Fully hide sidebar when collapsed */
    section[data-testid="stSidebar"][aria-expanded="false"] {
      width: 0 !important;
      min-width: 0 !important;
      max-width: 0 !important;
    }

    /* 📐 Keep main app centered regardless of sidebar */
    div[data-testid="stAppViewContainer"] {
      margin-left: auto !important;
      margin-right: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## Cost and Price Calculator\n")

# ==============================================================================
# 3. SIDEBAR (User Inputs)
# ==============================================================================

# 3a. Select Tariff Band (Must be first to drive defaults)
default_tariff = 'medium'
tariff_band = st.sidebar.radio(
    "Select Tariff Band",
    options=["low", "medium", "high"],
    index=["low", "medium", "high"].index(default_tariff),
    horizontal=True,
    key='tariff_band_selector',
    on_change=reset_rates_to_tariff # Callback to reset rates when band changes
)

# 3b. Initialize Session State (Only on first run)
if 'rates_initialized' not in st.session_state:
    reset_rates_to_tariff() # Initialize rates based on default_tariff
    st.session_state['rates_initialized'] = True


with st.sidebar:
    st.divider()
    
    # Informative box about the active tariff
    st.info(f"Using **{tariff_band.capitalize()}** intensity values for calculations.")
    st.divider()

    # 1. Prison and Region
    prison = st.selectbox(
        "Select HMP/YOI",
        options=list(PRISON_TO_REGION.keys()),
        index=list(PRISON_TO_REGION.keys()).index("Belmarsh"),
        key='selected_prison'
    )
    
    # FIX APPLIED: Region is calculated and displayed correctly here.
    region = PRISON_TO_REGION.get(prison, "National")
    st.markdown(f"**Region:** <span style='font-weight:700; color:#00703C;'>{region}</span>", unsafe_allow_html=True)
    
    st.divider()
    
    # 2. Area Input
    st.markdown("### Cost Drivers")
    area_sqft = st.number_input(
        "Production Area (Sq Ft)", 
        min_value=0, 
        value=5000, 
        step=100,
        key='area_sqft',
        format="%d"
    )
    area_m2 = area_sqft * FT2_TO_M2
    st.markdown(f"*(**{area_m2:.2f}** $\\text{{m}}^2$)*")
    
    # Placeholder for other drivers (e.g., FTE, Hours)
    num_employees = st.number_input(
        "FTE Employees (for Water/HR)",
        min_value=1,
        value=5,
        key='fte_employees',
        format="%d"
    )
    st.divider()

    # 3. Editable Rates (Refactored using loop and Session State)
    st.markdown("### 💰 Editable Rates (Override Defaults)")
    
    # Button to reset rates to the currently selected tariff's defaults
    st.button("Reset Rates to Tariff Defaults", on_click=reset_rates_to_tariff, key='reset_button')
    st.markdown("---")
    
    editable_rates = {}
    
    for key, label, decimals in RATE_INPUTS_CONFIG:
        # The key ties the widget value to session state
        editable_rates[key] = st.number_input(
            label,
            value=st.session_state[f'rate_{key}'],
            min_value=0.0,
            format=f"%.{decimals}f",
            step=0.0001 if decimals > 2 else 0.01,
            key=f"rate_{key}" 
        )

# ==============================================================================
# 4. MAIN APP BODY (Calculations & Output)
# ==============================================================================

st.write("This is the main page content, centered even when the sidebar is open/closed.")
st.markdown("---")

# Call the modular function to get the results
cost_df = calculate_costs(
    tariff_band=tariff_band,
    editable_rates=editable_rates,
    area_m2=area_m2
)

st.subheader(f"Annual Estimated Costs ({prison})")

# Custom styling for the total row in the Streamlit dataframe
st.dataframe(
    cost_df.style.apply(lambda x: ['font-weight: bold; border-top: 3px double black' if i == len(cost_df) - 1 else '' for i in range(len(cost_df))], axis=0).format(
        {'Annual Cost (£)': '£{:,.2f}'}
    ).hide(axis='index'),
    use_container_width=True
)

st.caption("Note: Costs are based on the selected tariff intensities and current/overridden rates.")

# -----------------------------
# Ad-hoc Dates (Working Days) Input
# -----------------------------
st.markdown("---")
st.subheader("Ad-Hoc / Project Date Range")
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start Date", 
        value=date.today(),
        key='adhoc_start'
    )
with col2:
    end_date = st.date_input(
        "End Date", 
        value=date.today() + timedelta(days=90),
        key='adhoc_end'
    )

if end_date < start_date:
    st.error("The End Date must be after the Start Date.")
else:
    total_days = (end_date - start_date).days + 1
    
    # Simple 5/7 working day approximation
    working_days_estimate = math.ceil(total_days * 5 / 7) 
    
    st.markdown(f"""
    <div style='border: 1px solid #b1b4b6; padding: 10px; background:#f3f2f1; border-radius: 4px;'>
        <p style='margin: 0; font-weight:700;'>Range Summary:</p>
        <ul style='list-style-type: none; padding: 0; margin: 0; margin-left: 10px;'>
            <li>**Total Days:** {total_days}</li>
            <li>**Estimated Working Days:** {working_days_estimate}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
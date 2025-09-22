import streamlit as st
from pathlib import Path

# --- BRAND COLORS ---
NFN_BLUE = "#1D428A"
GOV_GREEN = "#00703C"

# --- TOP BAR WITH LOGO OR TITLE ---
def render_header():
    logo_path = Path("logo.png")
    st.markdown(
        f"""
        <div style="width:100%;background:{NFN_BLUE};padding:20px 0 12px 0;margin-bottom:28px;">
            <div style="max-width:1200px;margin:auto;display:flex;align-items:center;">
                {f'<img src="Logo.png" style="height:48px;margin-right:20px;border-radius:8px;box-shadow-size:2.2rem;font-weight:700;letter-spacing:0.5px;">Cost and Price Calculator</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with st.sidebar:
    st.header("Brand options")
    st.info("Logo will be used from Logo.png in your repo. To update, replace the file.")

render_header()

# --- EXAMPLE INPUTS ---
st.subheader("Workshop Size")
width_ft = st.number_input("Width (ft)", min_value=0.0, value=30.0, step=1.0)
length_ft = st.number_input("Length (ft)", min_value=0.0, value=30.0, step=1.0)
area_ft2 = width_ft * length_ft
area_m2 = area_ft2 * 0.092903

# --- HIGHLIGHTED AREA DISPLAY ---
st.markdown(
    f'''
    <div style="
        background:{GOV_GREEN};
        color:#fff;
        padding:14px 28px;
        border-radius:12px;
        display:inline-block;
        font-weight:600;
        font-size:1.25rem;
        margin-top:12px;
        margin-bottom:12px;
        box-shadow:0 2px 8px rgba(0,0,0,0.07);
    ">
        Calculated area: {area_ft2:,.0f} ft² · {area_m2:,.0f} m²
    </div>
    ''',
    unsafe_allow_html=True
)

# --- MAINTENANCE/DEPRECIATION CALCULATION ---
st.subheader("Maintenance/Depreciation (£/m²/year)")
rate_per_m2_y = st.number_input("Maintenance rate (£/m²/year)", min_value=0.0, value=15.0, step=1.0)
annual_maintenance = area_m2 * rate_per_m2_y
monthly_maintenance = annual_maintenance / 12
st.markdown(
    f"""
    <div style="margin-top:16px;font-size:1.1rem;">
        <b>Annual maintenance:</b> £{annual_maintenance:,.2f}<br>
        <b>Monthly maintenance:</b> £{monthly_maintenance:,.2f}
    </div>
    """,
    unsafe_allow_html=True
)

# --- ADDITIONAL STYLING FOR BUTTONS AND INPUTS ---
st.markdown(
    f"""
    <style>
    .stButton > button {{
        background-color: {NFN_BLUE} !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        padding: 10px 24px !important;
        margin-top: 8px !important;
    }}
    .stNumberInput input {{
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        padding: 8px 12px !important;
    }}
    .stTextInput input {{
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        padding: 8px 12px !important;
    }}
    .stSelectbox div[data-baseweb="select"] {{
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        padding: 8px 12px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

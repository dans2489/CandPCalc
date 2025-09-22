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
                {f'<img src="logo.png" style="height:48px;margin-right:20px;borderstyle="color:#fff;font-size:2.2rem;font-weight:700;letter-spacing:0.5px;">Cost and Price Calculator</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- SIDEBAR ---
with st.sidebar:
    st.header("Brand options")
    st.info("Logo will be used from logo.png in your repo. To update, replace the file.")
    st.markdown("---")
    st.header("Instructions")
    st.write(
        "1. Enter your workshop dimensions in feet or select a template.\n"
        "2. Adjust the maintenance rate if needed.\n"
        "3. Fill in other cost lines as needed.\n"
        "4. View your calculated costs instantly."
    )

render_header()

# --- SIZE TEMPLATES ---
SIZE_LABELS = [
    "Select",
    "Small (~2,500 ft², ~50×50 ft)",
    "Medium (~5,000 ft²)",
    "Large (~10,000 ft²)",
    "Enter dimensions in ft",
]
size_map = {
    "Small (~2,500 ft², ~50×50 ft)": 2500,
    "Medium (~5,000 ft²)": 5000,
    "Large (~10,000 ft²)": 10000,
}

st.subheader("Workshop Size")
workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS)
if workshop_size == "Enter dimensions in ft":
    col1, col2 = st.columns(2)
    with col1:
        width_ft = st.number_input("Width (ft)", min_value=0.0, value=30.0, step=1.0)
    with col2:
        length_ft = st.number_input("Length (ft)", min_value=0.0, value=30.0, step=1.0)
    area_ft2 = width_ft * length_ft
else:
    area_ft2 = size_map.get(workshop_size, 0)
    width_ft = length_ft = 0

area_m2 = area_ft2 * 0.092903

# --- HIGHLIGHTED AREA DISPLAY ---
if area_ft2 > 0:
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

# --- OTHER COST LINES ---
st.subheader("Other Costs (Optional)")
prisoner_wages = st.number_input("Prisoner wages (monthly, £)", min_value=0.0, value=0.0, step=10.0)
electricity = st.number_input("Electricity (monthly est, £)", min_value=0.0, value=0.0, step=10.0)
gas = st.number_input("Gas (monthly est, £)", min_value=0.0, value=0.0, step=10.0)
water = st.number_input("Water (monthly est, £)", min_value=0.0, value=0.0, step=10.0)
admin = st.number_input("Administration (monthly, £)", min_value=0.0, value=0.0, step=10.0)
development = st.number_input("Development charge (monthly, £)", min_value=0.0, value=0.0, step=10.0)

# --- TOTAL COST TABLE ---
st.subheader("Summary Table")
cost_items = {
    "Prisoner wages (monthly)": prisoner_wages,
    "Electricity (monthly est)": electricity,
    "Gas (monthly est)": gas,
    "Water (monthly est)": water,
    "Administration (monthly)": admin,
    "Depreciation/Maintenance (monthly)": monthly_maintenance,
    "Development charge (monthly)": development,
}
total_monthly = sum(cost_items.values())

st.markdown(
    """
    <style>
    .cost-table td, .cost-table th {
        padding: 8px 16px;
        font-size: 1.08rem;
    }
    .cost-table {
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .cost-table tr:nth-child(even) {background: #f6f6f6;}
    .cost-table tr:last-child {font-weight: bold; background: #e6f4ea;}
    </style>
    """,
    unsafe_allow_html=True
)

table_html = "<table class='cost-table'><tr><th>Cost Item</th><th>Amount (£)</th></tr>"
for k, v in cost_items.items():
    table_html += f"<tr><td>{k}</td><td>£{v:,.2f}</td></tr>"
table_html += f"<tr><td>Total Monthly Cost</td><td>£{total_monthly:,.2f}</td></tr></table>"
st.markdown(table_html, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown(
    """
    <hr style="margin-top:40px;margin-bottom:10px;">
    <div style="color:#888;font-size:0.95rem;">
        &copy; 2025 New Futures Network | Cost and Price Calculator
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

# Cost and Price Calculator — NFN (Streamlit Cloud safe)
# v2.4 | 2025-09-22
# - Title + font size increased, white on NFN blue bar
# - Production settings only visible when Production mode is selected
# - Host summary text: "Host Contract for [Customer Name] — Costs are per month."
# - Removed "(monthly)" from Host line items; kept "(estimated)" only for energy/water
# - If development charge = £0 (Commercial + Both supports), show a highlight about the reduction
# - Excel export removed; CSV + PDF-ready HTML only
# - EUI slider removed; evidence-aligned EUI ordering; capacity badge retained

from pathlib import Path
from io import BytesIO
import pandas as pd
import streamlit as st

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# THEME: NFN blue header + GOV.UK green actions
# ----------------------------
NFN_BLUE = "#1D428A"
NFN_BLUE_DARK = "#153163"
GOV_GREEN = "#00703C"        # GOV.UK success green
GOV_GREEN_DARK = "#005A30"

st.markdown(
    f"""
<style>
/* Top bar */
.topbar {{
  position: sticky;
  top: 0;
  z-index: 999;
  background: {NFN_BLUE};
  border-bottom: 4px solid {NFN_BLUE_DARK};
  padding: .65rem 1rem;
  display: flex; align-items:center; gap:.75rem;
}}
.topbar .title {{
  color: #fff; font-weight: 800; letter-spacing:.2px; font-size: 2.05rem; margin:0;
}}

/* Area badge (GOV green) */
.area-badge {{
  background: {GOV_GREEN};
  color: #fff; font-weight: 700;
  padding: .4rem .6rem; border-radius: .5rem;
  display: inline-block; margin: .25rem 0 .75rem 0;
}}

/* Capacity preview badge (bigger + green border) */
.capacity-badge {{
  font-size: 1.05rem; font-weight: 700; line-height: 1.25;
  color: #0b0c0c; background: #f7fff9;
  border: 2px solid {GOV_GREEN}; border-radius: .5rem;
  padding: .55rem .8rem; display:inline-block; margin:.25rem 0 .75rem 0;
}}

/* Cost table */
table.cost {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}}
table.cost th {{
  background: #F3F4F6;
  text-align: left;
  padding: .6rem .5rem;
  border-bottom: 1px solid #E5E7EB;
}}
table.cost td {{
  padding: .55rem .5rem;
  border-top: 1px solid #E5E7EB;
}}
table.cost tr.total td {{
  font-weight: 700;
  border-top: 2px solid #111827;
}}

/* Primary buttons in GOV.UK green */
div.stButton > button[kind="primary"] {{
  background: {GOV_GREEN} !important;
  color: #fff !important;
  border: 0 !important;
}}
div.stButton > button[kind="primary"]:hover {{
  background: {GOV_GREEN_DARK} !important;
}}

/* Inline error hint */
.error-text {{
  color: #B10E1E; font-weight: 600; margin-top: .15rem; display:block;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# HEADER (no logo; white title on NFN blue)
# ----------------------------
def render_header():
    st.markdown(
        """
<div class="topbar">
  <span class="title">Cost and Price Calculator</span>
</div>
""",
        unsafe_allow_html=True,
    )
render_header()

# ----------------------------
# CONSTANTS (tariffs overrideable in sidebar)
# ----------------------------
ELECTRICITY_RATE_DEFAULT = 0.22  # £/kWh (override below)
GAS_RATE_DEFAULT = 0.05          # £/kWh
WATER_RATE_DEFAULT = 2.00        # £/m³

# Evidence-aligned EUI mapping (kWh/m²/year).
# Relative pattern reflects ND-NEED/BEES: warehouses lowest; high-process highest.
EUI_MAP = {
    "Empty/basic (warehouse)": {"electric_kwh_m2_y": 35, "gas_kwh_m2_y": 30},
    "Light industrial":        {"electric_kwh_m2_y": 45, "gas_kwh_m2_y": 60},
    "Factory (typical)":       {"electric_kwh_m2_y": 30, "gas_kwh_m2_y": 70},
    "High energy process":     {"electric_kwh_m2_y": 60, "gas_kwh_m2_y": 100},
}

# PRISON → REGION mapping (auto-fill)
PRISON_TO_REGION = {
    "Altcourse": "National", "Ashfield": "National", "Askham Grange": "National", "Aylesbury": "National",
    "Bedford": "National", "Belmarsh": "Inner London", "Berwyn": "National", "Birmingham": "National",
    "Brinsford": "National", "Bristol": "National", "Brixton": "Inner London", "Bronzefield": "Outer London",
    "Buckley Hall": "National", "Bullingdon": "National", "Bure": "National", "Cardiff": "National",
    "Channings Wood": "National", "Chelmsford": "National", "Coldingley": "Outer London", "Cookham Wood": "National",
    "Dartmoor": "National", "Deerbolt": "National", "Doncaster": "National", "Dovegate": "National",
    "Downview": "Outer London", "Drake Hall": "National", "Durham": "National", "East Sutton Park": "National",
    "Eastwood Park": "National", "Elmley": "National", "Erlestoke": "National", "Exeter": "National",
    "Featherstone": "National", "Feltham A": "Outer London", "Feltham B": "Outer London", "Five Wells": "National",
    "Ford": "National", "Forest Bank": "National", "Fosse Way": "National", "Foston Hall": "National",
    "Frankland": "National", "Full Sutton": "National", "Garth": "National", "Gartree": "National",
    "Grendon": "National", "Guys Marsh": "National", "Hatfield": "National", "Haverigg": "National",
    "Hewell": "National", "High Down": "Outer London", "Highpoint": "National", "Hindley": "National",
    "Hollesley Bay": "National", "Holme House": "National", "Hull": "National", "Humber": "National",
    "Huntercombe": "National", "Isis": "Inner London", "Isle of Wight": "National", "Kirkham": "National",
    "Kirklevington Grange": "National", "Lancaster Farms": "National", "Leeds": "National", "Leicester": "National",
    "Lewes": "National", "Leyhill": "National", "Lincoln": "National", "Lindholme": "National",
    "Littlehey": "National", "Liverpool": "National", "Long Lartin": "National", "Low Newton": "National",
    "Lowdham Grange": "National", "Maidstone": "National", "Manchester": "National", "Moorland": "National",
    "Morton Hall": "National", "The Mount": "National", "New Hall": "National", "North Sea Camp": "National",
    "Northumberland": "National", "Norwich": "National", "Nottingham": "National", "Oakwood": "National",
    "Onley": "National", "Parc": "National", "Parc (YOI)": "National", "Pentonville": "Inner London",
    "Peterborough Female": "National", "Peterborough Male": "National", "Portland": "National", "Prescoed": "National",
    "Preston": "National", "Ranby": "National", "Risley": "National", "Rochester": "National", "Rye Hill": "National",
    "Send": "National", "Spring Hill": "National", "Stafford": "National", "Standford Hill": "National",
    "Stocken": "National", "Stoke Heath": "National", "Styal": "National", "Sudbury": "National",
    "Swaleside": "National", "Swansea": "National", "Swinfen Hall": "National", "Thameside": "Inner London",
    "Thorn Cross": "National", "Usk": "National", "Verne": "National", "Wakefield": "National",
    "Wandsworth": "Inner London", "Warren Hill": "National", "Wayland": "National", "Wealstun": "National",
    "Werrington": "National", "Wetherby": "National", "Whatton": "National", "Whitemoor": "National",
    "Winchester": "National", "Woodhill": "Inner London", "Wormwood Scrubs": "Inner London", "Wymott": "National",
}

# ----------------------------
# RESET
# ----------------------------
if st.button("Reset App"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# ----------------------------
# SIDEBAR: Tariffs & Overheads
# ----------------------------
with st.sidebar:
    st.header("Tariffs & Overheads")

    electricity_rate = st.number_input(
        "Electricity tariff (€/£ per kWh)",
        min_value=0.0, value=ELECTRICITY_RATE_DEFAULT, step=0.01, format="%.2f",
    )
    gas_rate = st.number_input(
        "Gas tariff (€/£ per kWh)",
        min_value=0.0, value=GAS_RATE_DEFAULT, step=0.01, format="%.2f",
    )
    water_rate = st.number_input(
        "Water tariff (€/£ per m³)",
        min_value=0.0, value=WATER_RATE_DEFAULT, step=0.10, format="%.2f",
    )

    st.markdown("---")
    # Maintenance/Depreciation
    maint_method = st.radio(
        "Maintenance/Depreciation method",
        ["Set a fixed monthly amount", "% of reinstatement value", "£/m² per year"],
        index=2,
    )

    maint_monthly = 0.0
    if maint_method == "Set a fixed monthly amount":
        maint_monthly = st.number_input(
            "Maintenance (monthly)", min_value=0.0, value=0.0, step=50.0
        )
    elif maint_method == "% of reinstatement value":
        reinstatement_value = st.number_input(
            "Reinstatement value (£)", min_value=0.0, value=0.0, step=10000.0
        )
        percent = st.number_input(
            "Annual % of reinstatement value", min_value=0.0, value=2.0, step=0.25, format="%.2f"
        )
        maint_monthly = (reinstatement_value * (percent / 100.0)) / 12.0
    else:
        rate_per_m2_y = st.number_input(
            "Maintenance rate (£/m²/year)", min_value=0.0, value=15.0, step=1.0
        )
        st.session_state["maint_rate_per_m2_y"] = rate_per_m2_y

    st.markdown("---")
    admin_monthly = st.number_input(
        "Administration (monthly)", min_value=0.0, value=150.0, step=25.0
    )

# ----------------------------
# BASE INPUTS (inline hints)
# ----------------------------
st.subheader("Inputs")

prisons_sorted = ["Select"] + sorted(PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0)
if prison_choice == "Select":
    st.markdown('<span class="error-text">Please select a prison.</span>', unsafe_allow_html=True)

region = PRISON_TO_REGION.get(prison_choice, "Select") if prison_choice != "Select" else "Select"
st.text_input("Region", value=("" if region == "Select" else region), disabled=True)
if region == "Select":
    st.markdown('<span class="error-text">Region could not be derived from the prison selection.</span>', unsafe_allow_html=True)

customer_type = st.selectbox("I want to quote for", ["Select", "Commercial", "Another Government Department"])
if customer_type == "Select":
    st.markdown('<span class="error-text">Please choose the customer type.</span>', unsafe_allow_html=True)

customer_name = st.text_input("Customer Name")
if not str(customer_name).strip():
    st.markdown('<span class="error-text">Enter the customer name.</span>', unsafe_allow_html=True)

workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"])
if workshop_mode == "Select":
    st.markdown('<span class="error-text">Select contract type.</span>', unsafe_allow_html=True)

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
workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS)
if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area_ft2 = width * length
else:
    area_ft2 = size_map.get(workshop_size, 0)
if area_ft2 <= 0:
    st.markdown('<span class="error-text">Area must be greater than zero.</span>', unsafe_allow_html=True)

# Highlight ft² and m²
area_m2 = area_ft2 * 0.092903
st.markdown(
    f'<div class="area-badge">Calculated area: {area_ft2:,.0f} ft² · {area_m2:,.0f} m²</div>',
    unsafe_allow_html=True,
)

workshop_energy_types = list(EUI_MAP.keys())
workshop_type = st.selectbox("Workshop type?", ["Select"] + workshop_energy_types)
if workshop_type == "Select":
    st.markdown('<span class="error-text">Select workshop type.</span>', unsafe_allow_html=True)

workshop_hours = st.number_input("How many hours per week is it open? (for production calc)", min_value=0.0, format="%.2f")
if workshop_hours <= 0:
    st.markdown('<span class="error-text">Enter weekly hours > 0.</span>', unsafe_allow_html=True)

num_prisoners = st.number_input("How many prisoners employed?", min_value=0)
if num_prisoners <= 0:
    st.markdown('<span class="error-text">Enter prisoners employed > 0.</span>', unsafe_allow_html=True)

prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")
if prisoner_salary <= 0:
    st.markdown('<span class="error-text">Enter prisoner salary > 0.</span>', unsafe_allow_html=True)

# Supervisors
num_supervisors = st.number_input("How many supervisors?", min_value=0)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s)?")

supervisor_salaries = []
recommended_pct = 0
if not customer_covers_supervisors:
    for i in range(int(num_supervisors)):
        sup_salary = st.number_input(
            f"Supervisor {i+1} annual salary (£)",
            min_value=0.0, format="%.2f", key=f"sup_salary_{i}"
        )
        supervisor_salaries.append(sup_salary)
    contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=1, value=1)
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if contracts and workshop_hours >= 0 else 0
    st.subheader("Supervisor Time Allocation")
    st.info(f"Recommended: {recommended_pct}%")
    chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), key="chosen_pct")
else:
    chosen_pct = 0

# Development charge (Commercial only)
dev_charge = 0.0
support = "Select"
if customer_type == "Commercial":
    support = st.selectbox("Customer employment support?", ["Select", "None", "Employment on release/RoTL", "Post release", "Both"])
    if support == "None":
        dev_charge = 0.20
    elif support in ["Employment on release/RoTL", "Post release"]:
        dev_charge = 0.10
    elif support == "Both":
        dev_charge = 0.0  # Waived when both supports are provided

# Pricing (Commercial): VAT only (no margin)
st.markdown("---")
st.subheader("Pricing (Commercial)")
colp1, colp2 = st.columns([1,1])
with colp1:
    apply_vat = st.checkbox("Apply VAT?")
with colp2:
    vat_rate = st.number_input("VAT rate %", min_value=0.0, max_value=100.0, value=20.0, step=0.5, format="%.1f")

st.caption(
    "Unit Cost includes labour + apportioned supervisors + apportioned overheads. "
    "With no margin, Unit Price (ex VAT) = Unit Cost. "
    "If VAT is ticked and customer is Commercial, Unit Price (inc VAT) = ex VAT × (1 + VAT%)."
)

# ----------------------------
# VALIDATION
# ----------------------------
def validate_inputs():
    errors = []
    if prison_choice == "Select":
        errors.append("Select prison")
    if region == "Select":
        errors.append("Region could not be derived from prison selection")
    if customer_type == "Select":
        errors.append("Select customer type")
    if not str(customer_name).strip():
        errors.append("Enter customer name")
    if workshop_mode == "Select":
        errors.append("Select contract type")
    if workshop_size == "Select":
        errors.append("Select workshop size")
    if workshop_type == "Select":
        errors.append("Select workshop type")
    if area_ft2 <= 0:
        errors.append("Area must be greater than zero")
    if workshop_hours <= 0:
        errors.append("Hours per week must be > 0")
    if num_prisoners <= 0:
        errors.append("Enter prisoners employed (>0)")
    if prisoner_salary <= 0:
        errors.append("Enter prisoner salary (>0)")
    if not customer_covers_supervisors:
        if num_supervisors <= 0:
            errors.append("Enter number of supervisors")
        if any(s <= 0 for s in supervisor_salaries):
            errors.append("Enter all supervisor salaries (>0)")
    return errors

# ----------------------------
# COST HELPERS
# ----------------------------
def monthly_energy_costs():
    """EUI (kWh/m²/y) × area (m²) × tariff ÷ 12. Using fixed EUI values (no multiplier)."""
    eui = EUI_MAP.get(workshop_type, None)
    if not eui:
        return 0.0, 0.0
    elec_kwh_y = eui["electric_kwh_m2_y"] * area_m2
    gas_kwh_y  = eui["gas_kwh_m2_y"]  * area_m2
    elec_cost_m = (elec_kwh_y / 12.0) * electricity_rate
    gas_cost_m  = (gas_kwh_y  / 12.0) * gas_rate
    return elec_cost_m, gas_cost_m

def monthly_water_costs():
    """Simple people-based benchmark: ~15 L/person/day, 5 days/week."""
    persons = num_prisoners + (0 if customer_covers_supervisors else num_supervisors)
    litres_per_day = 15.0
    days_per_week = 5.0
    weeks_per_year = 52.0
    m3_per_year = (persons * litres_per_day * days_per_week * weeks_per_year) / 1000.0
    return (m3_per_year / 12.0) * water_rate

def weekly_overheads_total():
    """Electricity, gas, water, admin, maintenance → weekly total + breakdown."""
    if maint_method == "£/m² per year":
        rate = st.session_state.get("maint_rate_per_m2_y", 15.0)
        maint_m = (rate * area_m2) / 12.0
    else:
        maint_m = maint_monthly

    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()

    overheads_m = elec_m + gas_m + water_m + admin_monthly + maint_m
    return overheads_m * 12.0 / 52.0, {
        "Electricity (m)": elec_m, "Gas (m)": gas_m, "Water (m)": water_m,
        "Admin (m)": admin_monthly, "Maintenance (m)": maint_m
    }

# ----------------------------
# HOST COSTS (monthly)
# ----------------------------
def calculate_host_costs():
    breakdown = {}

    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52 / 12)

    supervisor_cost = 0.0
    if not customer_covers_supervisors:
        supervisor_cost = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
    breakdown["Supervisors"] = supervisor_cost

    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()
    breakdown["Electricity (estimated)"] = elec_m
    breakdown["Gas (estimated)"] = gas_m
    breakdown["Water (estimated)"] = water_m

    breakdown["Administration"] = admin_monthly

    if maint_method == "£/m² per year":
        rate = st.session_state.get("maint_rate_per_m2_y", 15.0)
        breakdown["Depreciation/Maintenance"] = (rate * area_m2) / 12.0
    else:
        breakdown["Depreciation/Maintenance"] = maint_monthly

    # Development charge (if Commercial)
    breakdown["Development charge"] = supervisor_cost * dev_charge if customer_type == "Commercial" else 0.0

    subtotal = sum(breakdown.values())

    # VAT only (no margin)
    vat_amount = (subtotal * (vat_rate / 100.0)) if (customer_type == "Commercial" and apply_vat) else 0.0
    grand_total = subtotal + vat_amount

    totals = {
        "Subtotal": subtotal,
        "VAT %": vat_rate if (customer_type == "Commercial" and apply_vat) else 0.0,
        "VAT (£)": vat_amount if (customer_type == "Commercial" and apply_vat) else 0.0,
        "Grand Total (£/month)": grand_total,
    }
    return breakdown, totals

# ----------------------------
# DISPLAY HELPERS
# ----------------------------
def display_table(breakdown: dict, totals: dict | None = None, total_label="Total"):
    html = """
<table class="cost">
<tr>
  <th>Cost Item</th>
  <th>Amount (£)</th>
</tr>
"""
    for k, v in breakdown.items():
        html += f"""
<tr>
  <td>{k}</td>
  <td>£{v:,.2f}</td>
</tr>
"""
    total = sum(breakdown.values())
    html += f"""
<tr class="total">
  <td>{total_label}</td>
  <td>£{total:,.2f}</td>
</tr>
"""
    if totals:
        html += f"""
<tr>
  <td>VAT ({totals.get('VAT %',0):.1f}%)</td>
  <td>£{totals.get('VAT (£)',0):,.2f}</td>
</tr>
<tr class="total">
  <td>Grand Total (£/month)</td>
  <td>£{totals.get('Grand Total (£/month)',0):,.2f}</td>
</tr>
"""
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

def to_dataframe_host(breakdown: dict, totals: dict) -> pd.DataFrame:
    rows = list(breakdown.items())
    rows += [
        ("Subtotal", sum(breakdown.values())),
        (f"VAT ({totals.get('VAT %',0):.1f}%)", totals.get("VAT (£)",0)),
        ("Grand Total (£/month)", totals.get("Grand Total (£/month)",0)),
    ]
    return pd.DataFrame(rows, columns=["Item", "Amount (£)"])

def to_dataframe_production(results: list[dict]) -> pd.DataFrame:
    cols = ["Item", "Output %", "Units/week", "Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]
    df = pd.DataFrame([{c: r.get(c) for c in cols} for r in results])
    for c in ["Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: None if x is None else round(float(x), 2))
    return df

# ----------------------------
# EXPORT HELPERS (CSV, HTML)
# ----------------------------
def export_csv_bytes(df: pd.DataFrame) -> BytesIO:
    b = BytesIO()
    df.to_csv(b, index=False)
    b.seek(0)
    return b

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="NFN Quote") -> BytesIO:
    def df_to_html(df: pd.DataFrame) -> str:
        return df.to_html(index=False, border=0).replace('<table border="0" class="dataframe">', '<table class="cost">')

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; }}
.top {{ background:{NFN_BLUE}; border-bottom:4px solid {NFN_BLUE_DARK}; color:#fff; padding:10px 12px; display:flex; align-items:center; gap:8px; }}
h1 {{ font-size: 22px; margin: 0; }}
table.cost {{
  width:100%; border-collapse: collapse; font-size: 14px; margin-top: 10px;
}}
table.cost th {{
  background:#F3F4F6; text-align:left; padding:8px; border-bottom:1px solid #E5E7EB;
}}
table.cost td {{
  padding:8px; border-top:1px solid #E5E7EB;
}}
</style>
</head>
<body>
<div class="top"><h1>Cost and Price Calculator — Quote</h1></div>
<p><strong>Customer:</strong> {customer_name or ''} &nbsp; &nbsp; <strong>Prison:</strong> {prison_choice or ''} &nbsp; &nbsp; <strong>Region:</strong> {region or ''}</p>
"""
    if host_df is not None:
        html += "<h2>Host Costs (per month)</h2>" + df_to_html(host_df)
    if prod_df is not None:
        html += "<h2>Production Items</h2>" + df_to_html(prod_df)
    html += "</body></html>"

    b = BytesIO(html.encode("utf-8"))
    b.seek(0)
    return b

# ----------------------------
# UI: Host vs Production
# ----------------------------
errors = validate_inputs()

if workshop_mode == "Host":
    if st.button("Generate Costs", type="primary"):
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            st.subheader(f"Host Contract for {customer_name or '—'} — Costs are per month.")
            breakdown, totals = calculate_host_costs()

            # Highlight reduction if dev charge waived (Commercial + Both)
            if customer_type == "Commercial" and support == "Both":
                if breakdown.get("Development charge", 0) == 0:
                    st.success("Development charge is **£0** — a reduction has been applied for the support offered (Both).")

            display_table(breakdown, totals, total_label="Subtotal")

            # Exports (CSV + HTML only)
            host_df = to_dataframe_host(breakdown, totals)
            st.download_button("Download CSV (Host)", data=export_csv_bytes(host_df), file_name="NFN_host_quote.csv",
                               mime="text/csv")
            st.download_button("Download PDF-ready HTML (Host)",
                               data=export_html(host_df, None, "NFN Host Quote"),
                               file_name="NFN_host_quote.html", mime="text/html")

elif workshop_mode == "Production":
    # --- Production settings appear ONLY in Production mode ---
    st.subheader("Production Settings")
    apportion_rule = st.radio(
        "How should we share overheads and supervisor cost between items?",
        ["By labour minutes (capacity @ 100%)", "By assigned prisoners"],
        index=0,
    )
    with st.expander("What does this mean (plain English)?", expanded=False):
        st.markdown(
            """
**By labour minutes (capacity @ 100%) — recommended**  
We look at the **minutes of labour** each item *could* have in a full week if everyone is busy:  
**assigned prisoners × weekly hours × 60**.  
If Item A has more labour minutes than Item B, **Item A takes a bigger share** of overheads and supervisor time.  
*Example:* Item A (3 prisoners) at 37.5h → 6,750 mins; Item B (1 prisoner) → 2,250 mins, so A takes **3×** the share.

**By assigned prisoners**  
We just count heads. If an item has **3 prisoners** and another has **1**, the first gets **3×** the share — even if one item’s units take longer to make.

Either way, when you **turn Output % down**, you make **fewer units**, so **cost per unit goes up** (same weekly costs spread over fewer units).
            """
        )

    st.subheader("Production Contract Costs")
    num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")
    items = []
    for i in range(int(num_items)):
        with st.expander(f"Item {i+1} details", expanded=(i == 0)):
            name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
            prisoners_required = st.number_input(
                f"Prisoners required to make 1 item (Item {i+1})", min_value=1, value=1, step=1, key=f"req_{i}"
            )
            minutes_per_item = st.number_input(
                f"How many minutes to make 1 item (Item {i+1})", min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}"
            )
            prisoners_assigned = st.number_input(
                f"How many prisoners work solely on this item (Item {i+1})",
                min_value=0, max_value=int(num_prisoners), value=0, step=1, key=f"assigned_{i}"
            )
            items.append({
                "name": name,
                "required": int(prisoners_required),
                "minutes": float(minutes_per_item),
                "assigned": int(prisoners_assigned)
            })

    if errors:
        st.error("Fix errors before production calculations:\n- " + "\n- ".join(errors))
    else:
        # Overheads (weekly) + supervisor total forAbsolutely

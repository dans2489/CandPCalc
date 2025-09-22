import streamlit as st
from pathlib import Path

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Prison Workshop Costing Tool", layout="wide")

# ------------------------------
# THEME: NFN blue header + GOV.UK green actions
# ------------------------------
NFN_BLUE = "#1D428A"
NFN_BLUE_DARK = "#153163"
GOV_GREEN = "#00703C"   # GOV.UK green
GOV_GREEN_DARK = "#005A30"
GOV_FOCUS = "#FFDD00"   # GOV.UK focus yellow

st.markdown(
    f"""
    <style>
        :root {{
            --nfn-blue: {NFN_BLUE};
            --nfn-blue-dark: {NFN_BLUE_DARK};
            --gov-green: {GOV_GREEN};
            --gov-green-dark: {GOV_GREEN_DARK};
            --gov-focus: {GOV_FOCUS};
        }}
        .nfn-title {{
            margin: 0; color: var(--nfn-blue);
            font-size: 1.6rem; font-weight: 700;
            padding-bottom: 4px;
            border-bottom: 3px solid var(--nfn-blue);
            margin-bottom: 8px;
        }}
        .stButton > button[kind="primary"] {{
            background-color: var(--gov-green) !important;
            border: 1px solid var(--gov-green) !important;
            color: #fff !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: var(--gov-green-dark) !important;
            border-color: var(--gov-green-dark) !important;
        }}
        .stButton > button:focus,
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stSelectbox [data-baseweb="select"] div:focus,
        .stSlider [role="slider"]:focus {{
            outline: 3px solid var(--gov-focus) !important;
            outline-offset: 0 !important;
            box-shadow: 0 0 0 3px var(--gov-focus) inset !important;
        }}
        .stButton > button:not([kind="primary"]) {{
            border: 1px solid var(--nfn-blue) !important;
            color: var(--nfn-blue) !important;
            background: #fff !important;
        }}
        .stButton > button:not([kind="primary"]):hover {{
            background: rgba(29,66,138,0.08) !important;
        }}
        .st-expanderHeader, .stExpander > details > summary {{
            color: var(--nfn-blue) !important;
            font-weight: 600 !important;
        }}
        a, a:visited {{ color: var(--nfn-blue); }}
        input[disabled], .stTextInput [disabled] {{ color: #333 !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# LOGO (URL -> local -> text link)
# ------------------------------
def render_header():
    logo_url = st.session_state.get("nfn_logo_url", "").strip()
    local_logo = Path("assets/nfn_logo.png")

    c_logo, c_title = st.columns([1, 8])
    with c_logo:
        shown = False
        if logo_url:
            try:
                st.image(logo_url, use_column_width=True); shown = True
            except Exception:
                pass
        if not shown and local_logo.exists():
            try:
                st.image(str(local_logo), use_column_width=True); shown = True
            except Exception:
                pass
        if not shown:
            st.markdown(
                '<div style="font-weight:700;"><a href="https://newfuturesnetwork.gov.uk/" target="_blank">New Futures Network</a></div>',
                unsafe_allow_html=True,
            )
    with c_title:
        st.markdown('<div class="nfn-title">Prison Workshop Costing Tool</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Brand options")
    st.text_input(
        "Logo URL (optional – paste a direct image URL)",
        key="nfn_logo_url",
        placeholder="https://newfuturesnetwork.gov.uk/.../logo.png",
        help="Leave blank to use local file at assets/nfn_logo.png."
    )

render_header()

# ------------------------------
# CONSTANTS (tariffs are overrideable in sidebar)
# Defaults set from DESNZ/ONS ranges for 2024–25 non-domestic sector. [4](https://assets.publishing.service.gov.uk/media/667c38215b0d63b556a4b3d2/quarterly-energy-prices-june-2024.pdf)[5](https://assets.publishing.service.gov.uk/media/6762955acdb5e64b69e30703/quarterly-energy-prices-december-2024.pdf)[6](https://www.ons.gov.uk/economy/economicoutputandproductivity/output/articles/theimpactofhigherenergycostsonukbusinesses/2021to2024)
# ------------------------------
ELECTRICITY_RATE_DEFAULT = 0.22  # £/kWh (override below)
GAS_RATE_DEFAULT = 0.05          # £/kWh (override below)
WATER_RATE_DEFAULT = 2.00        # £/m³ (keep but overrideable)

# Evidence-based energy-intensity (EUI) mapping by workshop type
# kWh/m²/year – baselines from ND-NEED/BEES context (warehouses/factories),
# with pragmatic roundings and an adjustable multiplier slider. [1](https://assets.publishing.service.gov.uk/media/62bc5a35d3bf7f2915159f64/non_domestic_need_data_framework_2022.pdf)[2](https://www.gov.uk/government/publications/building-energy-efficiency-survey-bees)
EUI_MAP = {
    "Empty/basic":   {"electric_kwh_m2_y": 53, "gas_kwh_m2_y": 41},  # Warehouse (illustrative BEES/ND-NEED)
    "Low energy":    {"electric_kwh_m2_y": 40, "gas_kwh_m2_y": 60},  # Light industrial blend
    "Medium energy": {"electric_kwh_m2_y": 28, "gas_kwh_m2_y": 72},  # Factory median (ND-NEED indicative)
    "High energy":   {"electric_kwh_m2_y": 40, "gas_kwh_m2_y": 90},  # Higher process load (uplift)
}

# ------------------------------
# PRISON → REGION mapping (auto-fill)
# ------------------------------
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
    "Lewes": "National", "Leyhill": "National", "Lincoln": "National", "Lindholme": "National", "Littlehey": "National",
    "Liverpool": "National", "Long Lartin": "National", "Low Newton": "National", "Lowdham Grange": "National",
    "Maidstone": "National", "Manchester": "National", "Moorland": "National", "Morton Hall": "National",
    "The Mount": "National", "New Hall": "National", "North Sea Camp": "National", "Northumberland": "National",
    "Norwich": "National", "Nottingham": "National", "Oakwood": "National", "Onley": "National", "Parc": "National",
    "Parc (YOI)": "National", "Pentonville": "Inner London", "Peterborough Female": "National",
    "Peterborough Male": "National", "Portland": "National", "Prescoed": "National", "Preston": "National",
    "Ranby": "National", "Risley": "National", "Rochester": "National", "Rye Hill": "National", "Send": "National",
    "Spring Hill": "National", "Stafford": "National", "Standford Hill": "National", "Stocken": "National",
    "Stoke Heath": "National", "Styal": "National", "Sudbury": "National", "Swaleside": "National", "Swansea": "National",
    "Swinfen Hall": "National", "Thameside": "Inner London", "Thorn Cross": "National", "Usk": "National",
    "Verne": "National", "Wakefield": "National", "Wandsworth": "Inner London", "Warren Hill": "National",
    "Wayland": "National", "Wealstun": "National", "Werrington": "National", "Wetherby": "National",
    "Whatton": "National", "Whitemoor": "National", "Winchester": "National", "Woodhill": "National",
    "Wormwood Scrubs": "Inner London", "Wymott": "National",
}

# ------------------------------
# RESET
# ------------------------------
if st.button("Reset App"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try: st.rerun()
    except Exception: st.experimental_rerun()

# ------------------------------
# SIDEBAR: tariffs & maintenance method
# ------------------------------
with st.sidebar:
    st.header("Tariffs & Overheads")
    electricity_rate = st.number_input("Electricity tariff (€/£ per kWh)", min_value=0.0, value=ELECTRICITY_RATE_DEFAULT, step=0.01, format="%.2f")
    gas_rate = st.number_input("Gas tariff (€/£ per kWh)", min_value=0.0, value=GAS_RATE_DEFAULT, step=0.01, format="%.2f")
    water_rate = st.number_input("Water tariff (€/£ per m³)", min_value=0.0, value=WATER_RATE_DEFAULT, step=0.10, format="%.2f")
    st.caption("Tariff defaults reflect recent UK non-domestic price ranges; adjust to your contract. [4](https://assets.publishing.service.gov.uk/media/667c38215b0d63b556a4b3d2/quarterly-energy-prices-june-2024.pdf)[5](https://assets.publishing.service.gov.uk/media/6762955acdb5e64b69e30703/quarterly-energy-prices-december-2024.pdf)[6](https://www.ons.gov.uk/economy/economicoutputandproductivity/output/articles/theimpactofhigherenergycostsonukbusinesses/2021to2024)")

    st.markdown("---")
    maint_method = st.radio(
        "Maintenance/Depreciation method",
        ["Set a fixed monthly amount", "% of reinstatement value", "£/m² per year"],
        index=0,
    )
    maint_monthly = 0.0
    if maint_method == "Set a fixed monthly amount":
        maint_monthly = st.number_input("Maintenance (monthly)", min_value=0.0, value=0.0, step=50.0)
        st.caption("Basis: policy input. For formal planning see RICS NRM3; for reinstatement values see BCIS. [8](https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/nrm)[9](https://bcis.co.uk/products/construction/reinstatement_costs/)")
    elif maint_method == "% of reinstatement value":
        reinstatement_value = st.number_input("Reinstatement value (£)", min_value=0.0, value=0.0, step=10000.0)
        percent = st.number_input("Annual % of reinstatement value", min_value=0.0, value=2.0, step=0.25, format="%.2f")
        maint_monthly = (reinstatement_value * (percent/100.0)) / 12.0
        st.caption("Guidance: plan maintenance against asset value per RICS NRM3; total maintenance often targeted ≤3% of RAV. [8](https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/nrm)[11](https://reliabilityweb.com/en/best-practices-maintenance-benchmarks)")
    else:
        rate_per_m2_y = st.number_input("Maintenance rate (£/m²/year)", min_value=0.0, value=0.0, step=1.0)
        st.session_state["maint_rate_per_m2_y"] = rate_per_m2_y  # used later

    st.markdown("---")
    admin_monthly = st.number_input("Administration (monthly)", min_value=0.0, value=150.0, step=25.0)
    st.caption("Fixed admin default £150/month. Set your policy value.")

# ------------------------------
# BASE INPUTS (labels exactly as requested)
# ------------------------------
prisons_sorted = ["Select"] + sorted(PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0)
region = PRISON_TO_REGION.get(prison_choice, "Select") if prison_choice != "Select" else "Select"
st.text_input("Region", value=("" if region == "Select" else region), disabled=True)

customer_type = st.selectbox("I want to quote for", ["Select", "Commercial", "Another Government Department"])
customer_name = st.text_input("Customer Name")
workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"])

SIZE_LABELS = [
    "Select",
    "Small (~2,500 ft², ~50×50 ft)",
    "Medium (~5,000 ft²)",
    "Large (~10,000 ft²)",
    "Enter dimensions in ft",
]
size_map = {"Small (~2,500 ft², ~50×50 ft)": 2500, "Medium (~5,000 ft²)": 5000, "Large (~10,000 ft²)": 10000}
workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS)

if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area_ft2 = width * length
else:
    area_ft2 = size_map.get(workshop_size, 0)

# Show ft² and m² clearly
area_m2 = area_ft2 * 0.092903
st.markdown(f"**Calculated area:** {area_ft2:,.0f} ft²  ·  {area_m2:,.0f} m²")

workshop_energy_types = list(EUI_MAP.keys())
workshop_type = st.selectbox("Workshop type?", ["Select"] + workshop_energy_types)
# Let user adjust intensity ±50% to reflect local processes/shift patterns.
eui_multiplier = st.slider("Energy intensity adjustment (×)", 0.5, 1.5, 1.0, 0.05)

workshop_hours = st.number_input("How many hours per week is it open? (for production calc)", min_value=0.0, format="%.2f")

num_prisoners = st.number_input("How many prisoners employed?", min_value=0)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")

num_supervisors = st.number_input("How many supervisors?", min_value=0)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s)?")

supervisor_salaries = []
recommended_pct = 0
if not customer_covers_supervisors:
    for i in range(int(num_supervisors)):
        sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, format="%.2f", key=f"sup_salary_{i}")
        supervisor_salaries.append(sup_salary)
    contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=1, value=1)
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if contracts and workshop_hours >= 0 else 0
    st.subheader("Supervisor Time Allocation")
    st.info(f"Recommended: {recommended_pct}%")
    chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), key="chosen_pct")
else:
    chosen_pct = 0

dev_charge = 0.0
if customer_type == "Commercial":
    support = st.selectbox("Customer employment support?", ["Select", "None", "Employment on release/RoTL", "Post release", "Both"])
    if support == "None": dev_charge = 0.20
    elif support in ["Employment on release/RoTL", "Post release"]: dev_charge = 0.10
    else: dev_charge = 0.0

reason_for_low_pct = ""
if not customer_covers_supervisors and chosen_pct < recommended_pct:
    reason_for_low_pct = st.text_area("Explain why choosing lower supervisor % allocation:")

# ------------------------------
# VALIDATION
# ------------------------------
def validate_inputs():
    errors = []
    if prison_choice == "Select": errors.append("Select prison")
    if region == "Select": errors.append("Region could not be derived from prison selection")
    if customer_type == "Select": errors.append("Select customer type")
    if not str(customer_name).strip(): errors.append("Enter customer name")
    if workshop_mode == "Select": errors.append("Select contract type")
    if workshop_size == "Select": errors.append("Select workshop size")
    if workshop_type == "Select": errors.append("Select workshop type")
    if area_ft2 <= 0: errors.append("Area must be greater than zero")
    if workshop_hours < 0: errors.append("Hours per week cannot be negative")
    if num_prisoners <= 0: errors.append("Enter prisoners employed")
    if prisoner_salary <= 0: errors.append("Enter prisoner salary")
    if not customer_covers_supervisors:
        if num_supervisors <= 0: errors.append("Enter number of supervisors")
        if any(s <= 0 for s in supervisor_salaries): errors.append("Enter all supervisor salaries")
        if chosen_pct < recommended_pct and not str(reason_for_low_pct).strip(): errors.append("Provide reason for low supervisor %")
    return errors

# ------------------------------
# OVERHEAD CALCS (evidence-based)
# ------------------------------
def monthly_energy_costs():
    """Use EUI (kWh/m²/y) × area (m²) × tariff ÷ 12. EUIs are mapped to workshop type and adjustable via multiplier."""
    eui = EUI_MAP.get(workshop_type, None)
    if not eui: return 0.0, 0.0
    elec_kwh_y = eui_multiplier * eui["electric_kwh_m2_y"] * area_m2
    gas_kwh_y  = eui_multiplier * eui["gas_kwh_m2_y"] * area_m2
    elec_cost_m = (elec_kwh_y / 12.0) * electricity_rate
    gas_cost_m  = (gas_kwh_y  / 12.0) * gas_rate
    return elec_cost_m, gas_cost_m

def monthly_water_costs():
    """
    Sanitary water benchmarked around 15 L/person/day (office baseline). Process water can be added separately.
    Defaults to 5 days/week usage for workshop. [7](https://waterwise.org.uk/app/uploads/2025/02/The-Waterwise-Guide-for-Offices.pdf)
    """
    persons = num_prisoners + (0 if customer_covers_supervisors else num_supervisors)
    litres_per_day = 15.0
    days_per_week = 5.0
    weeks_per_year = 52.0
    m3_per_year = (persons * litres_per_day * days_per_week * weeks_per_year) / 1000.0
    return (m3_per_year / 12.0) * water_rate

# ------------------------------
# HOST COSTS
# ------------------------------
def calculate_host_costs():
    breakdown = {}
    breakdown["Prisoner wages (monthly)"] = num_prisoners * prisoner_salary * (52/12)

    supervisor_cost = 0.0
    if not customer_covers_supervisors:
        supervisor_cost = sum([(s/12) * (chosen_pct / 100) for s in supervisor_salaries])
        breakdown["Supervisors (monthly)"] = supervisor_cost

    # Energy (evidence-based EUI)
    elec_m, gas_m = monthly_energy_costs()
    breakdown["Electricity (monthly est)"] = elec_m
    breakdown["Gas (monthly est)"] = gas_m

    # Water (people-based benchmark)
    breakdown["Water (monthly est)"] = monthly_water_costs()

    # Administration (policy input)
    breakdown["Administration (monthly)"] = admin_monthly

    # Maintenance/Depreciation (method chosen)
    if maint_method == "£/m² per year":
        rate = st.session_state.get("maint_rate_per_m2_y", 0.0)
        breakdown["Depreciation/Maintenance (monthly)"] = (rate * area_m2) / 12.0
    else:
        breakdown["Depreciation/Maintenance (monthly)"] = maint_monthly

    # Regional uplift removed as requested

    # Development charge (if Commercial)
    breakdown["Development charge (monthly)"] = supervisor_cost * dev_charge if customer_type == "Commercial" else 0.0

    return breakdown, sum(breakdown.values())

# ------------------------------
# PRODUCTION CALCULATIONS (WEEKLY BASIS)
# ------------------------------
def calculate_production(items):
    results = []
    sup_weekly = sum([(s/52) * (chosen_pct / 100) for s in supervisor_salaries]) if not customer_covers_supervisors else 0.0
    prisoner_weekly = num_prisoners * prisoner_salary  # per week
    total_weekly_cost = prisoner_weekly + sup_weekly

    for item in items:
        name = item.get("name", "").strip() or "(Unnamed)"
        mins_per_unit = float(item.get("minutes", 0))
        prisoners_required = int(item.get("required", 1))
        prisoners_assigned = int(item.get("assigned", 0))

        if mins_per_unit <= 0 or prisoners_required <= 0 or prisoners_assigned <= 0 or workshop_hours <= 0:
            capacity_week = 0.0
            unit_cost = None
        else:
            available_mins_week = prisoners_assigned * workshop_hours * 60.0
            minutes_per_unit_total = mins_per_unit * prisoners_required
            capacity_week = available_mins_week / minutes_per_unit_total if minutes_per_unit_total > 0 else 0.0
            unit_cost = (total_weekly_cost / capacity_week) if capacity_week > 0 else None

        results.append({"Item": name, "Unit Cost": unit_cost, "MinUnitsWeek": capacity_week})
    return results

# ------------------------------
# DISPLAY HELPER
# ------------------------------
def display_table(breakdown, total_label="Total Monthly Cost"):
    html = "<table><thead><tr><th>Cost Item</th><th>Amount (£)</th></tr></thead><tbody>"
    for k, v in breakdown.items():
        html += f"<tr><td>{k}</td><td>£{v:,.2f}</td></tr>"
    total = sum(breakdown.values())
    html += f"<tr class='total-row'><td>{total_label}</td><td>£{total:,.2f}</td></tr></tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# ------------------------------
# UI: Host vs Production
# ------------------------------
errors = validate_inputs()

if workshop_mode == "Host":
    if st.button("Generate Costs", type="primary"):
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            st.subheader("Host Contract Costs")
            breakdown, _ = calculate_host_costs()
            display_table(breakdown)

elif workshop_mode == "Production":
    st.subheader("Production Contract Costs")

    num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")
    items = []
    for i in range(int(num_items)):
        with st.expander(f"Item {i+1} details", expanded=(i == 0)):
            name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
            prisoners_required = st.number_input(f"Prisoners required to make 1 item (Item {i+1})", min_value=1, value=1, step=1, key=f"req_{i}")
            minutes_per_item = st.number_input(f"How many minutes to make 1 item (Item {i+1})", min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}")
            prisoners_assigned = st.number_input(f"How many prisoners work solely on this item (Item {i+1})",
                                                 min_value=0, max_value=int(num_prisoners), value=0, step=1, key=f"assigned_{i}")
            items.append({"name": name, "required": int(prisoners_required), "minutes": float(minutes_per_item), "assigned": int(prisoners_assigned)})

    if errors:
        st.error("Fix errors before production calculations:\n- " + "\n- ".join(errors))
    else:
        results = calculate_production(items)
        for i, r in enumerate(results):
            st.markdown(f"### {r['Item']}")
            if r["Unit Cost"] is None:
                st.write("- Unit Cost (£): **N/A** (insufficient capacity or missing inputs)")
            else:
                st.write(f"- Unit Cost (£): £{r['Unit Cost']:.2f}")
            cap = r["MinUnitsWeek"]
            if cap <= 0:
                st.write("- Units/week (capacity): **0** — check minutes/prisoners assigned/workshop hours")
            else:
                st.write(f"- Units/week (capacity): {cap:.0f}")
            percent = st.slider(f"Output % for Item {i+1}", min_value=0, max_value=100, value=100, key=f"percent_{i}")
            adjusted_units = int(round(cap * (percent / 100.0))) if cap > 0 else 0
            st.write(f"- Adjusted units/week at {percent}% output: {adjusted_units}")

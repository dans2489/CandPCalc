# Cost and Price Calculator — Streamlit app
# v3.0 (2025-09-22)
# Changes this version:
# - Instructor (Supervisor) salary input switched to Title selection using Avg Total by Region.
# - Region auto-detected from Prison; title list filtered by region.
# - Keeps all prior behaviors: NFN blue title, Host heading "(costs are per month)",
#   Grand Total emphasis, reductions in red, maintenance default £8/m²/yr, Reset Selections at footer (red),
#   Instructor Time Allocation workflow (warning & reason when below recommended),
#   Development % on OVERHEADS with baseline/reduction/applied lines, true-HTML summary, no Excel.

from io import BytesIO
import pandas as pd
import streamlit as st

# -----------------------------
# Page config + minimal theming
# -----------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="💷",
    layout="wide",
    initial_sidebar_state="expanded",
)

NFN_BLUE = "#1D428A"
GOV_GREEN = "#00703C"
GOV_GREEN_DARK = "#005A30"
GOV_RED = "#D4351C"
GOV_RED_DARK = "#942514"

# Minimal CSS: NFN-blue title, green action buttons, red reset footer, table emphasis.
st.markdown(
    f"""
    <style>
      .app-title {{
        color: {NFN_BLUE} !important;
        font-size: 2.05rem;
        line-height: 1.1;
        margin: 0 0 14px 0;
        font-weight: 700;
      }}

      /* Default buttons = GOV.UK green */
      div.stButton > button, div.stDownloadButton > button {{
        background-color: {GOV_GREEN} !important;
        color: #fff !important;
        border: 1px solid {GOV_GREEN_DARK} !important;
        border-radius: 6px !important;
      }}
      div.stButton > button:hover, div.stDownloadButton > button:hover {{
        background-color: {GOV_GREEN_DARK} !important;
        border-color: {GOV_GREEN_DARK} !important;
      }}

      /* Reset footer button (red) */
      .reset-btn button {{
        background-color: {GOV_RED} !important;
        color: #fff !important;
        border: 1px solid {GOV_RED_DARK} !important;
        border-radius: 6px !important;
      }}
      .reset-btn button:hover {{
        background-color: {GOV_RED_DARK} !important;
        border-color: {GOV_RED_DARK} !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="app-title">Cost and Price Calculator</h1>', unsafe_allow_html=True)

# -----------------------------
# Constants and reference maps
# -----------------------------
ELECTRICITY_RATE_DEFAULT = 0.22  # £/kWh
GAS_RATE_DEFAULT = 0.05          # £/kWh
WATER_RATE_DEFAULT = 2.00        # £/m³

# EUI map (illustrative; kWh/m²/year)
EUI_MAP = {
    "Empty/basic (warehouse)": {"electric_kwh_m2_y": 35, "gas_kwh_m2_y": 30},
    "Light industrial":        {"electric_kwh_m2_y": 45, "gas_kwh_m2_y": 60},
    "Factory (typical)":       {"electric_kwh_m2_y": 30, "gas_kwh_m2_y": 70},
    "High energy process":     {"electric_kwh_m2_y": 60, "gas_kwh_m2_y": 100},
}

# Full Prison → Region mapping (unchanged)
PRISON_TO_REGION = {
    "Altcourse": "National", "Ashfield": "National", "Askham Grange": "National",
    "Aylesbury": "National", "Bedford": "National", "Belmarsh": "Inner London",
    "Berwyn": "National", "Birmingham": "National", "Brinsford": "National",
    "Bristol": "National", "Brixton": "Inner London", "Bronzefield": "Outer London",
    "Buckley Hall": "National", "Bullingdon": "National", "Bure": "National",
    "Cardiff": "National", "Channings Wood": "National", "Chelmsford": "National",
    "Coldingley": "Outer London", "Cookham Wood": "National", "Dartmoor": "National",
    "Deerbolt": "National", "Doncaster": "National", "Dovegate": "National",
    "Downview": "Outer London", "Drake Hall": "National", "Durham": "National",
    "East Sutton Park": "National", "Eastwood Park": "National", "Elmley": "National",
    "Erlestoke": "National", "Exeter": "National", "Featherstone": "National",
    "Feltham A": "Outer London", "Feltham B": "Outer London", "Five Wells": "National",
    "Ford": "National", "Forest Bank": "National", "Fosse Way": "National",
    "Foston Hall": "National", "Frankland": "National", "Full Sutton": "National",
    "Garth": "National", "Gartree": "National", "Grendon": "National",
    "Guys Marsh": "National", "Hatfield": "National", "Haverigg": "National",
    "Hewell": "National", "High Down": "Outer London", "Highpoint": "National",
    "Hindley": "National", "Hollesley Bay": "National", "Holme House": "National",
    "Hull": "National", "Humber": "National", "Huntercombe": "National",
    "Isis": "Inner London", "Isle of Wight": "National", "Kirkham": "National",
    "Kirklevington Grange": "National", "Lancaster Farms": "National",
    "Leeds": "National", "Leicester": "National", "Lewes": "National",
    "Leyhill": "National", "Lincoln": "National", "Lindholme": "National",
    "Littlehey": "National", "Liverpool": "National", "Long Lartin": "National",
    "Low Newton": "National", "Lowdham Grange": "National", "Maidstone": "National",
    "Manchester": "National", "Moorland": "National", "Morton Hall": "National",
    "The Mount": "National", "New Hall": "National", "North Sea Camp": "National",
    "Northumberland": "National", "Norwich": "National", "Nottingham": "National",
    "Oakwood": "National", "Onley": "National", "Parc": "National", "Parc (YOI)": "National",
    "Pentonville": "Inner London", "Peterborough Female": "National",
    "Peterborough Male": "National", "Portland": "National", "Prescoed": "National",
    "Preston": "National", "Ranby": "National", "Risley": "National",
    "Rochester": "National", "Rye Hill": "National", "Send": "National",
    "Spring Hill": "National", "Stafford": "National", "Standford Hill": "National",
    "Stocken": "National", "Stoke Heath": "National", "Styal": "National",
    "Sudbury": "National", "Swaleside": "National", "Swansea": "National",
    "Swinfen Hall": "National", "Thameside": "Inner London", "Thorn Cross": "National",
    "Usk": "National", "Verne": "National", "Wakefield": "National",
    "Wandsworth": "Inner London", "Warren Hill": "National", "Wayland": "National",
    "Wealstun": "National", "Werrington": "National", "Wetherby": "National",
    "Whatton": "National", "Whitemoor": "National", "Winchester": "National",
    "Woodhill": "Inner London", "Wormwood Scrubs": "Inner London", "Wymott": "National",
}

# NEW: Instructor (Supervisor) Avg Totals by Region & Title
SUPERVISOR_PAY = {
    "Inner London": [
        {"title": "Production Instructor: Band 3", "avg_total": 49603 - 400},  # Will replace with exact values below
        {"title": "Specialist Instructor: Band 4", "avg_total": 55632},
    ],
    "Outer London": [
        {"title": "Prison Officer Specialist - Instructor: Band 4", "avg_total": 69584},
        {"title": "Production Instructor: Band 3", "avg_total": 45856},
    ],
    "National": [
        {"title": "Prison Officer Specialist - Instructor: Band 4", "avg_total": 48969},
        {"title": "Production Instructor: Band 3", "avg_total": 42248},
    ],
}
# Correct the Inner London Band 3 to EXACT figure you provided (49,203).
SUPERVISOR_PAY["Inner London"][0]["avg_total"] = 49203

# -----------------------------------
# Sidebar: tariffs & fixed overheads
# -----------------------------------
with st.sidebar:
    st.header("Tariffs & Overheads")
    electricity_rate = st.number_input(
        "Electricity tariff (€/£ per kWh)",
        min_value=0.0, value=ELECTRICITY_RATE_DEFAULT, step=0.01, format="%.2f"
    )
    gas_rate = st.number_input(
        "Gas tariff (€/£ per kWh)",
        min_value=0.0, value=GAS_RATE_DEFAULT, step=0.01, format="%.2f"
    )
    water_rate = st.number_input(
        "Water tariff (€/£ per m³)",
        min_value=0.0, value=WATER_RATE_DEFAULT, step=0.10, format="%.2f"
    )

    st.markdown("---")
    st.markdown("**Maintenance / Depreciation**")
    maint_method = st.radio(
        "Method",
        ["£/m² per year (industry standard)", "Set a fixed monthly amount", "% of reinstatement value"],
        index=0,
    )
    maint_monthly = 0.0
    if maint_method.startswith("£/m² per year"):
        # Default changed to £8/m²/year per your instruction
        rate_per_m2_y = st.number_input("Maintenance rate (£/m²/year)", min_value=0.0, value=8.0, step=0.5)
        st.session_state["maint_rate_per_m2_y"] = rate_per_m2_y
    elif maint_method == "Set a fixed monthly amount":
        maint_monthly = st.number_input("Maintenance", min_value=0.0, value=0.0, step=25.0)
    else:  # % of reinstatement value
        reinstatement_value = st.number_input("Reinstatement value (£)", min_value=0.0, value=0.0, step=10_000.0)
        percent = st.number_input("Annual % of reinstatement value", min_value=0.0, value=2.0, step=0.25, format="%.2f")
        maint_monthly = (reinstatement_value * (percent / 100.0)) / 12.0

    st.markdown("---")
    admin_monthly = st.number_input("Administration", min_value=0.0, value=150.0, step=25.0)

# ----------------
# Base inputs (no top "Inputs" subtitle)
# ----------------
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

area_m2 = area_ft2 * 0.092903 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ft²** · **{area_m2:,.0f} m²**")

workshop_energy_types = list(EUI_MAP.keys())
workshop_type = st.selectbox("Workshop type?", ["Select"] + workshop_energy_types)

workshop_hours = st.number_input("How many hours per week is it open? (for production calc)", min_value=0.0, format="%.2f")

num_prisoners = st.number_input("How many prisoners employed?", min_value=0, step=1)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")

# Instructors (formerly supervisors)
num_supervisors = st.number_input("How many supervisors?", min_value=0, step=1)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s)?")

supervisor_salaries = []
recommended_pct = 0
if not customer_covers_supervisors:
    # Title selection uses Region from prison to filter available titles
    titles_for_region = SUPERVISOR_PAY.get(region, [])
    if region == "Select" or not titles_for_region:
        st.warning("Select a prison to derive the Region before assigning instructor titles.")
    else:
        for i in range(int(num_supervisors)):
            options = [t["title"] for t in titles_for_region]
            sel = st.selectbox(
                f"Instructor {i+1} title",
                options,
                key=f"inst_title_{i}"
            )
            pay = next(t["avg_total"] for t in titles_for_region if t["title"] == sel)
            st.caption(f"Avg Total for {region}: **£{pay:,.0f}** per year")
            supervisor_salaries.append(float(pay))

    # Contracts & recommended allocation (same logic)
    contracts = st.number_input("How many contracts do these instructors oversee?", min_value=1, value=1)
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if contracts and workshop_hours >= 0 else 0

    # Instructor Time Allocation
    st.subheader("Instructor Time Allocation")
    st.info(f"Recommended: {recommended_pct}%")
    chosen_pct = st.slider("Adjust instructor % allocation", 0, 100, int(recommended_pct), key="chosen_pct")

    effective_pct = int(chosen_pct)
    if chosen_pct < int(round(recommended_pct)):
        st.warning("You have selected less than recommended — please explain why here.")
        reason = st.text_area("Reason for using a lower allocation", key="alloc_reason")
        action = st.radio("Apply allocation", ["Keep recommended", "Set new"], index=0, horizontal=True, key="alloc_action")
        if action == "Set new":
            if not str(reason).strip():
                st.error("Please provide a brief explanation before setting a lower allocation.")
                effective_pct = int(round(recommended_pct))
            else:
                effective_pct = int(chosen_pct)
        else:
            effective_pct = int(round(recommended_pct))
else:
    chosen_pct = 0
    effective_pct = 0

# Employment support → development % of OVERHEADS
dev_rate = 0.0
support = "Select"
if customer_type == "Commercial":
    support = st.selectbox(
        "Customer employment support?",
        ["Select", "None", "Employment on release/RoTL", "Post release", "Both"]
    )
    if support == "None":
        dev_rate = 0.20
    elif support in ["Employment on release/RoTL", "Post release"]:
        dev_rate = 0.10
    elif support == "Both":
        dev_rate = 0.0

# Pricing (Commercial): VAT only
st.markdown("---")
st.subheader("Pricing (Commercial)")
colp1, colp2 = st.columns([1, 1])
with colp1:
    apply_vat = st.checkbox("Apply VAT?")
with colp2:
    vat_rate = st.number_input("VAT rate %", min_value=0.0, max_value=100.0, value=20.0, step=0.5, format="%.1f")

st.caption(
    "Unit pricing: Unit Cost includes labour + apportioned supervisors + apportioned overheads. "
    "No margin control: Unit Price ex VAT = Unit Cost. "
    "If VAT is ticked and customer is Commercial, Unit Price inc VAT = ex VAT × (1 + VAT%)."
)

# ----------------
# Validation
# ----------------
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
    if workshop_mode == "Production" and workshop_hours <= 0:
        errors.append("Hours per week must be > 0 (Production)")
    if num_prisoners <= 0:
        errors.append("Enter prisoners employed (>0)")
    if prisoner_salary <= 0:
        errors.append("Enter prisoner salary (>0)")
    if not customer_covers_supervisors:
        if num_supervisors <= 0:
            errors.append("Enter number of supervisors (>0) or tick 'Customer provides supervisor(s)'")
        # When region not selected, titles_for_region is empty—catch that
        if region == "Select":
            errors.append("Select a prison/region to populate instructor titles")
        # ensure we have the right count
        if len(supervisor_salaries) != int(num_supervisors):
            errors.append("Choose a title for each instructor")
        if any(s <= 0 for s in supervisor_salaries):
            errors.append("Instructor Avg Total must be > 0")
    return errors

# ----------------
# Cost helpers
# ----------------
def monthly_energy_costs():
    """EUI (kWh/m²/y) × area (m²) × tariff ÷ 12."""
    eui = EUI_MAP.get(workshop_type, None)
    if not eui or area_m2 <= 0:
        return 0.0, 0.0
    elec_kwh_y = eui["electric_kwh_m2_y"] * area_m2
    gas_kwh_y = eui["gas_kwh_m2_y"] * area_m2
    elec_cost_m = (elec_kwh_y / 12.0) * electricity_rate
    gas_cost_m = (gas_kwh_y / 12.0) * gas_rate
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
    """
    Electricity, gas, water, admin, maintenance → weekly total + monthly breakdown.
    (Maintenance labeled as estimated for consistency with overheads.)
    """
    if maint_method.startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", 8.0)
        maint_m = (rate * area_m2) / 12.0
    else:
        maint_m = maint_monthly

    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()

    overheads_m = elec_m + gas_m + water_m + admin_monthly + maint_m
    return overheads_m * 12.0 / 52.0, {
        "Electricity (estimated)": elec_m,
        "Gas (estimated)": gas_m,
        "Water (estimated)": water_m,
        "Administration": admin_monthly,
        "Depreciation/Maintenance (estimated)": maint_m,
    }

# ----------------
# Host costs (monthly)
# ----------------
def calculate_host_costs():
    breakdown = {}

    # Prisoner wages (per month)
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52 / 12)

    # Supervisors (Instructors) apportioned per effective_pct
    supervisor_cost = 0.0
    if not customer_covers_supervisors:
        supervisor_cost = sum((s / 12) * (effective_pct / 100) for s in supervisor_salaries)
    breakdown["Supervisors"] = supervisor_cost

    # Overheads (utilities estimated; admin not; maintenance estimated)
    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()
    breakdown["Electricity (estimated)"] = elec_m
    breakdown["Gas (estimated)"] = gas_m
    breakdown["Water (estimated)"] = water_m
    breakdown["Administration"] = admin_monthly

    # Maintenance (estimated)
    if maint_method.startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", 8.0)
        maint_val = (rate * area_m2) / 12.0
    else:
        maint_val = maint_monthly
    breakdown["Depreciation/Maintenance (estimated)"] = maint_val

    # Development charge on OVERHEADS (Commercial only)
    overheads_subtotal = elec_m + gas_m + water_m + admin_monthly + maint_val
    dev_baseline_rate = 0.20  # baseline for "None"
    dev_baseline_amount = overheads_subtotal * dev_baseline_rate

    if customer_type == "Commercial":
        dev_applied_rate = dev_rate
        dev_applied_amount = overheads_subtotal * dev_applied_rate
        reduction_amount = max(dev_baseline_amount - dev_applied_amount, 0.0)

        breakdown["Development charge baseline (20% of overheads)"] = dev_baseline_amount
        if reduction_amount > 0:
            breakdown["Support reduction (employment support)"] = -reduction_amount  # will render red
        breakdown["Development charge (applied)"] = dev_applied_amount
    else:
        breakdown["Development charge (applied)"] = 0.0

    # Totals & VAT
    subtotal = sum(breakdown.values())
    vat_amount = (subtotal * (vat_rate / 100.0)) if (customer_type == "Commercial" and apply_vat) else 0.0
    grand_total = subtotal + vat_amount

    totals = {
        "Subtotal": subtotal,
        "VAT %": vat_rate if (customer_type == "Commercial" and apply_vat) else 0.0,
        "VAT (£)": vat_amount if (customer_type == "Commercial" and apply_vat) else 0.0,
        "Grand Total (£/month)": grand_total,
    }
    return breakdown, totals

# --------------------------
# Production (weekly model)
# --------------------------
def calculate_production(items: list[dict], output_percents: list[int], apportion_rule: str):
    """
    Weekly model:
      weekly_cost = prisoner_weekly + apportioned_supervisors_weekly + apportioned_overheads_weekly
      unit_cost   = weekly_cost / (units/week at Output %)
    """
    overheads_weekly, _detail = weekly_overheads_total()
    sup_weekly_total = (
        sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
        if not customer_covers_supervisors else 0.0
    )

    # Apportionment denominator
    if apportion_rule.startswith("By labour minutes"):
        def cap_minutes(it):
            return int(it.get("assigned", 0)) * workshop_hours * 60.0
        denom = sum(cap_minutes(it) for it in items)
    else:
        denom = sum(int(it.get("assigned", 0)) for it in items)

    results = []
    for idx, item in enumerate(items):
        name = (item.get("name", "") or "(Unnamed)").strip()
        mins_per_unit = float(item.get("minutes", 0))
        prisoners_required = int(item.get("required", 1))
        prisoners_assigned = int(item.get("assigned", 0))
        output_pct = int(output_percents[idx]) if idx < len(output_percents) else 100

        # Capacity @100%
        if mins_per_unit <= 0 or prisoners_required <= 0 or prisoners_assigned <= 0 or workshop_hours <= 0:
            capacity_week = 0.0
        else:
            available_mins_week = prisoners_assigned * workshop_hours * 60.0
            minutes_per_unit_total = mins_per_unit * prisoners_required
            capacity_week = available_mins_week / minutes_per_unit_total if minutes_per_unit_total > 0 else 0.0

        # Share for apportionment
        if denom > 0:
            share_num = (prisoners_assigned * workshop_hours * 60.0) if apportion_rule.startswith("By labour minutes") else prisoners_assigned
            share = share_num / denom
        else:
            share = 0.0

        # Weekly cost components
        prisoner_weekly_item = prisoners_assigned * prisoner_salary
        sup_weekly_item = sup_weekly_total * share
        overheads_weekly_item = overheads_weekly * share
        weekly_cost_item = prisoner_weekly_item + sup_weekly_item + overheads_weekly_item

        # Apply Output %
        actual_units = capacity_week * (output_pct / 100.0)

        # Unit costs/prices
        unit_cost_base = (weekly_cost_item / actual_units) if actual_units > 0 else None
        unit_price_ex_vat = unit_cost_base
        unit_price_inc_vat = None
        if unit_price_ex_vat is not None and (customer_type == "Commercial" and apply_vat):
            unit_price_inc_vat = unit_price_ex_vat * (1 + (vat_rate / 100.0))
        elif unit_price_ex_vat is not None:
            unit_price_inc_vat = unit_price_ex_vat

        results.append({
            "Item": name,
            "Output %": output_pct,
            "Units/week": 0 if actual_units <= 0 else int(round(actual_units)),
            "Unit Cost (£)": unit_cost_base,
            "Unit Price ex VAT (£)": unit_price_ex_vat,
            "Unit Price inc VAT (£)": unit_price_inc_vat,
            # Diagnostics
            "Capacity @100% (units)": capacity_week,
            "Weekly Cost (£)": weekly_cost_item,
            "Weekly: Prisoners (£)": prisoner_weekly_item,
            "Weekly: Supervisors (£)": sup_weekly_item,
            "Weekly: Overheads (£)": overheads_weekly_item,
            "Share": share,
        })
    return results

# ----------------
# Display helpers (true HTML with emphasis + red reductions)
# ----------------
def _currency(v) -> str:
    try:
        return f"£{float(v):,.2f}"
    except Exception:
        return str(v)

def _host_table_html(breakdown: dict, totals: dict, total_label="Total Monthly Cost") -> str:
    rows_html = []
    for k, v in breakdown.items():
        amount = _currency(v)
        neg_cls = " class='neg'" if isinstance(v, (int, float)) and v < 0 else ""
        rows_html.append(f"<tr><td>{k}</td><td{neg_cls}>{amount}</td></tr>")

    total = sum(breakdown.values())
    rows_html.append(f"<tr><td>{total_label}</td><td>{_currency(total)}</td></tr>")

    if totals:
        rows_html.append(f"<tr><td>VAT ({totals.get('VAT %',0):.1f}%)</td><td>{_currency(totals.get('VAT (£)',0))}</td></tr>")
        rows_html.append(f"<tr class='grand'><td>Grand Total (£/month)</td><td>{_currency(totals.get('Grand Total (£/month)',0))}</td></tr>")

    style = """
      <style>
        table { width:100%; border-collapse:collapse; margin: 0.5rem 0 1rem 0; font-family: Arial, Helvetica, sans-serif; }
        th, td { text-align:left; padding:8px 10px; border-bottom:1px solid #e6e6e6; }
        th { background:#f8f8f8; }
        td.neg { color:#D4351C; font-weight:600; }           /* reductions in red */
        tr.grand td { font-weight:800; font-size:1.05rem; border-top:2px solid #222; } /* standout Grand Total */
      </style>
    """
    return f"{style}<table><tr><th>Cost Item</th><th>Amount (£)</th></tr>{''.join(rows_html)}</table>"

def display_table(breakdown: dict, totals: dict, total_label="Total Monthly Cost"):
    html = _host_table_html(breakdown, totals, total_label)
    rows = 1 + len(breakdown) + (2 if totals else 0)
    height = 100 + int(rows * 40)
    st.components.v1.html(html, height=height, scrolling=False)

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

# ----------------
# Export helpers (CSV / HTML only)
# ----------------
def export_csv_bytes(df: pd.DataFrame) -> BytesIO:
    b = BytesIO()
    df.to_csv(b, index=False)
    b.seek(0)
    return b

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="Quote") -> BytesIO:
    def df_to_html(df: pd.DataFrame) -> str:
        return df.to_html(index=False, border=0)

    html = f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <title>{title}</title>
      <style>
        body {{ font-family: Arial, Helvetica, sans-serif; color:#111; }}
        h1, h2, h3 {{ margin: 0.2rem 0 0.6rem 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 0.5rem 0 1rem 0; }}
        th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e6e6e6; }}
        th {{ background: #f8f8f8; }}
      </style>
    </head>
    <body>
      <h1>Cost and Price Calculator — Quote</h1>
      <p><strong>Customer:</strong> {customer_name or ''} &nbsp;|&nbsp; <strong>Prison:</strong> {prison_choice or ''} &nbsp;|&nbsp; <strong>Region:</strong> {region or ''}</p>
    """
    if host_df is not None:
        html += f"<h2>Host Costs</h2>{df_to_html(host_df)}"
    if prod_df is not None:
        html += f"<h2>Production Items</h2>{df_to_html(prod_df)}"
    html += "</body></html>"
    b = BytesIO(html.encode("utf-8"))
    b.seek(0)
    return b

# ----------------
# Main UI branches
# ----------------
errors = validate_inputs()

# HOST — Production settings hidden
if workshop_mode == "Host":
    if st.button("Generate Costs", type="primary"):
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            heading_name = customer_name if str(customer_name).strip() else "Customer"
            st.subheader(f"Host Contract for {heading_name} (costs are per month)")
            breakdown, totals = calculate_host_costs()
            display_table(breakdown, totals)

            host_df = to_dataframe_host(breakdown, totals)
            st.download_button(
                "Download CSV (Host)",
                data=export_csv_bytes(host_df),
                file_name="host_quote.csv",
                mime="text/csv",
            )
            st.download_button(
                "Download PDF-ready HTML (Host)",
                data=export_html(host_df, None, title="Host Quote"),
                file_name="host_quote.html",
                mime="text/html",
            )

# PRODUCTION — only appears when selected
elif workshop_mode == "Production":
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
            Minutes available per item at full utilisation = **assigned prisoners × weekly hours × 60**.  
            More minutes ⇒ bigger share of weekly overheads and supervisor time.  
            **By assigned prisoners** just counts heads (simpler, less precise).
            """
        )

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
                "assigned": int(prisoners_assigned),
            })

    if errors:
        st.error("Fix errors before production calculations:\n- " + "\n- ".join(errors))
    else:
        output_percents = []
        for i, it in enumerate(items):
            cap_preview = 0.0
            if it["minutes"] > 0 and it["required"] > 0 and it["assigned"] > 0 and workshop_hours > 0:
                cap_preview = (it["assigned"] * workshop_hours * 60.0) / (it["minutes"] * it["required"])
            st.markdown(f"Item {i+1} capacity @ 100%: **{cap_preview:.0f} units/week**")
            output_percents.append(st.slider(f"Output % for Item {i+1}", min_value=0, max_value=100, value=100, key=f"percent_{i}"))

        results = calculate_production(items, output_percents, apportion_rule)

        for r in results:
            st.markdown(f"### {r['Item'] or 'Item'}")
            st.write(f"- Output %: {r['Output %']}%")
            st.write(f"- Units/week: {r['Units/week']}")
            if r["Unit Cost (£)"] is None:
                st.write("- Unit Cost (£): **N/A** — check minutes/prisoners assigned/workshop hours or increase Output %")
                st.write("- Unit Price ex VAT (£): **N/A**")
                st.write("- Unit Price inc VAT (£): **N/A**")
            else:
                st.write(f"- Unit Cost (£): **£{r['Unit Cost (£)']:.2f}**")
                if r["Unit Price ex VAT (£)"] is not None:
                    st.write(f"- Unit Price ex VAT (£): **£{r['Unit Price ex VAT (£)']:.2f}**")
                if r["Unit Price inc VAT (£)"] is not None:
                    st.write(f"- Unit Price inc VAT (£): **£{r['Unit Price inc VAT (£)']:.2f}**")

        prod_df = to_dataframe_production(results)
        st.download_button(
            "Download CSV (Production)",
            data=export_csv_bytes(prod_df),
            file_name="production_quote.csv",
            mime="text/csv",
        )
        st.download_button(
            "Download PDF-ready HTML (Production)",
            data=export_html(None, prod_df, title="Production Quote"),
            file_name="production_quote.html",
            mime="text/html",
        )

# ----------------
# Footer: Reset Selections (red) — at the very end
# ----------------
st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
if st.button("Reset Selections", key="reset_app_footer"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
st.markdown('</div>', unsafe_allow_html=True)

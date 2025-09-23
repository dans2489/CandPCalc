# Cost and Price Calculator — Streamlit app
# v3.3 (2025-09-23)
# Production updates:
# - Per-item ad-hoc targets with back-solve (Assigned prisoners / Weekly hours / Output % needed).
# - "Apply" actions update widget state safely (no auto-changes without user click).
# - Advanced: pooled targets across items (allocates assigned prisoners per item if feasible).
# - Labour minutes apportionment only; minutes budget shown and enforced.
# - Dynamic labels use item name; Output % slider has a help tooltip.
# - Hours label clarifies effect on capacity and instructor allocation.
#
# Styling/formatting retained from earlier versions:
# - NFN-blue title, GOV colour accents, grey Grand Total row (not bold), red negatives,
#   GBP with 2dp, true-HTML export, red "Reset Selections" footer.

from io import BytesIO
import math
import pandas as pd
import streamlit as st

# ------------------------------
# Page config + minimal theming
# ------------------------------
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

# Minimal CSS, preserving your established look
st.markdown(
    f"""
    <style>
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0 0 0.5rem 0;
        font-size: 0.95rem;
    }}
    th, td {{
        border-bottom: 1px solid #ddd;
        padding: 0.5rem 0.6rem;
        text-align: left;
        vertical-align: top;
    }}
    th {{
        background: #f3f2f1;
        font-weight: 600;
        color: #0b0c0c;
    }}
    tr.grand td {{
        background: #f3f2f1 !important;  /* grey like header */
        font-weight: 400 !important;      /* not bold */
    }}
    td.neg {{ color: {GOV_RED}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('\n\n## Cost and Price Calculator\n\n', unsafe_allow_html=True)

# ------------------------------
# Constants and reference maps
# ------------------------------
ELECTRICITY_RATE_DEFAULT = 0.22  # £/kWh
GAS_RATE_DEFAULT = 0.05          # £/kWh
WATER_RATE_DEFAULT = 2.00        # £/m³

# EUI map (illustrative; kWh/m²/year)
EUI_MAP = {
    "Empty/basic (warehouse)": {"electric_kwh_m2_y": 35, "gas_kwh_m2_y": 30},
    "Light industrial": {"electric_kwh_m2_y": 45, "gas_kwh_m2_y": 60},
    "Factory (typical)": {"electric_kwh_m2_y": 30, "gas_kwh_m2_y": 70},
    "High energy process": {"electric_kwh_m2_y": 60, "gas_kwh_m2_y": 100},
}

# Full Prison → Region mapping (unchanged)
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
    "Norwich": "National", "Nottingham": "National", "Oakwood": "National", "Onley": "National",
    "Parc": "National", "Parc (YOI)": "National", "Pentonville": "Inner London", "Peterborough Female": "National",
    "Peterborough Male": "National", "Portland": "National", "Prescoed": "National", "Preston": "National",
    "Ranby": "National", "Risley": "National", "Rochester": "National", "Rye Hill": "National",
    "Send": "National", "Spring Hill": "National", "Stafford": "National", "Standford Hill": "National",
    "Stocken": "National", "Stoke Heath": "National", "Styal": "National", "Sudbury": "National",
    "Swaleside": "National", "Swansea": "National", "Swinfen Hall": "National", "Thameside": "Inner London",
    "Thorn Cross": "National", "Usk": "National", "Verne": "National", "Wakefield": "National",
    "Wandsworth": "Inner London", "Warren Hill": "National", "Wayland": "National", "Wealstun": "National",
    "Werrington": "National", "Wetherby": "National", "Whatton": "National", "Whitemoor": "National",
    "Winchester": "National", "Woodhill": "Inner London", "Wormwood Scrubs": "Inner London", "Wymott": "National",
}

# Instructor (Supervisor) Avg Totals by Region & Title
SUPERVISOR_PAY = {
    "Inner London": [
        {"title": "Production Instructor: Band 3", "avg_total": 49203},
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

# --------------------------------
# Sidebar — tariffs & fixed costs
# --------------------------------
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
    st.markdown("**Maintenance / Depreciation**")

    maint_method = st.radio(
        "Method",
        ["£/m² per year (industry standard)", "Set a fixed monthly amount", "% of reinstatement value"],
        index=0,
    )

    maint_monthly = 0.0
    if maint_method.startswith("£/m² per year"):
        # Default £8/m²/year
        rate_per_m2_y = st.number_input("Maintenance rate (£/m²/year)", min_value=0.0, value=8.0, step=0.5)
        st.session_state["maint_rate_per_m2_y"] = rate_per_m2_y
    elif maint_method == "Set a fixed monthly amount":
        maint_monthly = st.number_input("Maintenance", min_value=0.0, value=0.0, step=25.0)
    else:
        # % of reinstatement value
        reinstatement_value = st.number_input("Reinstatement value (£)", min_value=0.0, value=0.0, step=10_000.0)
        percent = st.number_input("Annual % of reinstatement value", min_value=0.0, value=2.0, step=0.25, format="%.2f")
        maint_monthly = (reinstatement_value * (percent / 100.0)) / 12.0

    st.markdown("---")
    admin_monthly = st.number_input("Administration", min_value=0.0, value=150.0, step=25.0)

# --------------------------
# Main inputs
# --------------------------
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

# Hours label clarifies dual impact
workshop_hours = st.number_input(
    "How many hours per week is the workshop open?",
    min_value=0.0, format="%.2f",
    help="This value affects production capacity and the recommended % share of instructor time for this contract.",
)

num_prisoners = st.number_input("How many prisoners employed?", min_value=0, step=1)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")

# Instructors (formerly supervisors)
num_supervisors = st.number_input("How many supervisors?", min_value=0, step=1)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s)?")
supervisor_salaries = []
recommended_pct = 0

if not customer_covers_supervisors:
    titles_for_region = SUPERVISOR_PAY.get(region, [])
    if region == "Select" or not titles_for_region:
        st.warning("Select a prison to derive the Region before assigning instructor titles.")
    else:
        for i in range(int(num_supervisors)):
            options = [t["title"] for t in titles_for_region]
            sel = st.selectbox(f"Instructor {i+1} title", options, key=f"inst_title_{i}")
            pay = next(t["avg_total"] for t in titles_for_region if t["title"] == sel)
            st.caption(f"Avg Total for {region}: **£{pay:,.0f}** per year")
            supervisor_salaries.append(float(pay))

# Contracts & recommended allocation
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
    effective_pct = int(round(recommended_pct))

# Employment support → development % of OVERHEADS (Commercial only)
dev_rate = 0.0
support = "Select"
if customer_type == "Commercial":
    support = st.selectbox(
        "Customer employment support?",
        ["Select", "None", "Employment on release/RoTL", "Post release", "Both"],
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

# --------------------------
# Validation
# --------------------------
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
    if workshop_mode == "Production" and workshop_hours <= 0: errors.append("Hours per week must be > 0 (Production)")
    if num_prisoners <= 0: errors.append("Enter prisoners employed (>0)")
    if prisoner_salary <= 0: errors.append("Enter prisoner salary (>0)")
    if not customer_covers_supervisors:
        if num_supervisors <= 0: errors.append("Enter number of supervisors (>0) or tick 'Customer provides supervisor(s)'")
        if region == "Select": errors.append("Select a prison/region to populate instructor titles")
        if len(supervisor_salaries) != int(num_supervisors): errors.append("Choose a title for each instructor")
        if any(s <= 0 for s in supervisor_salaries): errors.append("Instructor Avg Total must be > 0")
    return errors

# --------------------------
# Cost helpers
# --------------------------
def monthly_energy_costs():
    """EUI (kWh/m²/y) × area (m²) × tariff ÷ 12."""
    eui = EUI_MAP.get(workshop_type, None)
    if not eui or area_m2 <= 0: return 0.0, 0.0
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
    """Electricity, gas, water, admin, maintenance → weekly total + monthly breakdown."""
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

# --------------------------
# Host costs (monthly)
# --------------------------
def calculate_host_costs():
    breakdown = {}
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52 / 12)
    supervisor_cost = 0.0
    if not customer_covers_supervisors:
        supervisor_cost = sum((s / 12) * (effective_pct / 100) for s in supervisor_salaries)
    breakdown["Supervisors"] = supervisor_cost
    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()
    breakdown["Electricity (estimated)"] = elec_m
    breakdown["Gas (estimated)"] = gas_m
    breakdown["Water (estimated)"] = water_m
    breakdown["Administration"] = admin_monthly
    if maint_method.startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", 8.0)
        maint_val = (rate * area_m2) / 12.0
    else:
        maint_val = maint_monthly
    breakdown["Depreciation/Maintenance (estimated)"] = maint_val

    overheads_subtotal = elec_m + gas_m + water_m + admin_monthly + maint_val
    dev_baseline_rate = 0.20
    dev_baseline_amount = overheads_subtotal * dev_baseline_rate
    if customer_type == "Commercial":
        dev_applied_rate = dev_rate
        dev_applied_amount = overheads_subtotal * dev_applied_rate
        reduction_amount = max(dev_baseline_amount - dev_applied_amount, 0.0)
        breakdown["Development charge baseline (20% of overheads)"] = dev_baseline_amount
        if reduction_amount > 0:
            breakdown["Support reduction (employment support)"] = -reduction_amount
        breakdown["Development charge (applied)"] = dev_applied_amount
    else:
        breakdown["Development charge (applied)"] = 0.0

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
# Production helpers (minutes & back-solve)
# --------------------------
def item_capacity_100(prisoners_assigned: int, minutes_per_item: float, prisoners_required: int, hours: float) -> float:
    """Units/week at 100% = (assigned × hours × 60) / (minutes_per_item × prisoners_required)."""
    if prisoners_assigned <= 0 or minutes_per_item <= 0 or prisoners_required <= 0 or hours <= 0:
        return 0.0
    return (prisoners_assigned * hours * 60.0) / (minutes_per_item * prisoners_required)

def minutes_required_for_units(units: float, minutes_per_item: float, prisoners_required: int) -> float:
    """Labour minutes needed to produce 'units' for this item."""
    if units <= 0 or minutes_per_item <= 0 or prisoners_required <= 0:
        return 0.0
    return units * minutes_per_item * prisoners_required

def assigned_needed_for_units(units: float, minutes_per_item: float, prisoners_required: int, hours: float) -> float:
    """Assigned prisoners needed to meet target units (may be fractional)."""
    mins_needed = minutes_required_for_units(units, minutes_per_item, prisoners_required)
    if hours <= 0: return float("inf")
    return mins_needed / (hours * 60.0)

def output_pct_needed(units_target: float, cap_100: float) -> int:
    if cap_100 <= 0: return 0
    return int(round(min(100.0, (units_target / cap_100) * 100.0)))

def labour_minutes_budget(num_pris: int, hours: float) -> float:
    return max(0.0, num_pris * hours * 60.0)

# --------------------------
# Production (weekly model) — Labour minutes ONLY
# --------------------------
def calculate_production(items, output_percents):
    overheads_weekly, _detail = weekly_overheads_total()
    sup_weekly_total = (
        sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
        if not customer_covers_supervisors else 0.0
    )
    # Denominator for apportionment (labour minutes)
    denom = sum(int(it.get("assigned", 0)) * workshop_hours * 60.0 for it in items)

    results = []
    for idx, item in enumerate(items):
        name = (item.get("name", "") or "").strip() or f"Item {idx+1}"
        mins_per_unit = float(item.get("minutes", 0))
        prisoners_required = int(item.get("required", 1))
        prisoners_assigned = int(item.get("assigned", 0))
        output_pct = int(output_percents[idx]) if idx < len(output_percents) else 100

        cap_100 = item_capacity_100(prisoners_assigned, mins_per_unit, prisoners_required, workshop_hours)
        share = ((prisoners_assigned * workshop_hours * 60.0) / denom) if denom > 0 else 0.0

        prisoner_weekly_item = prisoners_assigned * prisoner_salary
        sup_weekly_item = sup_weekly_total * share
        overheads_weekly_item = overheads_weekly * share
        weekly_cost_item = prisoner_weekly_item + sup_weekly_item + overheads_weekly_item

        actual_units = cap_100 * (output_pct / 100.0)
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
            "Capacity @100% (units)": cap_100,
            "Weekly Cost (£)": weekly_cost_item,
            "Weekly: Prisoners (£)": prisoner_weekly_item,
            "Weekly: Supervisors (£)": sup_weekly_item,
            "Weekly: Overheads (£)": overheads_weekly_item,
            "Share": share,
        })
    return results

# ------------------
# Display & export helpers
# ------------------
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
    return "<table><tr><th>Cost Item</th><th>Amount (£)</th></tr>" + "".join(rows_html) + "</table>"

def display_table(breakdown: dict, totals: dict, total_label="Total Monthly Cost"):
    html = _host_table_html(breakdown, totals, total_label)
    rows = 1 + len(breakdown) + (2 if totals else 0)
    height = 100 + int(rows * 40)
    st.components.v1.html(html, height=height, scrolling=False)

def to_dataframe_host(breakdown: dict, totals: dict) -> pd.DataFrame:
    rows = list(breakdown.items())
    rows += [("Subtotal", sum(breakdown.values())), (f"VAT ({totals.get('VAT %',0):.1f}%)", totals.get("VAT (£)",0)), ("Grand Total (£/month)", totals.get("Grand Total (£/month)",0))]
    return pd.DataFrame(rows, columns=["Item", "Amount (£)"])

def to_dataframe_production(results: list[dict]) -> pd.DataFrame:
    cols = ["Item", "Output %", "Units/week", "Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]
    df = pd.DataFrame([{c: r.get(c) for c in cols} for r in results])
    for c in ["Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: None if x is None else round(float(x), 2))
    return df

def export_csv_bytes(df: pd.DataFrame) -> BytesIO:
    b = BytesIO()
    df.to_csv(b, index=False)
    b.seek(0)
    return b

def _html_escape(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def _render_host_df_to_html(host_df: pd.DataFrame) -> str:
    rows_html = []
    for _, row in host_df.iterrows():
        item = str(row["Item"]); val = row["Amount (£)"]
        neg_cls = ""
        try:
            neg_cls = " class='neg'" if float(val) < 0 else ""
        except Exception:
            pass
        grand_cls = " class='grand'" if "Grand Total" in item else ""
        if grand_cls:
            rows_html.append(f"<tr{grand_cls}><td>{_html_escape(item)}</td><td>{_currency(val)}</td></tr>")
        else:
            rows_html.append(f"<tr><td>{_html_escape(item)}</td><td{neg_cls}>{_currency(val)}</td></tr>")
    header = "<tr><th>Item</th><th>Amount (£)</th></tr>"
    return f"<table>{header}{''.join(rows_html)}</table>"

def _render_generic_df_to_html(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    body_rows = []
    for _, row in df.iterrows():
        tds = []
        for col in cols:
            val = row[col]
            if isinstance(val, (int, float)) and pd.notna(val):
                tds.append(f"<td>{_currency(val) if '£' in col else f'{float(val):,.2f}'}</td>")
            else:
                tds.append(f"<td>{_html_escape(val)}</td>")
        body_rows.append(f"<tr>{''.join(tds)}</tr>")
    thead = "<tr>" + "".join([f"<th>{_html_escape(c)}</th>" for c in cols]) + "</tr>"
    return f"<table>{thead}{''.join(body_rows)}</table>"

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="Quote") -> BytesIO:
    html_parts = [f"# {_html_escape(title)}", "\n\n## Cost and Price Calculator — Quote\n"]
    html_parts.append(
        f"<p><strong>Customer:</strong> {_html_escape(customer_name or '')} &nbsp; "
        f"<strong>Prison:</strong> {_html_escape(prison_choice or '')} &nbsp; "
        f"<strong>Region:</strong> {_html_escape(region or '')}</p>\n"
    )
    if host_df is not None:
        html_parts.append("\n\n### Host Costs\n")
        html_parts.append(_render_host_df_to_html(host_df))
    if prod_df is not None:
        html_parts.append("\n\n### Production Items\n")
        html_parts.append(_render_generic_df_to_html(prod_df))
    b = BytesIO("".join(html_parts).encode("utf-8")); b.seek(0); return b

# --------------------------
# Main UI branches
# --------------------------
errors = validate_inputs()

# HOST
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
            st.download_button("Download CSV (Host)", data=export_csv_bytes(host_df), file_name="host_quote.csv", mime="text/csv")
            st.download_button("Download PDF-ready HTML (Host)", data=export_html(host_df, None, title="Host Quote"), file_name="host_quote.html", mime="text/html")

# PRODUCTION — Labour minutes only
elif workshop_mode == "Production":
    st.subheader("Production Settings")
    st.caption("Apportionment method: Labour minutes — overheads & instructor time are shared by "
               "assigned labour minutes (assigned prisoners × weekly hours × 60).")

    # Weekly minutes budget
    budget_minutes = labour_minutes_budget(num_prisoners, workshop_hours)
    st.markdown(f"As per your selected resources you have **{budget_minutes:,.0f} Labour minutes** available this week.")

    # Advanced pooled targets toggle
    pooled_toggle = st.checkbox("Advanced: pooled targets across items", value=False)

    # Items
    num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")
    items = []
    OUTPUT_PCT_HELP = ("How much of the item’s theoretical weekly capacity you plan to use this week. "
                       "100% assumes assigned prisoners and weekly hours are fully available; reduce for ramp-up, changeovers, downtime, etc.")

    # Collect per-item inputs
    for i in range(int(num_items)):
        with st.expander(f"Item {i+1} details", expanded=(i == 0)):
            name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
            display_name = (name.strip() or f"Item {i+1}")
            prisoners_required = st.number_input(f"Prisoners required to make 1 item ({display_name})",
                                                 min_value=1, value=1, step=1, key=f"req_{i}")
            minutes_per_item = st.number_input(f"How many minutes to make 1 item ({display_name})",
                                               min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}")
            # Assigned prisoners widget uses session_state to allow "Apply" to update it
            assigned_key = f"assigned_{i}"
            current_assigned_default = 0
            if assigned_key not in st.session_state:
                st.session_state[assigned_key] = current_assigned_default
            prisoners_assigned = st.number_input(f"How many prisoners work solely on this item ({display_name})",
                                                 min_value=0, max_value=int(num_prisoners), step=1, key=assigned_key)

            # Optional target and back-solve actions
            target_key = f"target_{i}"
            target_units = st.number_input(f"Target units this week (optional) — {display_name}",
                                           min_value=0, step=1, value=0, key=target_key)

            cap_preview = item_capacity_100(prisoners_assigned, minutes_per_item, prisoners_required, workshop_hours)
            st.markdown(f"{display_name} capacity @ 100%: **{cap_preview:.0f} units/week**")

            if target_units > 0:
                req_pct = output_pct_needed(target_units, cap_preview)
                st.caption(f"Diagnostic: requires ~**{req_pct}% Output** with current assignment/hours.")

                cols_apply = st.columns(2)
                with cols_apply[0]:
                    if st.button(f"Apply: set ASSIGNED for {display_name}", key=f"apply_assigned_{i}"):
                        needed = assigned_needed_for_units(target_units, minutes_per_item, prisoners_required, workshop_hours)
                        needed_int = int(math.ceil(needed)) if math.isfinite(needed) else 0
                        st.session_state[assigned_key] = needed_int
                        st.rerun()
                with cols_apply[1]:
                    if st.button(f"Apply: set HOURS to meet target ({display_name})", key=f"apply_hours_{i}"):
                        # Solve hours = (target_units * minutes_per_item * prisoners_required) / (assigned * 60)
                        if prisoners_assigned > 0:
                            hours_needed = (target_units * minutes_per_item * prisoners_required) / (prisoners_assigned * 60.0)
                            st.session_state["workshop_hours"] = round(hours_needed, 2)
                            st.rerun()
                        else:
                            st.warning("Assign at least 1 prisoner before solving for hours.")

            items.append({
                "name": name,
                "required": int(prisoners_required),
                "minutes": float(minutes_per_item),
                "assigned": int(st.session_state[assigned_key]),
            })

    if errors:
        st.error("Fix errors before production calculations:\n- " + "\n- ".join(errors))
    else:
        # ---------- Advanced pooled solver (optional) ----------
        if pooled_toggle:
            st.markdown("#### Pooled targets solver")
            # Gather per-item targets and compute total required minutes
            per_item_targets = []
            total_required_minutes = 0.0
            for i, it in enumerate(items):
                t = st.session_state.get(f"target_{i}", 0)
                per_item_targets.append(int(t))
                total_required_minutes += minutes_required_for_units(t, it["minutes"], it["required"])

            if sum(per_item_targets) == 0:
                st.info("Enter one or more per-item targets above to use the pooled solver.")
            else:
                # Feasibility check against labour minutes budget and headcount
                if total_required_minutes <= budget_minutes and workshop_hours > 0:
                    # Compute fractional assigned per item, then round up using largest remainders while respecting total prisoners
                    fractional = []
                    for i, it in enumerate(items):
                        need = assigned_needed_for_units(per_item_targets[i], it["minutes"], it["required"], workshop_hours)
                        fractional.append(max(0.0, need))
                    # Initial integer assignment = floor
                    assigned_ints = [int(math.floor(x)) for x in fractional]
                    remainder = [x - int(math.floor(x)) for x in fractional]

                    # Prisoners available limit
                    total_int = sum(assigned_ints)
                    prisoners_left = max(0, int(num_prisoners) - total_int)

                    # Distribute remaining using largest remainders
                    order = sorted(range(len(remainder)), key=lambda k: remainder[k], reverse=True)
                    for k in order:
                        if prisoners_left <= 0:
                            break
                        # Only round up if there is actually a need (>0 remainder or fractional>0)
                        if fractional[k] > assigned_ints[k]:
                            assigned_ints[k] += 1
                            prisoners_left -= 1

                    # Final check: minutes used must cover required minutes; it will, because rounding up never reduces minutes
                    # Apply button to update all "assigned_i"
                    if st.button("Apply pooled assignment (sets per-item Assigned prisoners)"):
                        for i in range(len(items)):
                            st.session_state[f"assigned_{i}"] = int(assigned_ints[i])
                        st.rerun()

                    # Show summary
                    st.success(
                        f"Pooled solution is feasible under the minutes budget. "
                        f"Suggested assigned prisoners: {', '.join([str(x) for x in assigned_ints])} "
                        f"(total {sum(assigned_ints)} ≤ available {num_prisoners})."
                    )
                    st.caption(f"Total required minutes {int(total_required_minutes):,} ≤ budget {int(budget_minutes):,}.")
                else:
                    # Infeasible: report shortfall & scaling factor suggestion
                    if workshop_hours <= 0:
                        st.error("Set weekly hours > 0 to use the pooled solver.")
                    else:
                        shortfall = max(0.0, total_required_minutes - budget_minutes)
                        scale = (budget_minutes / total_required_minutes) if total_required_minutes > 0 else 0.0
                        st.error(
                            f"Pooled targets are not feasible with current resources.\n\n"
                            f"- Required minutes: **{int(total_required_minutes):,}**\n"
                            f"- Available minutes: **{int(budget_minutes):,}**\n"
                            f"- Shortfall: **{int(shortfall):,} minutes**\n"
                            f"- Max achievable ≈ **{scale:.1%}** of the requested targets (if scaled evenly)."
                        )

        # ---------- Minutes cap enforcement ----------
        used_minutes = sum(int(it["assigned"]) * workshop_hours * 60.0 for it in items)
        st.markdown(f"**Used Labour minutes:** {used_minutes:,.0f} / {budget_minutes:,.0f}")
        if used_minutes > budget_minutes:
            st.error(
                "Assigned prisoners across items exceed the available weekly Labour minutes. "
                "Reduce assigned counts, add prisoners, or increase weekly hours."
            )
        else:
            # Output % sliders (with help). Default respects any pre-seeded session state (e.g., if user set via diagnostic).
            output_percents = []
            for i, it in enumerate(items):
                disp = (it["name"].strip() or f"Item {i+1}") if isinstance(it["name"], str) else f"Item {i+1}"
                key = f"percent_{i}"
                default_val = st.session_state.get(key, 100)
                val = st.slider(f"Output % for {disp}", min_value=0, max_value=100, value=default_val, key=key, help=OUTPUT_PCT_HELP)
                output_percents.append(val)

            # Calculate and display
            results = calculate_production(items, output_percents)
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

            # Exports
            prod_df = to_dataframe_production(results)
            st.download_button("Download CSV (Production)", data=export_csv_bytes(prod_df), file_name="production_quote.csv", mime="text/csv")
            st.download_button("Download PDF-ready HTML (Production)", data=export_html(None, prod_df, title="Production Quote"), file_name="production_quote.html", mime="text/html")

# --------------------------
# Footer: Reset Selections
# --------------------------
st.markdown('\n', unsafe_allow_html=True)
if st.button("Reset Selections", key="reset_app_footer"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
st.markdown('\n', unsafe_allow_html=True)

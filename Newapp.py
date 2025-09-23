# Cost and Price Calculator â€” Streamlit app
# v3.4 (2025-09-23)
# ---------------------------------------------------------
# What's in this build (per Dan):
# - Production starts by asking: Contractual work (as normal) OR Ad-hoc costs with a deadline.
# - Contractual work = previous Production flow (Labour minutes only, minutes budget+cap, per-item Output%).
# - Ad-hoc = single-item, deadline-driven calculator:
#     * Inputs: item name, minutes per item, prisoners required per item, units needed, deadline date.
#     * Uses existing resources (hours/week, prisoners employed, wage, supervisors, allocation).
#     * Computes weeks to deadline, checks total minutes, tells you additional prisoners needed (if any),
#       and provides a total job price (ex VAT + inc VAT if Commercial+VAT).
# - All styling/formatting retained: NFN-blue title, grey Grand Total row (not bold), red negatives,
#   GBP Â£ with 2dp, true-HTML exports, red Reset button.

from io import BytesIO
import math
from datetime import date
import pandas as pd
import streamlit as st

# ------------------------------
# Page config + minimal theming
# ------------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="ðŸ’·",
    layout="wide",
    initial_sidebar_state="expanded",
)

NFN_BLUE = "#1D428A"
GOV_GREEN = "#00703C"
GOV_GREEN_DARK = "#005A30"
GOV_RED = "#D4351C"
GOV_RED_DARK = "#942514"

# Minimal CSS preserved (government style look)
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
ELECTRICITY_RATE_DEFAULT = 0.22  # Â£/kWh
GAS_RATE_DEFAULT = 0.05          # Â£/kWh
WATER_RATE_DEFAULT = 2.00        # Â£/mÂ³

# EUI map (illustrative; kWh/mÂ²/year)
EUI_MAP = {
    "Empty/basic (warehouse)": {"electric_kwh_m2_y": 35, "gas_kwh_m2_y": 30},
    "Light industrial": {"electric_kwh_m2_y": 45, "gas_kwh_m2_y": 60},
    "Factory (typical)": {"electric_kwh_m2_y": 30, "gas_kwh_m2_y": 70},
    "High energy process": {"electric_kwh_m2_y": 60, "gas_kwh_m2_y": 100},
}

# Full Prison â†’ Region mapping (unchanged)
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
# Sidebar â€” tariffs & fixed costs
# --------------------------------
with st.sidebar:
    st.header("Tariffs & Overheads")

    electricity_rate = st.number_input(
        "Electricity tariff (â‚¬/Â£ per kWh)",
        min_value=0.0, value=ELECTRICITY_RATE_DEFAULT, step=0.01, format="%.2f",
    )
    gas_rate = st.number_input(
        "Gas tariff (â‚¬/Â£ per kWh)",
        min_value=0.0, value=GAS_RATE_DEFAULT, step=0.01, format="%.2f",
    )
    water_rate = st.number_input(
        "Water tariff (â‚¬/Â£ per mÂ³)",
        min_value=0.0, value=WATER_RATE_DEFAULT, step=0.10, format="%.2f",
    )

    st.markdown("---")
    st.markdown("**Maintenance / Depreciation**")

    maint_method = st.radio(
        "Method",
        ["Â£/mÂ² per year (industry standard)", "Set a fixed monthly amount", "% of reinstatement value"],
        index=0,
    )

    maint_monthly = 0.0
    if maint_method.startswith("Â£/mÂ² per year"):
        # Default Â£8/mÂ²/year
        rate_per_m2_y = st.number_input("Maintenance rate (Â£/mÂ²/year)", min_value=0.0, value=8.0, step=0.5)
        st.session_state["maint_rate_per_m2_y"] = rate_per_m2_y
    elif maint_method == "Set a fixed monthly amount":
        maint_monthly = st.number_input("Maintenance", min_value=0.0, value=0.0, step=25.0)
    else:
        # % of reinstatement value
        reinstatement_value = st.number_input("Reinstatement value (Â£)", min_value=0.0, value=0.0, step=10_000.0)
        percent = st.number_input("Annual % of reinstatement value", min_value=0.0, value=2.0, step=0.25, format="%.2f")
        maint_monthly = (reinstatement_value * (percent / 100.0)) / 12.0

    st.markdown("---")
    admin_monthly = st.number_input("Administration", min_value=0.0, value=150.0, step=25.0)

# --------------------------
# Base inputs
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
    "Small (~2,500 ftÂ², ~50Ã—50 ft)",
    "Medium (~5,000 ftÂ²)",
    "Large (~10,000 ftÂ²)",
    "Enter dimensions in ft",
]
size_map = {"Small (~2,500 ftÂ², ~50Ã—50 ft)": 2500, "Medium (~5,000 ftÂ²)": 5000, "Large (~10,000 ftÂ²)": 10000}
workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS)

if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area_ft2 = width * length
else:
    area_ft2 = size_map.get(workshop_size, 0)
area_m2 = area_ft2 * 0.092903 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ftÂ²** Â· **{area_m2:,.0f} mÂ²**")

workshop_energy_types = list(EUI_MAP.keys())
workshop_type = st.selectbox("Workshop type?", ["Select"] + workshop_energy_types)

# Hours label clarifies dual impact
workshop_hours = st.number_input(
    "How many hours per week is the workshop open?",
    min_value=0.0, format="%.2f",
    help="This value affects production capacity and the recommended % share of instructor time for this contract.",
)

num_prisoners = st.number_input("How many prisoners employed?", min_value=0, step=1)
prisoner_salary = st.number_input("Prisoner salary per week (Â£)", min_value=0.0, format="%.2f")

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
            st.caption(f"Avg Total for {region}: **Â£{pay:,.0f}** per year")
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
    st.warning("You have selected less than recommended â€” please explain why here.")
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

# Employment support â†’ development % of OVERHEADS (Commercial only)
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
    "If VAT is ticked and customer is Commercial, Unit Price inc VAT = ex VAT Ã— (1 + VAT%)."
)

# --------------------------
# Validation (shared)
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
    if num_prisoners < 0: errors.append("Prisoners employed cannot be negative")
    if prisoner_salary < 0: errors.append("Prisoner salary per week cannot be negative")
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
    """EUI (kWh/mÂ²/y) Ã— area (mÂ²) Ã— tariff Ã· 12."""
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
    """Electricity, gas, water, admin, maintenance â†’ weekly total + monthly breakdown."""
    if maint_method.startswith("Â£/mÂ² per year"):
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

# Host costs (monthly)
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
    if maint_method.startswith("Â£/mÂ² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", 8.0)
        maint_val = (rate * area_m2) / 12.0
    else:
        maint_val = maint_monthly
    breakdown["Depreciation/Maintenance (estimated)"] = maint_val

    # Development charge on OVERHEADS (Commercial only)
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
        "VAT (Â£)": vat_amount if (customer_type == "Commercial" and apply_vat) else 0.0,
        "Grand Total (Â£/month)": grand_total,
    }
    return breakdown, totals

# --------------------------
# Production helpers
# --------------------------
def labour_minutes_budget(num_pris: int, hours: float) -> float:
    return max(0.0, num_pris * hours * 60.0)

def item_capacity_100(prisoners_assigned: int, minutes_per_item: float, prisoners_required: int, hours: float) -> float:
    """Units/week at 100% = (assigned Ã— hours Ã— 60) / (minutes_per_item Ã— prisoners_required)."""
    if prisoners_assigned <= 0 or minutes_per_item <= 0 or prisoners_required <= 0 or hours <= 0:
        return 0.0
    return (prisoners_assigned * hours * 60.0) / (minutes_per_item * prisoners_required)

def calculate_production_contractual(items, output_percents):
    """Weekly production model (Contractual): Labour minutes apportionment only."""
    overheads_weekly, _detail = weekly_overheads_total()
    sup_weekly_total = (
        sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
        if not customer_covers_supervisors else 0.0
    )
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
            "Unit Cost (Â£)": unit_cost_base,
            "Unit Price ex VAT (Â£)": unit_price_ex_vat,
            "Unit Price inc VAT (Â£)": unit_price_inc_vat,
            # Diagnostics
            "Capacity @100% (units)": cap_100,
            "Weekly Cost (Â£)": weekly_cost_item,
            "Weekly: Prisoners (Â£)": prisoner_weekly_item,
            "Weekly: Supervisors (Â£)": sup_weekly_item,
            "Weekly: Overheads (Â£)": overheads_weekly_item,
            "Share": share,
        })
    return results

# --------------------------
# Display/Export helpers
# --------------------------
def _currency(v) -> str:
    try:
        return f"Â£{float(v):,.2f}"
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
        rows_html.append(f"<tr><td>VAT ({totals.get('VAT %',0):.1f}%)</td><td>{_currency(totals.get('VAT (Â£)',0))}</td></tr>")
    rows_html.append(f"<tr class='grand'><td>Grand Total (Â£/month)</td><td>{_currency(totals.get('Grand Total (Â£/month)',0))}</td></tr>")
    return "<table><tr><th>Cost Item</th><th>Amount (Â£)</th></tr>" + "".join(rows_html) + "</table>"

def display_table(breakdown: dict, totals: dict, total_label="Total Monthly Cost"):
    html = _host_table_html(breakdown, totals, total_label)
    rows = 1 + len(breakdown) + (2 if totals else 0)
    height = 100 + int(rows * 40)
    st.components.v1.html(html, height=height, scrolling=False)

def to_dataframe_host(breakdown: dict, totals: dict) -> pd.DataFrame:
    rows = list(breakdown.items())
    rows += [("Subtotal", sum(breakdown.values())),
             (f"VAT ({totals.get('VAT %',0):.1f}%)", totals.get("VAT (Â£)",0)),
             ("Grand Total (Â£/month)", totals.get("Grand Total (Â£/month)",0))]
    return pd.DataFrame(rows, columns=["Item", "Amount (Â£)"])

def to_dataframe_production(results: list[dict]) -> pd.DataFrame:
    cols = ["Item", "Output %", "Units/week", "Unit Cost (Â£)", "Unit Price ex VAT (Â£)", "Unit Price inc VAT (Â£)"]
    df = pd.DataFrame([{c: r.get(c) for c in cols} for r in results])
    for c in ["Unit Cost (Â£)", "Unit Price ex VAT (Â£)", "Unit Price inc VAT (Â£)"]:
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
        item = str(row["Item"]); val = row["Amount (Â£)"]
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
    header = "<tr><th>Item</th><th>Amount (Â£)</th></tr>"
    return f"<table>{header}{''.join(rows_html)}</table>"

def _render_generic_df_to_html(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    body_rows = []
    for _, row in df.iterrows():
        tds = []
        for col in cols:
            val = row[col]
            if isinstance(val, (int, float)) and pd.notna(val):
                tds.append(f"<td>{_currency(val) if 'Â£' in col else f'{float(val):,.2f}'}</td>")
            else:
                tds.append(f"<td>{_html_escape(val)}</td>")
        body_rows.append(f"<tr>{''.join(tds)}</tr>")
    thead = "<tr>" + "".join([f"<th>{_html_escape(c)}</th>" for c in cols]) + "</tr>"
    return f"<table>{thead}{''.join(body_rows)}</table>"

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="Quote") -> BytesIO:
    html_parts = [f"# {_html_escape(title)}", "\n\n## Cost and Price Calculator â€” Quote\n"]
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

# HOST branch (unchanged behaviour)
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

# PRODUCTION branch
elif workshop_mode == "Production":
    st.subheader("Production Settings")

    # 1) Choose the production type up-front
    prod_type = st.radio(
        "Do you want ad-hoc costs with a deadline, or contractual work?",
        ["Contractual work", "Ad-hoc costs (single item) with a deadline"],
        index=0,
        help="Contractual work = ongoing weekly production. Ad-hoc = a one-off job with a delivery deadline."
    )

    # -----------------------------
    # A) CONTRACTUAL WORK (as normal)
    # -----------------------------
    if prod_type == "Contractual work":
        # Fixed apportionment method per policy (Labour minutes). No radio shown.
        st.caption("Apportionment method: Labour minutes â€” overheads & instructor time are shared by "
                   "assigned labour minutes (assigned prisoners Ã— weekly hours Ã— 60).")

        # Minutes budget & cap
        budget_minutes = labour_minutes_budget(num_prisoners, workshop_hours)
        st.markdown(f"As per your selected resources you have **{budget_minutes:,.0f} Labour minutes** available this week.")

        num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")
        items = []
        OUTPUT_PCT_HELP = (
            "How much of the itemâ€™s theoretical weekly capacity you plan to use this week. "
            "100% assumes assigned prisoners and weekly hours are fully available; reduce to account for rampâ€‘up, changeovers, downtime, etc."
        )

        for i in range(int(num_items)):
            with st.expander(f"Item {i+1} details", expanded=(i == 0)):
                name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
                display_name = (name.strip() or f"Item {i+1}")
                prisoners_required = st.number_input(
                    f"Prisoners required to make 1 item ({display_name})",
                    min_value=1, value=1, step=1, key=f"req_{i}"
                )
                minutes_per_item = st.number_input(
                    f"How many minutes to make 1 item ({display_name})",
                    min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}"
                )
                prisoners_assigned = st.number_input(
                    f"How many prisoners work solely on this item ({display_name})",
                    min_value=0, max_value=int(num_prisoners), value=0, step=1, key=f"assigned_{i}"
                )
                # Capacity preview
                cap_preview = item_capacity_100(prisoners_assigned, minutes_per_item, prisoners_required, workshop_hours)
                st.markdown(f"{display_name} capacity @ 100%: **{cap_preview:.0f} units/week**")

                items.append({
                    "name": name,
                    "required": int(prisoners_required),
                    "minutes": float(minutes_per_item),
                    "assigned": int(prisoners_assigned),
                })

        if errors:
            st.error("Fix errors before production calculations:\n- " + "\n- ".join(errors))
        else:
            used_minutes = sum(int(it["assigned"]) * workshop_hours * 60.0 for it in items)
            st.markdown(f"**Used Labour minutes:** {used_minutes:,.0f} / {budget_minutes:,.0f}")
            if used_minutes > budget_minutes:
                st.error(
                    "Assigned prisoners across items exceed the available weekly Labour minutes. "
                    "Reduce assigned counts, add prisoners, or increase weekly hours."
                )
            else:
                output_percents = []
                for i, it in enumerate(items):
                    disp = (it["name"].strip() or f"Item {i+1}") if isinstance(it["name"], str) else f"Item {i+1}"
                    output_percents.append(
                        st.slider(
                            f"Output % for {disp}",
                            min_value=0, max_value=100, value=100, key=f"percent_{i}",
                            help=OUTPUT_PCT_HELP
                        )
                    )

                results = calculate_production_contractual(items, output_percents)

                for r in results:
                    st.markdown(f"### {r['Item'] or 'Item'}")
                    st.write(f"- Output %: {r['Output %']}%")
                    st.write(f"- Units/week: {r['Units/week']}")
                    if r["Unit Cost (Â£)"] is None:
                        st.write("- Unit Cost (Â£): **N/A** â€” check minutes/prisoners assigned/workshop hours or increase Output %")
                        st.write("- Unit Price ex VAT (Â£): **N/A**")
                        st.write("- Unit Price inc VAT (Â£): **N/A**")
                    else:
                        st.write(f"- Unit Cost (Â£): **Â£{r['Unit Cost (Â£)']:.2f}**")
                        if r["Unit Price ex VAT (Â£)"] is not None:
                            st.write(f"- Unit Price ex VAT (Â£): **Â£{r['Unit Price ex VAT (Â£)']:.2f}**")
                        if r["Unit Price inc VAT (Â£)"] is not None:
                            st.write(f"- Unit Price inc VAT (Â£): **Â£{r['Unit Price inc VAT (Â£)']:.2f}**")

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

    # ----------------------------------------
    # B) AD-HOC COSTS (single item) with deadline
    # ----------------------------------------
    else:
        st.caption("Provide item details and a delivery deadline. The calculator shows if extra prisoners are needed and the total job price.")

        # Ad-hoc item inputs
        adhoc_name = st.text_input("Item Name (adâ€‘hoc)")
        minutes_per_item = st.number_input("Minutes to make 1 item", min_value=1.0, value=10.0, format="%.2f")
        prisoners_required_per_item = st.number_input("Prisoners required to make 1 item", min_value=1, value=1, step=1)
        units_needed = st.number_input("How many units are needed (total)?", min_value=1, step=1, value=100)
        deadline = st.date_input("What is your deadline?", value=date.today())

        # Calculate button
        if st.button("Calculate Adâ€‘hoc Cost", type="primary"):
            # Basic validations (on top of shared)
            local_errors = list(errors)
            display_name = (adhoc_name.strip() or "Item")
            if minutes_per_item <= 0: local_errors.append("Minutes per item must be > 0")
            if prisoners_required_per_item <= 0: local_errors.append("Prisoners required per item must be > 0")
            if units_needed <= 0: local_errors.append("Units needed must be > 0")
            # Weeks until deadline: minimum 1 week
            days_to_deadline = (deadline - date.today()).days
            weeks_to_deadline = max(1, math.ceil(days_to_deadline / 7)) if days_to_deadline is not None else 1

            if workshop_hours <= 0: local_errors.append("Hours per week must be > 0 for Adâ€‘hoc")
            if num_prisoners < 0: local_errors.append("Prisoners employed cannot be negative")
            if prisoner_salary < 0: local_errors.append("Prisoner weekly salary cannot be negative")

            if local_errors:
                st.error("Fix errors:\n- " + "\n- ".join(local_errors))
            else:
                # Totals and capacity calculations
                required_minutes_total = units_needed * minutes_per_item * prisoners_required_per_item
                available_minutes_total_current = num_prisoners * workshop_hours * 60.0 * weeks_to_deadline
                deficit_minutes = max(0.0, required_minutes_total - available_minutes_total_current)

                # Additional prisoners needed across the whole period
                denom = workshop_hours * 60.0 * weeks_to_deadline
                additional_prisoners = int(math.ceil(deficit_minutes / denom)) if denom > 0 else 0
                additional_prisoners = max(0, additional_prisoners)

                assigned_total = num_prisoners + additional_prisoners

                # Weekly requirements for context
                weekly_units_required = math.ceil(units_needed / weeks_to_deadline)
                cap_per_week_100 = item_capacity_100(assigned_total, minutes_per_item, prisoners_required_per_item, workshop_hours)
                output_pct_needed = int(round(min(100.0, (weekly_units_required / cap_per_week_100) * 100.0))) if cap_per_week_100 > 0 else 0

                # Weekly cost components (assign 100% of supervisors & overheads to this job)
                overheads_weekly, _detail = weekly_overheads_total()
                sup_weekly_total = (
                    sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
                    if not customer_covers_supervisors else 0.0
                )
                prisoners_weekly_cost = assigned_total * prisoner_salary  # includes any additional prisoners
                weekly_cost_total = prisoners_weekly_cost + sup_weekly_total + overheads_weekly

                # Job totals (weeks Ã— weekly cost)
                job_cost_ex_vat = weekly_cost_total * weeks_to_deadline
                vat_amount = (job_cost_ex_vat * (vat_rate / 100.0)) if (customer_type == "Commercial" and apply_vat) else 0.0
                job_cost_inc_vat = job_cost_ex_vat + vat_amount

                # Present the plan
                st.markdown(f"### Adâ€‘hoc plan for {display_name}")
                st.write(f"- Deadline: **{deadline.isoformat()}**  â€¢  Weeks available: **{weeks_to_deadline}**")
                st.write(f"- Units required (total): **{units_needed:,}**  â€¢  Required per week (avg): **{weekly_units_required:,}**")
                st.write(f"- With **{assigned_total}** prisoners assigned (current {num_prisoners} + additional {additional_prisoners}),")
                st.write(f"  capacity @100% â‰ˆ **{int(round(cap_per_week_100)):,} units/week** â†’ Output needed â‰ˆ **{output_pct_needed}%**")

                # Price summary table (keeps existing table look)
                rows = [
                    ("Weekly: Prisoners", prisoners_weekly_cost),
                    ("Weekly: Supervisors (apportioned 100%)", sup_weekly_total),
                    ("Weekly: Overheads (apportioned 100%)", overheads_weekly),
                    ("Weekly Total", weekly_cost_total),
                    (f"Weeks to {deadline.isoformat()}", weeks_to_deadline),
                    ("Job Cost (ex VAT)", job_cost_ex_vat),
                ]
                if customer_type == "Commercial" and apply_vat:
                    rows.append((f"VAT ({vat_rate:.1f}%)", vat_amount))
                                    # Add explicit Item Price per unit
                item_price_ex_vat = (job_cost_ex_vat / units_needed) if units_needed > 0 else 0.0
                if customer_type == "Commercial" and apply_vat:
                    item_price_inc_vat = (job_cost_inc_vat / units_needed) if units_needed > 0 else 0.0
                    rows.append(("Item Price per unit (ex VAT)", item_price_ex_vat))
                    rows.append(("Item Price per unit (inc VAT)", item_price_inc_vat))
                else:
                    rows.append(("Item Price per unit", item_price_ex_vat))

rows.append(("Total Job Cost (inc VAT)", job_cost_inc_vat))
                else:
                                    # Add explicit Item Price per unit
                item_price_ex_vat = (job_cost_ex_vat / units_needed) if units_needed > 0 else 0.0
                if customer_type == "Commercial" and apply_vat:
                    item_price_inc_vat = (job_cost_inc_vat / units_needed) if units_needed > 0 else 0.0
                    rows.append(("Item Price per unit (ex VAT)", item_price_ex_vat))
                    rows.append(("Item Price per unit (inc VAT)", item_price_inc_vat))
                else:
                    rows.append(("Item Price per unit", item_price_ex_vat))

rows.append(("Total Job Cost", job_cost_ex_vat))

                # Render the summary table in the same visual style
                # (reuse host table HTML renderer on-the-fly)
                html_rows = []
                for k, v in rows:
                    if isinstance(v, (int, float)) and "Weeks to" not in k:
                        html_rows.append(f"<tr><td>{k}</td><td>{_currency(v)}</td></tr>")
                    else:
                        html_rows.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
                st.components.v1.html(
                    "<table><tr><th>Item</th><th>Amount</th></tr>" + "".join(html_rows) + "</table>",
                    height=100 + int(len(rows) * 40),
                    scrolling=False
                )

                # The key sentence you asked for:
                if additional_prisoners > 0:
                    st.success(
                        f"To produce **{units_needed:,}** units by **{deadline.isoformat()}** we need to employ **{additional_prisoners}** additional prisoner(s)."
                    )
                else:
                    st.success(
                        f"To produce **{units_needed:,}** units by **{deadline.isoformat()}** your current staffing is sufficient (no additional prisoners required)."
                    )

                # Optional export for records
                adhoc_df = pd.DataFrame(
                    [(k, v if not isinstance(v, (int, float)) or "Weeks to" in k else _currency(v)) for k, v in rows],
                    columns=["Item", "Amount"]
                )
                st.download_button(
                    "Download CSV (Adâ€‘hoc)",
                    data=export_csv_bytes(adhoc_df),
                    file_name="adhoc_quote.csv",
                    mime="text/csv",
                )
                # Simple HTML export using same generic renderer
                # (convert currency-like strings back to numeric where possible for consistency)
                st.download_button(
                    "Download PDF-ready HTML (Adâ€‘hoc)",
                    data=export_html(None, adhoc_df.rename(columns={"Amount": "Amount (Â£)"}), title="Ad-hoc Quote"),
                    file_name="adhoc_quote.html",
                    mime="text/html",
                )

# --------------------------
# Footer: Reset Selections (Government Green)
# --------------------------
st.markdown('\n', unsafe_allow_html=True)
if st.button("Reset Selections", type="primary"), key="reset_app_footer"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
st.markdown('\n', unsafe_allow_html=True)

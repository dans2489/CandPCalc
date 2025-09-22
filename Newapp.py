# Cost and Price Calculator — Streamlit app
# v2.4 (2025-09-22)
# Implemented changes:
# - Title set to "Cost and Price Calculator"; header font 2.05rem.
# - When "Host" is selected, no Production settings/sections are shown.
# - Host summary: "Host Contract for [Customer Name] Costs are per month."
# - Remove "(monthly)" from line items; keep "(estimated)" for utilities (not wages).
# - If development charge is £0, highlight reduction due to support offered.
# - Remove all Excel exports; keep CSV and PDF-ready HTML only.

from io import BytesIO
import pandas as pd
import streamlit as st
# -----------------------------
# Page config + simple theming
# -----------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="💷",
    layout="wide",
    initial_sidebar_state="expanded",
)

NFN_BLUE = "#1D428A"

st.markdown(
    f"""
    <style>
      .app-header {{
        background:{NFN_BLUE};
        padding:14px 18px;
        border-radius:6px;
        margin-bottom:14px;
      }}
      .app-title {{
        color:#fff;
        font-size:2.05rem; /* per request */
        line-height:1.1;
        margin:0;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0.5rem 0 1rem 0;
      }}
      th, td {{
        text-align: left;
        padding: 8px 10px;
        border-bottom: 1px solid #e6e6e6;
      }}
      th {{
        background: #f8f8f8;
      }}
    </style>
    <div class="app-header"><h1 class="app-title">Cost and Price Calculator</h1></div>
    """,
    unsafe_allow_html=True,
)

# Optional: quick reset
if st.button("Reset App"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# -----------------------------
# Constants and reference maps
# -----------------------------
ELECTRICITY_RATE_DEFAULT = 0.22  # £/kWh
GAS_RATE_DEFAULT = 0.05          # £/kWh
WATER_RATE_DEFAULT = 2.00        # £/m³

# Evidence-aligned (illustrative) EUI map (kWh/m²/year)
EUI_MAP = {
    "Empty/basic (warehouse)": {"electric_kwh_m2_y": 35, "gas_kwh_m2_y": 30},
    "Light industrial":        {"electric_kwh_m2_y": 45, "gas_kwh_m2_y": 60},
    "Factory (typical)":       {"electric_kwh_m2_y": 30, "gas_kwh_m2_y": 70},
    "High energy process":     {"electric_kwh_m2_y": 60, "gas_kwh_m2_y": 100},
}

# Full Prison → Region mapping (restored)
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

    maint_method = st.radio(
        "Maintenance/Depreciation method",
        ["Set a fixed monthly amount", "% of reinstatement value", "£/m² per year"],
        index=2,
    )
    maint_monthly = 0.0
    if maint_method == "Set a fixed monthly amount":
        maint_monthly = st.number_input(
            "Maintenance", min_value=0.0, value=0.0, step=50.0
        )
    elif maint_method == "% of reinstatement value":
        reinstatement_value = st.number_input(
            "Reinstatement value (£)", min_value=0.0, value=0.0, step=10_000.0
        )
        percent = st.number_input(
            "Annual % of reinstatement value", min_value=0.0, value=2.0, step=0.25, format="%.2f"
        )
        maint_monthly = (reinstatement_value * (percent / 100.0)) / 12.0
    else:  # £/m² per year
        rate_per_m2_y = st.number_input(
            "Maintenance rate (£/m²/year)", min_value=0.0, value=15.0, step=1.0
        )
        st.session_state["maint_rate_per_m2_y"] = rate_per_m2_y

    st.markdown("---")
    admin_monthly = st.number_input(
        "Administration", min_value=0.0, value=150.0, step=25.0
    )

# -------------
# Base inputs
# -------------
st.subheader("Inputs")

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

area_m2 = area_ft2 * 0.092903 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ft²** · **{area_m2:,.0f} m²**")

workshop_energy_types = list(EUI_MAP.keys())
workshop_type = st.selectbox("Workshop type?", ["Select"] + workshop_energy_types)

workshop_hours = st.number_input("How many hours per week is it open? (for production calc)", min_value=0.0, format="%.2f")

num_prisoners = st.number_input("How many prisoners employed?", min_value=0, step=1)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")

# Supervisors
num_supervisors = st.number_input("How many supervisors?", min_value=0, step=1)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s)?")

supervisor_salaries = []
recommended_pct = 0
if not customer_covers_supervisors:
    for i in range(int(num_supervisors)):
        sup_salary = st.number_input(
            f"Supervisor {i+1} annual salary (£)", min_value=0.0, format="%.2f", key=f"sup_salary_{i}"
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
    support = st.selectbox(
        "Customer employment support?",
        ["Select", "None", "Employment on release/RoTL", "Post release", "Both"]
    )
    if support == "None":
        dev_charge = 0.20
    elif support in ["Employment on release/RoTL", "Post release"]:
        dev_charge = 0.10
    elif support == "Both":
        dev_charge = 0.0

# Pricing (Commercial): VAT only
st.markdown("---")
st.subheader("Pricing (Commercial)")
colp1, colp2 = st.columns([1, 1])
with colp1:
    apply_vat = st.checkbox("Apply VAT?")
with colp2:
    vat_rate = st.number_input("VAT rate %", min_value=0.0, max_value=100.0, value=20.0, step=0.5, format="%.1f")

st.caption(
    "Pricing: Unit Cost includes labour + apportioned supervisors + apportioned overheads. "
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
    if workshop_hours <= 0:
        errors.append("Hours per week must be > 0")
    if num_prisoners <= 0:
        errors.append("Enter prisoners employed (>0)")
    if prisoner_salary <= 0:
        errors.append("Enter prisoner salary (>0)")
    if not customer_covers_supervisors:
        if num_supervisors <= 0:
            errors.append("Enter number of supervisors (>0) or tick 'Customer provides supervisor(s)'")
        if any(s <= 0 for s in supervisor_salaries):
            errors.append("Enter all supervisor salaries (>0)")
    return errors

# ----------------
# Cost helpers
# ----------------
def monthly_energy_costs():
    """
    EUI (kWh/m²/y) × area (m²) × tariff ÷ 12.
    """
    eui = EUI_MAP.get(workshop_type, None)
    if not eui or area_m2 <= 0:
        return 0.0, 0.0
    elec_kwh_y = eui["electric_kwh_m2_y"] * area_m2
    gas_kwh_y = eui["gas_kwh_m2_y"] * area_m2
    elec_cost_m = (elec_kwh_y / 12.0) * electricity_rate
    gas_cost_m = (gas_kwh_y / 12.0) * gas_rate
    return elec_cost_m, gas_cost_m

def monthly_water_costs():
    """
    Simple people-based benchmark: ~15 L/person/day, 5 days/week.
    """
    persons = num_prisoners + (0 if customer_covers_supervisors else num_supervisors)
    litres_per_day = 15.0
    days_per_week = 5.0
    weeks_per_year = 52.0
    m3_per_year = (persons * litres_per_day * days_per_week * weeks_per_year) / 1000.0
    return (m3_per_year / 12.0) * water_rate

def weekly_overheads_total():
    """
    Electricity, gas, water, admin, maintenance → weekly total + monthly breakdown.
    """
    if maint_method == "£/m² per year":
        rate = st.session_state.get("maint_rate_per_m2_y", 15.0)
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
        "Depreciation/Maintenance": maint_m,
    }

# ----------------
# Host costs
# ----------------
def calculate_host_costs():
    breakdown = {}

    # Prisoner wages (values are per month)
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52 / 12)

    # Supervisors (apportioned to this contract via chosen_pct)
    supervisor_cost = 0.0
    if not customer_covers_supervisors:
        supervisor_cost = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
    breakdown["Supervisors"] = supervisor_cost

    # Overheads (retain "estimated" only on utilities)
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

    # Development charge (Commercial only), proportion of supervisor cost
    if customer_type == "Commercial":
        dev_amount = supervisor_cost * dev_charge
        if dev_charge == 0.0:
            # Explicitly show the reduction due to support offered
            breakdown["Development charge — reduced to £0 due to support offered"] = 0.0
        else:
            breakdown["Development charge"] = dev_amount
    else:
        breakdown["Development charge"] = 0.0

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
# Production (weekly logic)
# --------------------------
def calculate_production(items: list[dict], output_percents: list[int], apportion_rule: str):
    """
    For each item:
      - Allocates weekly overheads and supervisor cost by selected rule.
      - Computes weekly capacity at 100% output.
      - Applies Output % to get actual units/week.
      - Unit Cost = (weekly costs for the item) / (actual units/week).
      - Prices: Unit Price ex VAT = Unit Cost; inc VAT = ex VAT × (1 + VAT%) if Commercial & VAT on.
    """
    overheads_weekly, _detail = weekly_overheads_total()
    sup_weekly_total = (
        sum([(s / 52) * (chosen_pct / 100) for s in supervisor_salaries])
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

        # Capacity at 100%
        if mins_per_unit <= 0 or prisoners_required <= 0 or prisoners_assigned <= 0 or workshop_hours <= 0:
            capacity_week = 0.0
        else:
            available_mins_week = prisoners_assigned * workshop_hours * 60.0
            minutes_per_unit_total = mins_per_unit * prisoners_required
            capacity_week = available_mins_week / minutes_per_unit_total if minutes_per_unit_total > 0 else 0.0

        # Apportionment share
        if denom > 0:
            share_num = (prisoners_assigned * workshop_hours * 60.0) if apportion_rule.startswith("By labour minutes") else prisoners_assigned
            share = share_num / denom
        else:
            share = 0.0

        # Weekly cost for this item
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
# Display helpers
# ----------------
def display_table(breakdown: dict, totals: dict, total_label="Total Monthly Cost"):
    html = """
    <table>
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
      <tr>
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
        <tr>
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
        html += f"""
        <h2>Host Costs</h2>
        {df_to_html(host_df)}
        """
    if prod_df is not None:
        html += f"""
        <h2>Production Items</h2>
        {df_to_html(prod_df)}
        """
    html += "</body></html>"
    b = BytesIO(html.encode("utf-8"))
    b.seek(0)
    return b

# ----------------
# Main UI branches
# ----------------
errors = validate_inputs()

# HOST BRANCH — No production settings should appear here
if workshop_mode == "Host":
    if st.button("Generate Costs", type="primary"):
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            st.subheader(f"Host Contract for {customer_name} Costs are per month.")
            breakdown, totals = calculate_host_costs()

            # Explicit highlight if dev charge reduced to £0 due to support
            if customer_type == "Commercial" and dev_charge == 0.0:
                st.success("Development charge has been **reduced to £0** due to the **support offered**.")

            display_table(breakdown, totals)

            # Exports (CSV + PDF-ready HTML only)
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

# PRODUCTION BRANCH — Show production settings only when Production is selected
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
            We look at how many **minutes of labour** each item could get in a full week *if everyone is busy the whole time*:  
            **assigned prisoners × weekly hours × 60**.  
            If an item has **more labour minutes available**, it gets a **bigger share** of the weekly overheads and supervisor time.  
            **By assigned prisoners**  
            We just count heads. If an item has **3 prisoners** and another has **1**, the first gets **3×** the share.  
            Either way, when you **turn the Output % down**, you’ll make **fewer units**, so your **cost per unit goes up** (same weekly costs over fewer units).
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
        # Preview capacities + Output % sliders
        output_percents = []
        for i, it in enumerate(items):
            cap_preview = 0.0
            if it["minutes"] > 0 and it["required"] > 0 and it["assigned"] > 0 and workshop_hours > 0:
                cap_preview = (it["assigned"] * workshop_hours * 60.0) / (it["minutes"] * it["required"])
            st.markdown(f"Item {i+1} capacity @ 100%: **{cap_preview:.0f} units/week**")
            output_percents.append(st.slider(f"Output % for Item {i+1}", min_value=0, max_value=100, value=100, key=f"percent_{i}"))

        # Compute and render
        results = calculate_production(items, output_percents, apportion_rule)

        for r in results:
            st.markdown(f"### {r['Item']}")
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

        # Exports (CSV + PDF-ready HTML only)
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

# If no branch selected yet, nudge user
elif workshop_mode == "Select":
    st.info("Select a **Contract type** to continue.")

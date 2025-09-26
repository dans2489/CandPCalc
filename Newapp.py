# Cost and Price Calculator — Streamlit (Tariff C&P integrated)
# Author: M365 Copilot for Dan Smith — 2025-09-26

from __future__ import annotations

from io import BytesIO
from datetime import date
import math
import pandas as pd
import streamlit as st

# -----------------------------
# Page config & light GOV.UK styling
# -----------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="💷",
    layout="wide",
    initial_sidebar_state="expanded",
)

GOV_GREEN = "#00703C"
GOV_GREEN_DARK = "#005A30"
GOV_RED = "#D4351C"
GOV_YELLOW = "#FFDD00"

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Ubuntu, Cantarell,
                   Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
    }}
    .stButton>button {{
      background: {GOV_GREEN}; color: #fff; border: 2px solid {GOV_GREEN_DARK};
      border-radius: 4px; padding: .45rem 1rem; font-weight: 600;
    }}
    .stButton>button:focus {{ outline: 3px solid {GOV_YELLOW}; outline-offset: 1px; }}
    table {{ border-collapse: collapse; width: 100%; margin: .5rem 0 1rem; }}
    th, td {{ border: 1px solid #b1b4b6; padding: .5rem .6rem; text-align: left; }}
    thead th {{ background: #f3f2f1; font-weight: 700; }}
    tr.grand td {{ font-weight: 800; border-top: 3px double #0b0c0c; }}
    td.neg {{ color: {GOV_RED}; }}
    .muted {{ color: #6f777b; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## Cost and Price Calculator\n")

# -----------------------------
# Prison → Region map (unchanged)
# -----------------------------
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
    "Thorn Cross": "National", "Usk": "National", "Verne": "National", "Wakefield": "National", "Wandsworth": "Inner London",
    "Warren Hill": "National", "Wayland": "National", "Wealstun": "National", "Werrington": "National",
    "Wetherby": "National", "Whatton": "National", "Whitemoor": "National", "Winchester": "National",
    "Woodhill": "Inner London", "Wormwood Scrubs": "Inner London", "Wymott": "National",
}

# Instructor pay by Region & Title
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

# -----------------------------
# Tariff bands (from Tariff C&P.xlsx — Sheet "Tariff")
# -----------------------------
TARIFF_BANDS = {
    "low": {
        "intensity_per_year": {"elec_kwh_per_m2": 65, "gas_kwh_per_m2": 80, "water_m3_per_employee": 15, "maint_gbp_per_m2": 8},
        "rates": {"elec_unit": 0.2597, "elec_daily": 0.487, "gas_unit": 0.0629, "gas_daily": 0.3403, "water_unit": 1.30, "admin_monthly": 150.0},
    },
    "medium": {
        "intensity_per_year": {"elec_kwh_per_m2": 110, "gas_kwh_per_m2": 120, "water_m3_per_employee": 15, "maint_gbp_per_m2": 12},
        "rates": {"elec_unit": 0.2597, "elec_daily": 0.487, "gas_unit": 0.0629, "gas_daily": 0.3403, "water_unit": 1.30, "admin_monthly": 150.0},
    },
    "high": {
        "intensity_per_year": {"elec_kwh_per_m2": 160, "gas_kwh_per_m2": 180, "water_m3_per_employee": 15, "maint_gbp_per_m2": 15},
        "rates": {"elec_unit": 0.2597, "elec_daily": 0.487, "gas_unit": 0.0629, "gas_daily": 0.3403, "water_unit": 1.30, "admin_monthly": 150.0},
    },
}
# (All rates above are exactly from your workbook.)  # [1](https://justiceuk-my.sharepoint.com/personal/dan_smith1_justice_gov_uk/_layouts/15/Doc.aspx?sourcedoc=%7BEB8330F5-8F7E-4D43-903F-E329FB3AD976%7D&file=Tariff%20C%26P.xlsx&action=default&mobileredirect=true)

DAYS_PER_MONTH = 365.0 / 12.0
FT2_TO_M2 = 0.092903

# -----------------------------
# Helpers (render/exports)
# -----------------------------
def _currency(v) -> str:
    try:
        return f"£{float(v):,.2f}"
    except Exception:
        return ""

def _render_table_two_col(rows, amount_header="Amount (£)") -> str:
    """rows: list of tuples (label, value, is_currency, is_grand=False)."""
    out = ["<table>", f"<thead><tr><th>Item</th><th>{amount_header}</th></tr></thead>", "<tbody>"]
    for label, value, is_currency, *rest in rows:
        is_grand = bool(rest[0]) if rest else False
        if value is None:
            val_txt = ""
        elif is_currency:
            val_txt = _currency(value)
        else:
            try:
                fval = float(value)
                val_txt = f"{int(fval):,}" if fval.is_integer() else f"{fval:,.2f}"
            except Exception:
                val_txt = str(value)
        tr_cls = " class='grand'" if is_grand else ""
        out.append(f"<tr{tr_cls}><td>{label}</td><td>{val_txt}</td></tr>")
    out.append("</tbody></table>")
    return "".join(out)

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
        rows_html.append(f"<tr{grand_cls}><td>{item}</td><td{neg_cls}>{_currency(val)}</td></tr>")
    header = "<thead><tr><th>Item</th><th>Amount (£)</th></tr></thead>"
    return f"<table>{header}<tbody>{''.join(rows_html)}</tbody></table>"

def _render_generic_df_to_html(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    thead = "<thead><tr>" + "".join([f"<th>{c}</th>" for c in cols]) + "</tr></thead>"
    body_rows = []
    for _, row in df.iterrows():
        tds = []
        for col in cols:
            val = row[col]
            if isinstance(val, (int, float)) and pd.notna(val):
                tds.append(f"<td>{_currency(val) if '£' in col else f'{float(val):,.2f}'}</td>")
            else:
                tds.append(f"<td>{val}</td>")
        body_rows.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table>{thead}<tbody>{''.join(body_rows)}</tbody></table>"

def export_csv_bytes(df: pd.DataFrame) -> BytesIO:
    b = BytesIO(); df.to_csv(b, index=False); b.seek(0); return b

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="Quote") -> BytesIO:
    # Keep the same GOV.UK-like table chrome as in-app
    parts = [f"<h1>{title}</h1>",
             f"<p class='muted'>Date: {date.today().isoformat()}</p>",
             f"<p class='muted'><strong>Customer:</strong> {st.session_state.get('customer_name','')} &nbsp;|&nbsp; "
             f"<strong>Prison:</strong> {st.session_state.get('prison_choice','')} &nbsp;|&nbsp; "
             f"<strong>Region:</strong> {st.session_state.get('region_text','')}</p>"]
    if host_df is not None:
        parts += ["<h2>Host Costs</h2>", _render_host_df_to_html(host_df)]
    if prod_df is not None:
        parts += ["<h2>Production Items</h2>", _render_generic_df_to_html(prod_df)]
    parts.append("<p class='muted'>Prices are indicative and may change based on final scope and site conditions.</p>")
    html = """
    <style>
      body { font-family: Arial, Helvetica, sans-serif; margin: 14mm; color:#0b0c0c; }
      table { border-collapse: collapse; width: 100%; margin: .5rem 0 1rem; }
      th, td { border: 1px solid #b1b4b6; padding: .5rem .6rem; text-align: left; }
      thead th { background: #f3f2f1; font-weight: 700; }
      tr.grand td { font-weight: 800; border-top: 3px double #0b0c0c; }
      td.neg { color: #D4351C; }
      .muted { color:#6f777b; }
    </style>
    """ + "\n".join(parts)
    b = BytesIO(html.encode("utf-8")); b.seek(0); return b

# -----------------------------
# Base inputs (main area)
# -----------------------------
prisons_sorted = ["Select"] + sorted(PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0, key="prison_choice")
region = PRISON_TO_REGION.get(prison_choice, "Select") if prison_choice != "Select" else "Select"
# Always show current region text (no sticky key here so it updates every run)
region_text = "" if region == "Select" else region
st.text_input("Region", value=region_text, disabled=True)
st.session_state["region_text"] = region_text  # for exports

customer_type = st.selectbox("I want to quote for", ["Select", "Commercial", "Another Government Department"], key="customer_type")
customer_name = st.text_input("Customer Name", key="customer_name")
workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"], key="workshop_mode")

# Workshop size mapping (Small=500, Medium=2,500, Large=5,000; or custom)
SIZE_LABELS = ["Select", "Small (500 ft²)", "Medium (2,500 ft²)", "Large (5,000 ft²)", "Enter dimensions in ft"]
SIZE_MAP = {"Small (500 ft²)": 500, "Medium (2,500 ft²)": 2500, "Large (5,000 ft²)": 5000}

workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS, key="workshop_size")
if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area_ft2 = width * length
else:
    area_ft2 = SIZE_MAP.get(workshop_size, 0)
area_m2 = area_ft2 * FT2_TO_M2 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ft²** · **{area_m2:,.0f} m²**")

# Usage band with '?' explainer
tariff_cols = st.columns([1, 0.1])
with tariff_cols[0]:
    workshop_usage = st.radio(
        "Workshop usage tariff",
        ["Low usage", "Medium usage", "High usage"],
        horizontal=True,
        key="workshop_usage",
        help=("Use intensity profiles used in UK non‑domestic benchmarking (e.g. DEC/TM46) — "
              "pick the band matching your process intensity & hours."),
    )
with tariff_cols[1]:
    if st.button("?", key="usage_help_btn"):
        st.session_state["show_usage_help"] = not st.session_state.get("show_usage_help", False)
if st.session_state.get("show_usage_help", False):
    st.info(
        "• **Low**: storage/basic workshop — lighting, small power, space heating only (limited machinery). "
        "• **Medium**: light industrial — small machinery, some MEV/plug loads, longer hours. "
        "• **High**: manufacturing/process — powered machinery/compressed air, extended shifts.\n"
        "(Based on UK DEC/CIBSE TM46 approaches to non‑domestic energy profiling.)"
    )  # [3](https://www.gov.uk/government/publications/display-energy-certificates-and-advisory-reports-for-public-buildings/a-guide-to-display-energy-certificates-and-advisory-reports-for-public-buildings)[2](https://www.cibse.org/knowledge-research/knowledge-portal/tm46-energy-benchmarks)

USAGE_KEY = ("low" if "Low" in workshop_usage else "medium" if "Medium" in workshop_usage else "high")

# -----------------------------
# Tariff application (to state) BEFORE sidebar is drawn
# -----------------------------
for k, v in {
    "elec_unit": None, "elec_daily": None, "gas_unit": None, "gas_daily": None,
    "water_unit": None, "admin_monthly": None, "maint_rate_per_m2_y": None, "last_band": None
}.items():
    st.session_state.setdefault(k, v)

needs_seed = any(st.session_state[k] is None for k in
                 ["elec_unit", "elec_daily", "gas_unit", "gas_daily", "water_unit", "admin_monthly", "maint_rate_per_m2_y"])
if st.session_state["last_band"] != USAGE_KEY or needs_seed:
    band = TARIFF_BANDS[USAGE_KEY]
    st.session_state.update({
        "elec_unit": band["rates"]["elec_unit"],
        "elec_daily": band["rates"]["elec_daily"],
        "gas_unit":  band["rates"]["gas_unit"],
        "gas_daily": band["rates"]["gas_daily"],
        "water_unit": band["rates"]["water_unit"],
        "admin_monthly": band["rates"]["admin_monthly"],
        "maint_rate_per_m2_y": band["intensity_per_year"]["maint_gbp_per_m2"],
        "last_band": USAGE_KEY,
    })

# -----------------------------
# Cost functions (use state + area/headcount)
# -----------------------------
def monthly_energy_costs() -> tuple[float, float]:
    elec_kwh_y = TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["elec_kwh_per_m2"] * (area_m2 or 0.0)
    gas_kwh_y  = TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["gas_kwh_per_m2"]  * (area_m2 or 0.0)
    elec_m = (elec_kwh_y / 12.0) * st.session_state["elec_unit"] + st.session_state["elec_daily"] * DAYS_PER_MONTH
    gas_m  = (gas_kwh_y  / 12.0) * st.session_state["gas_unit"]  + st.session_state["gas_daily"] * DAYS_PER_MONTH
    return elec_m, gas_m

def monthly_water_costs() -> float:
    persons = st.session_state.get("num_prisoners", 0) + (0 if st.session_state.get("customer_covers_supervisors", False) else st.session_state.get("num_supervisors", 0))
    m3_per_year = persons * TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["water_m3_per_employee"]
    return (m3_per_year / 12.0) * st.session_state["water_unit"]

def weekly_overheads_total() -> tuple[float, dict]:
    # Maintenance — by default tariff £/m²/yr unless user chose a fixed amount/% (set below)
    maint_method = st.session_state.get("maint_method", "£/m² per year (industry standard)")
    if maint_method.startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["maint_gbp_per_m2"])
        maint_m = (rate * (area_m2 or 0.0)) / 12.0
    else:
        maint_m = st.session_state.get("maint_monthly", 0.0)

    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()
    admin_m = st.session_state.get("admin_monthly", 150.0)

    overheads_m = elec_m + gas_m + water_m + admin_m + maint_m
    detail = {
        "Electricity (estimated)": elec_m,
        "Gas (estimated)": gas_m,
        "Water (estimated)": water_m,
        "Administration": admin_m,
        "Depreciation/Maintenance (estimated)": maint_m,
    }
    weekly = overheads_m * 12.0 / 52.0
    return weekly, detail

# -----------------------------
# Sidebar — Tariff rates only (READ‑ONLY)
# -----------------------------
with st.sidebar:
    st.header("Tariffs (read‑only)")

    # Two columns: Electricity & Gas, then Water / Maintenance / Admin
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Electricity unit (₤/kWh)", f"£{st.session_state['elec_unit']:.4f}/kWh", disabled=True)
        st.text_input("Gas unit (₤/kWh)",        f"£{st.session_state['gas_unit']:.4f}/kWh", disabled=True)
        st.text_input("Water unit (₤/m³)",       f"£{st.session_state['water_unit']:.2f}/m³", disabled=True)
    with c2:
        st.text_input("Electricity daily (₤/day)", f"£{st.session_state['elec_daily']:.3f}/day", disabled=True)
        st.text_input("Gas daily (₤/day)",         f"£{st.session_state['gas_daily']:.3f}/day", disabled=True)
        st.text_input("Admin (₤/month)",           f"£{st.session_state['admin_monthly']:.2f}/month", disabled=True)

    st.text_input("Maintenance (₤/m²/year)", f"£{st.session_state['maint_rate_per_m2_y']:.2f} per m²/year", disabled=True)

# -----------------------------
# Hours / staffing & instructors
# -----------------------------
workshop_hours = st.number_input(
    "How many hours per week is the workshop open?",
    min_value=0.0, format="%.2f",
    help="Affects production capacity and the recommended % share of instructor time for this contract.",
    key="workshop_hours",
)
num_prisoners = st.number_input("How many prisoners employed?", min_value=0, step=1, key="num_prisoners")
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f", key="prisoner_salary")

num_supervisors = st.number_input("How many instructors?", min_value=0, step=1, key="num_supervisors")
customer_covers_supervisors = st.checkbox("Customer provides instructor(s)?", key="customer_covers_supervisors")

supervisor_salaries = []
if not customer_covers_supervisors:
    titles_for_region = SUPERVISOR_PAY.get(region, [])
    if region == "Select" or not titles_for_region:
        st.warning("Select a prison to derive the Region before assigning instructor titles.")
    else:
        for i in range(int(num_supervisors)):
            options = [t["title"] for t in titles_for_region]
            sel = st.selectbox(f"Instructor {i+1} title", options, key=f"inst_title_{i}")
            pay = next(t["avg_total"] for t in titles_for_region if t["title"] == sel)
            st.caption(f"Avg Total for {region_text or 'Region'}: **£{pay:,.0f}** per year")
            supervisor_salaries.append(float(pay))

contracts = st.number_input("How many contracts do these instructors oversee?", min_value=1, value=1, key="contracts")
recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if contracts and workshop_hours >= 0 else 0

st.subheader("Instructor Time Allocation")
st.info(f"Recommended: {recommended_pct}%")
chosen_pct = st.slider("Adjust instructor % allocation", 0, 100, int(recommended_pct), key="chosen_pct")
if chosen_pct < int(round(recommended_pct)):
    st.warning("You have selected less than recommended — please explain why here.")
    reason = st.text_area("Reason for using a lower allocation", key="alloc_reason")
    action = st.radio("Apply allocation", ["Keep recommended", "Set new"], index=0, horizontal=True, key="alloc_action")
    if action == "Set new":
        effective_pct = int(round(recommended_pct)) if not str(reason).strip() else int(chosen_pct)
    else:
        effective_pct = int(round(recommended_pct))
else:
    effective_pct = int(round(recommended_pct))

# Employment support → development % of OVERHEADS (Commercial only)
dev_rate = 0.0
if customer_type == "Commercial":
    support = st.selectbox("Customer employment support?", ["Select", "None", "Employment on release/RoTL", "Post release", "Both"], key="support")
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
    apply_vat = st.checkbox("Apply VAT?", key="apply_vat")
with colp2:
    vat_rate = st.number_input("VAT rate %", min_value=0.0, max_value=100.0, value=20.0, step=0.5, format="%.1f", key="vat_rate")
st.caption(
    "Unit pricing: Unit Cost includes labour + apportioned instructors + apportioned overheads. "
    "No margin control: Unit Price ex VAT = Unit Cost. "
    "If VAT is ticked and customer is Commercial, Unit Price inc VAT = ex VAT × (1 + VAT%)."
)

# -----------------------------
# Validation
# -----------------------------
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
    if area_ft2 <= 0:
        errors.append("Area must be greater than zero")
    if workshop_mode == "Production" and workshop_hours <= 0:
        errors.append("Hours per week must be > 0 (Production)")
    if num_prisoners < 0:
        errors.append("Prisoners employed cannot be negative")
    if prisoner_salary < 0:
        errors.append("Prisoner salary per week cannot be negative")
    if not customer_covers_supervisors:
        if num_supervisors <= 0:
            errors.append("Enter number of instructors (>0) or tick 'Customer provides instructor(s)'")
        if region == "Select":
            errors.append("Select a prison/region to populate instructor titles")
        if len(supervisor_salaries) != int(num_supervisors):
            errors.append("Choose a title for each instructor")
        if any(s <= 0 for s in supervisor_salaries):
            errors.append("Instructor Avg Total must be > 0")
    return errors

# -----------------------------
# Production helpers & model (Contractual)
# -----------------------------
def labour_minutes_budget(num_pris: int, hours: float) -> float:
    return max(0.0, num_pris * hours * 60.0)

def item_capacity_100(prisoners_assigned: int, minutes_per_item: float, prisoners_required: int, hours: float) -> float:
    if prisoners_assigned <= 0 or minutes_per_item <= 0 or prisoners_required <= 0 or hours <= 0:
        return 0.0
    return (prisoners_assigned * hours * 60.0) / (minutes_per_item * prisoners_required)

def calculate_production_contractual(items, output_percents):
    overheads_weekly, _detail = weekly_overheads_total()
    inst_weekly_total = (
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
        inst_weekly_item = inst_weekly_total * share
        overheads_weekly_item = overheads_weekly * share

        weekly_cost_item = prisoner_weekly_item + inst_weekly_item + overheads_weekly_item

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
            "Capacity @100% (units)": cap_100,
            "Weekly Cost (£)": weekly_cost_item,
            "Weekly: Prisoners (£)": prisoner_weekly_item,
            "Weekly: Instructors (£)": inst_weekly_item,
            "Weekly: Overheads (£)": overheads_weekly_item,
            "Share": share,
        })
    return results

# -----------------------------
# Main UI branches
# -----------------------------
errors = validate_inputs()

# HOST branch
if workshop_mode == "Host":
    if st.button("Generate Costs"):
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            heading_name = customer_name if str(customer_name).strip() else "Customer"
            st.subheader(f"Host Contract for {heading_name} (costs are per month)")

            breakdown = {}
            breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52 / 12)

            instructor_cost = 0.0
            if not customer_covers_supervisors:
                instructor_cost = sum((s / 12) * (effective_pct / 100) for s in supervisor_salaries)
            breakdown["Instructors"] = instructor_cost

            elec_m, gas_m = monthly_energy_costs()
            water_m = monthly_water_costs()
            breakdown["Electricity (estimated)"] = elec_m
            breakdown["Gas (estimated)"] = gas_m
            breakdown["Water (estimated)"] = water_m
            breakdown["Administration"] = st.session_state.get("admin_monthly", 150.0)

            if st.session_state.get("maint_method", "£/m² per year (industry standard)").startswith("£/m² per year"):
                rate = st.session_state.get("maint_rate_per_m2_y", TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["maint_gbp_per_m2"])
                breakdown["Depreciation/Maintenance (estimated)"] = (rate * (area_m2 or 0.0)) / 12.0
            else:
                breakdown["Depreciation/Maintenance (estimated)"] = st.session_state.get("maint_monthly", 0.0)

            overheads_subtotal = sum([
                breakdown.get("Electricity (estimated)", 0.0),
                breakdown.get("Gas (estimated)", 0.0),
                breakdown.get("Water (estimated)", 0.0),
                breakdown.get("Administration", 0.0),
                breakdown.get("Depreciation/Maintenance (estimated)", 0.0),
            ])

            dev_baseline_rate = 0.20
            dev_baseline_amount = overheads_subtotal * dev_baseline_rate
            if customer_type == "Commercial":
                dev_applied_amount = overheads_subtotal * dev_rate
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

            rows = list(breakdown.items()) + [
                ("Subtotal", subtotal),
                (f"VAT ({vat_rate:.1f}%)" if (customer_type == "Commercial" and apply_vat) else "VAT (0.0%)", vat_amount),
                ("Grand Total (£/month)", grand_total),
            ]
            host_df = pd.DataFrame(rows, columns=["Item", "Amount (£)"])
            st.markdown(_render_host_df_to_html(host_df), unsafe_allow_html=True)

            st.download_button("Download CSV (Host)", data=export_csv_bytes(host_df), file_name="host_quote.csv", mime="text/csv")
            st.download_button("Download PDF-ready HTML (Host)", data=export_html(host_df, None, title="Host Quote"),
                               file_name="host_quote.html", mime="text/html")
# -----------------------------
# PRODUCTION branch
# -----------------------------
elif workshop_mode == "Production":
    st.subheader("Production Settings")

    prod_type = st.radio(
        "Do you want ad-hoc costs with a deadline, or contractual work?",
        ["Contractual work", "Ad-hoc costs (multiple lines) with deadlines"],
        index=0,
        help=(
            "Contractual work = ongoing weekly production (items and unit prices per week). "
            "Ad‑hoc = one‑off job(s) with delivery deadlines; calculator estimates if extra prisoners are needed."
        ),
        key="prod_type"
    )

    # A) CONTRACTUAL WORK (unchanged model: labour-minutes apportionment)
    if prod_type == "Contractual work":
        st.caption(
            "Apportionment method: Labour minutes — overheads & instructor time are shared by "
            "assigned labour minutes (assigned prisoners × weekly hours × 60)."
        )
        budget_minutes = labour_minutes_budget(num_prisoners, workshop_hours)
        st.markdown(f"As per your selected resources you have **{budget_minutes:,.0f} Labour minutes** available this week.")

        num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")
        items = []
        OUTPUT_PCT_HELP = (
            "How much of the item’s theoretical weekly capacity you plan to use this week. "
            "100% assumes assigned prisoners and weekly hours are fully available; reduce to account for "
            "ramp‑up, changeovers, downtime, etc."
        )

        for i in range(int(num_items)):
            with st.expander(f"Item {i+1} details", expanded=(i == 0)):
                name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
                display_name = (name.strip() or f"Item {i+1}") if isinstance(name, str) else f"Item {i+1}"
                prisoners_required = st.number_input(
                    f"Prisoners required to make 1 item ({display_name})", min_value=1, value=1, step=1, key=f"req_{i}"
                )
                minutes_per_item = st.number_input(
                    f"How many minutes to make 1 item ({display_name})", min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}"
                )
                prisoners_assigned = st.number_input(
                    f"How many prisoners work solely on this item ({display_name})",
                    min_value=0, max_value=int(num_prisoners), value=0, step=1, key=f"assigned_{i}"
                )
                cap_preview = item_capacity_100(prisoners_assigned, minutes_per_item, prisoners_required, workshop_hours)
                st.markdown(f"{display_name} capacity @ 100%: **{cap_preview:.0f} units/week**")
                items.append({
                    "name": name, "required": int(prisoners_required), "minutes": float(minutes_per_item), "assigned": int(prisoners_assigned),
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
                        st.slider(f"Output % for {disp}", min_value=0, max_value=100, value=100, key=f"percent_{i}", help=OUTPUT_PCT_HELP)
                    )

                results = calculate_production_contractual(items, output_percents)

                # Export table
                prod_df = pd.DataFrame(
                    [
                        {k: (None if r[k] is None else (round(float(r[k]), 2) if isinstance(r[k], (int, float)) else r[k]))
                         for k in ["Item", "Output %", "Units/week", "Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]}
                        for r in results
                    ]
                )
                st.markdown(_render_generic_df_to_html(prod_df), unsafe_allow_html=True)
                st.download_button("Download CSV (Production)", data=export_csv_bytes(prod_df), file_name="production_quote.csv", mime="text/csv")
                st.download_button("Download PDF-ready HTML (Production)", data=export_html(None, prod_df, title="Production Quote"),
                                   file_name="production_quote.html", mime="text/html")

    # B) AD‑HOC COSTS (MULTI‑LINE) with per-line deadlines
    else:
        st.caption(
            "Enter how many **product lines** you need. For each line, provide the item name, total units requested, "
            "deadline, number of prisoners to make **one** unit, and minutes to make **one** unit. "
            "The calculator will estimate if additional prisoners are required to meet the deadlines."
        )

        num_lines = st.number_input("How many product lines are needed?", min_value=1, value=1, step=1, key="adhoc_num_lines")

        lines = []
        for i in range(int(num_lines)):
            with st.expander(f"Line {i+1}", expanded=(i == 0)):
                item_name = st.text_input(f"Item name (Line {i+1})", key=f"adhoc_name_{i}")
                units_requested = st.number_input(f"Units requested (Line {i+1})", min_value=1, value=100, step=1, key=f"adhoc_units_{i}")
                deadline = st.date_input(f"Deadline (Line {i+1})", value=date.today(), key=f"adhoc_deadline_{i}")
                pris_per_item = st.number_input(f"Prisoners to make one (Line {i+1})", min_value=1, value=1, step=1, key=f"adhoc_pris_req_{i}")
                minutes_per_item = st.number_input(f"Minutes to make one (Line {i+1})", min_value=1.0, value=10.0, format="%.2f", key=f"adhoc_mins_{i}")
                lines.append({
                    "name": (item_name.strip() or f"Line {i+1}") if isinstance(item_name, str) else f"Line {i+1}",
                    "units": int(units_requested),
                    "deadline": deadline,
                    "pris_per_item": int(pris_per_item),
                    "mins_per_item": float(minutes_per_item),
                })

        if st.button("Calculate Ad‑hoc Cost", key="calc_adhoc"):
            local_errors = list(errors)
            if workshop_hours <= 0:
                local_errors.append("Hours per week must be > 0 for Ad‑hoc")
            if num_prisoners < 0:
                local_errors.append("Prisoners employed cannot be negative")
            if prisoner_salary < 0:
                local_errors.append("Prisoner weekly salary cannot be negative")
            for i, ln in enumerate(lines):
                if ln["units"] <= 0:
                    local_errors.append(f"Line {i+1}: Units requested must be > 0")
                if ln["pris_per_item"] <= 0:
                    local_errors.append(f"Line {i+1}: Prisoners to make one must be > 0")
                if ln["mins_per_item"] <= 0:
                    local_errors.append(f"Line {i+1}: Minutes to make one must be > 0")

            if local_errors:
                st.error("Fix errors:\n- " + "\n- ".join(local_errors))
            else:
                # Per-line weeks to deadline, total minutes, and weekly demand
                weeks_each = []
                total_minutes_all = 0.0
                weekly_minutes_demand = 0.0
                for ln in lines:
                    days_to_deadline = (ln["deadline"] - date.today()).days
                    weeks_i = max(1, math.ceil(days_to_deadline / 7)) if days_to_deadline is not None else 1
                    weeks_each.append(weeks_i)
                    minutes_total_line = ln["units"] * ln["mins_per_item"] * ln["pris_per_item"]
                    total_minutes_all += minutes_total_line
                    weekly_minutes_demand += minutes_total_line / weeks_i

                # Current weekly capacity (prisoners only)
                weekly_minutes_capacity = num_prisoners * workshop_hours * 60.0
                deficit_weekly = max(0.0, weekly_minutes_demand - weekly_minutes_capacity)
                denom_per_prisoner_week = workshop_hours * 60.0
                additional_prisoners = int(math.ceil(deficit_weekly / denom_per_prisoner_week)) if denom_per_prisoner_week > 0 else 0
                additional_prisoners = max(0, additional_prisoners)
                assigned_total = num_prisoners + additional_prisoners

                # Job duration to cost for: conservative = max weeks across lines
                job_weeks = max(weeks_each) if weeks_each else 1

                # Weekly costs
                overheads_weekly, _detail = weekly_overheads_total()
                inst_weekly_total = (
                    sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
                    if not customer_covers_supervisors else 0.0
                )
                prisoners_weekly_cost = assigned_total * prisoner_salary
                weekly_cost_total = prisoners_weekly_cost + inst_weekly_total + overheads_weekly

                # Job totals
                job_cost_ex_vat = weekly_cost_total * job_weeks
                vat_amount = (job_cost_ex_vat * (vat_rate / 100.0)) if (customer_type == "Commercial" and apply_vat) else 0.0
                job_cost_inc_vat = job_cost_ex_vat + vat_amount

                # Output narrative
                if additional_prisoners > 0:
                    st.write(
                        f"To meet all deadlines (max **{job_weeks}** week{'s' if job_weeks>1 else ''}) "
                        f"we need to employ **{additional_prisoners}** additional prisoner(s)."
                    )
                else:
                    st.write(
                        f"Your current staffing is sufficient to meet all deadlines "
                        f"(max **{job_weeks}** week{'s' if job_weeks>1 else ''})."
                    )

                # Per-line summary table (non-monetary)
                summary_rows = [("Total minutes (all lines)", total_minutes_all, True, False)]
                for i, ln in enumerate(lines):
                    summary_rows.append((f"Line {i+1}: {ln['name']} — Units", ln["units"], False, False))
                    summary_rows.append((f"Line {i+1}: Deadline (weeks)", weeks_each[i], False, False))
                    summary_rows.append((f"Line {i+1}: Minutes/Unit × Prisoners", ln["mins_per_item"] * ln["pris_per_item"], False, False))
                st.markdown(_render_table_two_col(summary_rows, amount_header="Value"), unsafe_allow_html=True)

                # Monetary summary table
                adhoc_rows = [
                    ("Weeks to complete (max across lines)", job_weeks, False, False),
                    ("Weekly: Prisoners", prisoners_weekly_cost, True, False),
                    ("Weekly: Instructors (100%)", inst_weekly_total, True, False),
                    ("Weekly: Overheads (100%)", overheads_weekly, True, False),
                    ("Weekly Total", weekly_cost_total, True, False),
                    ("Job Cost (ex VAT)", job_cost_ex_vat, True, False),
                ]
                if customer_type == "Commercial" and apply_vat:
                    adhoc_rows.append((f"VAT ({vat_rate:.1f}%)", vat_amount, True, False))
                    adhoc_rows.append(("Total Job Cost (inc VAT)", job_cost_inc_vat, True, True))
                else:
                    adhoc_rows.append(("Total Job Cost", job_cost_ex_vat, True, True))

                st.markdown(_render_table_two_col(adhoc_rows), unsafe_allow_html=True)

                # Export (CSV/HTML)
                export_rows = [(lbl, val if isinstance(val, (int, float)) else str(val)) for (lbl, val, *_rest) in adhoc_rows]
                adhoc_export_df = pd.DataFrame(export_rows, columns=["Item", "Amount (£)"])
                st.download_button("Download CSV (Ad‑hoc)", data=export_csv_bytes(adhoc_export_df),
                                   file_name="adhoc_quote.csv", mime="text/csv")
                st.download_button("Download PDF-ready HTML (Ad‑hoc)",
                                   data=export_html(None, adhoc_export_df, title="Ad‑hoc Quote — Multiple Lines"),
                                   file_name="adhoc_quote.html", mime="text/html")

# -----------------------------
# Footer: Reset Selections (green)
# -----------------------------
st.markdown('\n', unsafe_allow_html=True)
if st.button("Reset Selections", key="reset_app_footer"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
st.markdown('\n', unsafe_allow_html=True)


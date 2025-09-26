# Cost and Price Calculator — Streamlit app
# Centered layout, neutral/wide sidebar (editable rates only), tariff intensities with active-band highlight,
# hour‑scaled variable energy (baseline 27 h/wk), Region display fix, Ad‑hoc (working days) with concise outputs.
# Author: M365 Copilot for Dan Smith — 2025‑09‑26

from __future__ import annotations
from io import BytesIO
from datetime import date, timedelta
import math
import pandas as pd
import streamlit as st

# -----------------------------
# Page config & GOV.UK styling (CENTERED + wider/neutral sidebar)
# -----------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="💷",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Neutral CSS (no f-string → avoids brace escaping; neutral sidebar; full-width buttons)
st.markdown(
    """
    <style>
    /* Typography */
    html, body, [class*="css"] {
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Ubuntu, Cantarell,
                   Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
    }
    /* Primary buttons – full width for alignment */
    .stButton > button {
      background: #00703C; color: #fff; border: 2px solid #005A30;
      border-radius: 4px; padding: .50rem 1rem; font-weight: 600; width: 100%;
    }
    .stButton > button:focus { outline: 3px solid #FFDD00; outline-offset: 2px; }
    /* Download buttons full width as well */
    .stDownloadButton > button { width: 100%; }

    /* Tables (GOV.UK-like chrome) */
    table { border-collapse: collapse; width: 100%; margin: .5rem 0 1rem; }
    th, td { border: 1px solid #b1b4b6; padding: .5rem .6rem; text-align: left; }
    thead th { background: #f3f2f1; font-weight: 700; }
    tr.grand td { font-weight: 800; border-top: 3px double #0b0c0c; }
    td.neg { color: #D4351C; }
    .muted { color: #6f777b; }

    /* Wider, neutral sidebar (no green background/border) */
    [data-testid="stSidebar"] > div:first-child {
      min-width: 420px; max-width: 480px; padding-right: 8px;
    }
    /* Optional neutral callout in the sidebar */
    .sb-callout {
      background: #f3f2f1; border-left: 6px solid #b1b4b6;
      padding: 8px 10px; margin-bottom: 6px; font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## Cost and Price Calculator\n")

# -----------------------------
# Constants
# -----------------------------
DAYS_PER_MONTH = 365.0 / 12.0   # ≈30.42
FT2_TO_M2 = 0.092903
BASE_HOURS_PER_WEEK = 27.0      # baseline for variable (kWh) scaling

# -----------------------------
# Prison → Region map
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
    "Preston": "National", "Ranby": "National", "Risley": "National", "Rochester": "National",
    "Rye Hill": "National", "Send": "National", "Spring Hill": "National", "Stafford": "National",
    "Standford Hill": "National", "Stocken": "National", "Stoke Heath": "National", "Styal": "National",
    "Sudbury": "National", "Swaleside": "National", "Swansea": "National", "Swinfen Hall": "National",
    "Thameside": "Inner London", "Thorn Cross": "National", "Usk": "National", "Verne": "National",
    "Wakefield": "National", "Wandsworth": "Inner London", "Warren Hill": "National", "Wayland": "National",
    "Wealstun": "National", "Werrington": "National", "Wetherby": "National", "Whatton": "National",
    "Whitemoor": "National", "Winchester": "National", "Woodhill": "Inner London", "Wormwood Scrubs": "Inner London",
    "Wymott": "National",
}

# Instructor pay (“Instructor”)
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
# Tariff bands (Tariff C&P.xlsx — Sheet "Tariff")
# -----------------------------
TARIFF_BANDS = {
    "low": {
        "intensity_per_year": {
            "elec_kwh_per_m2": 65, "gas_kwh_per_m2": 80,
            "water_m3_per_employee": 15, "maint_gbp_per_m2": 8,
        },
        "rates": {
            "elec_unit": 0.2597, "elec_daily": 0.487,
            "gas_unit": 0.0629,  "gas_daily": 0.3403,
            "water_unit": 1.30, "admin_monthly": 150.0,
        },
    },
    "medium": {
        "intensity_per_year": {
            "elec_kwh_per_m2": 110, "gas_kwh_per_m2": 120,
            "water_m3_per_employee": 15, "maint_gbp_per_m2": 12,
        },
        "rates": {
            "elec_unit": 0.2597, "elec_daily": 0.487,
            "gas_unit": 0.0629,  "gas_daily": 0.3403,
            "water_unit": 1.30, "admin_monthly": 150.0,
        },
    },
    "high": {
        "intensity_per_year": {
            "elec_kwh_per_m2": 160, "gas_kwh_per_m2": 180,
            "water_m3_per_employee": 15, "maint_gbp_per_m2": 15,
        },
        "rates": {
            "elec_unit": 0.2597, "elec_daily": 0.487,
            "gas_unit": 0.0629,  "gas_daily": 0.3403,
            "water_unit": 1.30, "admin_monthly": 150.0,
        },
    },
}

# -----------------------------
# Render / export helpers (GOV.UK-like)
# -----------------------------
def _currency(v) -> str:
    try:
        return f"£{float(v):,.2f}"
    except Exception:
        return ""

def _render_host_df_to_html(host_df: pd.DataFrame) -> str:
    rows_html = []
    for _, row in host_df.iterrows():
        item = str(row["Item"])
        val = row["Amount (£)"]
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
    b = BytesIO()
    df.to_csv(b, index=False)
    b.seek(0)
    return b

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="Quote") -> BytesIO:
    css = """
    <meta charset="utf-8">
    <style>
      body { font-family: Arial, Helvetica, sans-serif; margin: 14mm; color: #0b0c0c; }
      h1,h2,h3 { font-weight: 700; margin: 0 0 8px 0; }
      table { border-collapse: collapse; width: 100%; margin: 8px 0 16px 0; }
      th, td { border: 1px solid #B1B4B6; padding: 8px; text-align: left; }
      th { background: #F3F2F1; font-weight: 600; }
      tr.grand td { border-top: 3px double #0B0C0C; font-weight: 700; }
      td.neg { color: #D4351C; }
      .muted { color: #6f777b; }
    </style>
    """
    meta = (
        f"<p class='muted'><strong>Date:</strong> {date.today().isoformat()}<br>"
        f"<strong>Customer:</strong> {st.session_state.get('customer_name','')}<br>"
        f"<strong>Prison:</strong> {st.session_state.get('prison_choice','')}<br>"
        f"<strong>Region:</strong> {st.session_state.get('region','')}</p>"
    )
    parts = [css, f"<h1>{title}</h1>", meta]
    if host_df is not None:
        parts += ["<h2>Host Costs</h2>", _render_host_df_to_html(host_df)]
    if prod_df is not None:
        section_title = "Ad‑hoc Items" if "Ad‑hoc" in str(title) else "Production Items"
        parts += [f"<h2>{section_title}</h2>", _render_generic_df_to_html(prod_df)]
    parts.append("<p class='muted'>Prices are indicative and may change based on final scope and site conditions.</p>")
    b = BytesIO("".join(parts).encode("utf-8"))
    b.seek(0)
    return b

# -----------------------------
# Base inputs (main area)
# -----------------------------
prisons_sorted = ["Select"] + sorted(PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0, key="prison_choice")
region = PRISON_TO_REGION.get(prison_choice, "Select") if prison_choice != "Select" else "Select"
st.session_state["region"] = region
st.text_input("Region", value=(region if region != "Select" else ""), key="region_display", disabled=True)

customer_type = st.selectbox("I want to quote for", ["Select", "Commercial", "Another Government Department"], key="customer_type")
customer_name = st.text_input("Customer Name", key="customer_name")
workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"], key="workshop_mode")

# Workshop size mapping
SIZE_LABELS = ["Select", "Small (500 ft²)", "Medium (2,500 ft²)", "Large (5,000 ft²)", "Enter dimensions in ft"]
SIZE_MAP = {"Small (500 ft²)": 500, "Medium (2,500 ft²)": 2500, "Large (5,000 ft²)": 5000}

workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS, key="workshop_size")
if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area_ft2 = (width or 0.0) * (length or 0.0)
else:
    area_ft2 = SIZE_MAP.get(workshop_size, 0)
area_m2 = area_ft2 * FT2_TO_M2 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ft²** · **{area_m2:,.0f} m²**")

# Usage band selector with corrected definitions (no “band selected” badge)
workshop_usage = st.radio(
    "Workshop usage tariff",
    ["Low usage", "Medium usage", "High usage"],
    horizontal=True,
    key="workshop_usage",
)
USAGE_KEY = ("low" if "Low" in workshop_usage else "medium" if "Medium" in workshop_usage else "high")
st.caption(
    "**What these mean:** "
    "**Low** – heated & lit, light plug/process loads; minimal machinery. "
    "**Medium** – mixed light industrial with intermittent small machinery + lighting/IT. "
    "**High** – machinery‑heavy or continuous processes plus lighting/IT and heating. "
    "(Aligned with UK operational benchmarking practice.)"
)

# -----------------------------
# Sidebar — Tariffs & Overheads (editable rates only; no calculations shown)
# -----------------------------
with st.sidebar:
    st.header("Tariffs & Overheads")
    st.markdown("<div class='sb-callout'>← Set your tariff & overhead rates here</div>", unsafe_allow_html=True)

    # Intensities for ALL bands with active-band highlight
    elec_low  = TARIFF_BANDS["low"]["intensity_per_year"]["elec_kwh_per_m2"]
    elec_med  = TARIFF_BANDS["medium"]["intensity_per_year"]["elec_kwh_per_m2"]
    elec_high = TARIFF_BANDS["high"]["intensity_per_year"]["elec_kwh_per_m2"]
    gas_low   = TARIFF_BANDS["low"]["intensity_per_year"]["gas_kwh_per_m2"]
    gas_med   = TARIFF_BANDS["medium"]["intensity_per_year"]["gas_kwh_per_m2"]
    gas_high  = TARIFF_BANDS["high"]["intensity_per_year"]["gas_kwh_per_m2"]
    water_per_emp_y = TARIFF_BANDS["low"]["intensity_per_year"]["water_m3_per_employee"]

    def _mark(v, band): return f"**{v}** ← selected" if USAGE_KEY == band else f"{v}"
    st.caption(
        "**Electricity intensity (kWh/m²/year):** "
        f"Low {_mark(elec_low,'low')} • Medium {_mark(elec_med,'medium')} • High {_mark(elec_high,'high')}"
    )
    st.caption(
        "**Gas intensity (kWh/m²/year):** "
        f"Low {_mark(gas_low,'low')} • Medium {_mark(gas_med,'medium')} • High {_mark(gas_high,'high')}"
    )
    st.caption(f"**Water:** **{water_per_emp_y} m³ per employee per year**")

    # Ensure keys exist
    for k, v in {
        "electricity_rate": None, "elec_daily": None,
        "gas_rate": None, "gas_daily": None,
        "water_rate": None, "admin_monthly": None,
        "maint_rate_per_m2_y": None, "last_applied_band": None,
        "maint_method": "£/m² per year (industry standard)",
    }.items():
        st.session_state.setdefault(k, v)

    # Apply selected band defaults before drawing widgets
    needs_seed = any(st.session_state[k] is None for k in [
        "electricity_rate", "elec_daily", "gas_rate", "gas_daily",
        "water_rate", "admin_monthly", "maint_rate_per_m2_y"
    ])
    if st.session_state["last_applied_band"] != USAGE_KEY or needs_seed:
        band = TARIFF_BANDS[USAGE_KEY]
        st.session_state.update({
            "electricity_rate":    band["rates"]["elec_unit"],
            "elec_daily":          band["rates"]["elec_daily"],
            "gas_rate":            band["rates"]["gas_unit"],
            "gas_daily":           band["rates"]["gas_daily"],
            "water_rate":          band["rates"]["water_unit"],
            "admin_monthly":       band["rates"]["admin_monthly"],
            "maint_rate_per_m2_y": band["intensity_per_year"]["maint_gbp_per_m2"],
            "last_applied_band":   USAGE_KEY,
        })

    # Editable RATE FIELDS (no calculations shown here)
    st.markdown("**Electricity**")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.number_input("Unit rate (£/kWh)", min_value=0.0, step=0.0001, format="%.4f", key="electricity_rate")
    with col_e2:
        st.number_input("Daily charge (£/day)", min_value=0.0, step=0.001, format="%.3f", key="elec_daily")

    st.markdown("**Gas**")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.number_input("Unit rate (£/kWh)", min_value=0.0, step=0.0001, format="%.4f", key="gas_rate")
    with col_g2:
        st.number_input("Daily charge (£/day)", min_value=0.0, step=0.001, format="%.3f", key="gas_daily")

    st.markdown("**Water**")
    st.number_input("Unit rate (£/m³)", min_value=0.0, step=0.10, format="%.2f", key="water_rate")

    st.markdown("**Maintenance / Depreciation**")
    maint_method = st.radio(
        "Method",
        ["£/m² per year (industry standard)", "Set a fixed monthly amount", "% of reinstatement value"],
        index=0 if str(st.session_state.get("maint_method","")).startswith("£/m²") else
              (1 if st.session_state.get("maint_method") == "Set a fixed monthly amount" else 2),
        key="maint_method"
    )

    if maint_method.startswith("£/m² per year"):
        st.number_input(
            "Maintenance rate (£/m²/year)",
            min_value=0.0, step=0.5,
            value=float(st.session_state["maint_rate_per_m2_y"]),
            key="maint_rate_per_m2_y"
        )
    elif maint_method == "Set a fixed monthly amount":
        st.number_input("Maintenance (monthly £)", min_value=0.0, value=float(st.session_state.get("maint_monthly", 0.0)),
                        step=25.0, key="maint_monthly")
    else:
        st.number_input("Reinstatement value (£)", min_value=0.0, value=float(st.session_state.get("reinstate_val", 0.0)),
                        step=10_000.0, key="reinstate_val")
        st.number_input("Annual % of reinstatement value", min_value=0.0, value=float(st.session_state.get("reinstate_pct", 2.0)),
                        step=0.25, format="%.2f", key="reinstate_pct")

    st.markdown("**Administration**")
    st.number_input("Admin (monthly £)", min_value=0.0, step=25.0, key="admin_monthly")

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
            st.caption(f"Avg Total for {region}: **£{pay:,.0f}** per year")
            supervisor_salaries.append(float(pay))

# Contracts & recommended allocation
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
if customer_type == "Commercial":
    support = st.selectbox(
        "Customer employment support?",
        ["Select", "None", "Employment on release/RoTL", "Post release", "Both"],
        key="support",
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
# Cost functions (variable kWh scaled by hours; standing charges unscaled)
# -----------------------------
def monthly_energy_costs() -> tuple[float, float]:
    band = TARIFF_BANDS[USAGE_KEY]
    elec_kwh_y = band["intensity_per_year"]["elec_kwh_per_m2"] * (area_m2 or 0.0)
    gas_kwh_y  = band["intensity_per_year"]["gas_kwh_per_m2"]  * (area_m2 or 0.0)
    try:
        hours_scale = max(0.0, float(workshop_hours)) / float(BASE_HOURS_PER_WEEK)
    except Exception:
        hours_scale = 1.0
    elec_unit  = float(st.session_state["electricity_rate"])
    gas_unit   = float(st.session_state["gas_rate"])
    elec_daily = float(st.session_state["elec_daily"])
    gas_daily  = float(st.session_state["gas_daily"])
    elec_var_m = (elec_kwh_y / 12.0) * elec_unit * hours_scale
    gas_var_m  = (gas_kwh_y  / 12.0) * gas_unit  * hours_scale
    elec_fix_m = elec_daily * DAYS_PER_MONTH
    gas_fix_m  = gas_daily  * DAYS_PER_MONTH
    return elec_var_m + elec_fix_m, gas_var_m + gas_fix_m

def monthly_water_costs() -> float:
    band = TARIFF_BANDS[USAGE_KEY]
    persons = num_prisoners + (0 if customer_covers_supervisors else num_supervisors)
    m3_per_year = persons * band["intensity_per_year"]["water_m3_per_employee"]
    return (m3_per_year / 12.0) * float(st.session_state["water_rate"])

def weekly_overheads_total() -> tuple[float, dict]:
    if st.session_state.get("maint_method", "£/m² per year").startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["maint_gbp_per_m2"])
        maint_m = (float(rate) * (area_m2 or 0.0)) / 12.0
    elif st.session_state.get("maint_method") == "Set a fixed monthly amount":
        maint_m = float(st.session_state.get("maint_monthly", 0.0))
    else:
        reinstate_val = float(st.session_state.get("reinstate_val", 0.0))
        pct = float(st.session_state.get("reinstate_pct", 0.0))
        maint_m = (reinstate_val * (pct / 100.0)) / 12.0

    elec_m, gas_m = monthly_energy_costs()
    water_m = monthly_water_costs()
    admin_m = float(st.session_state.get("admin_monthly", 150.0))
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
# Production helpers (Contractual)
# -----------------------------
def labour_minutes_budget(num_pris: int, hours: float) -> float:
    return max(0.0, num_pris * hours * 60.0)

def item_capacity_100(prisoners_assigned: int, minutes_per_item: float, prisoners_required: int, hours: float) -> float:
    if prisoners_assigned <= 0 or minutes_per_item <= 0 or prisoners_required <= 0 or hours <= 0:
        return 0.0
    return (prisoners_assigned * hours * 60.0) / (minutes_per_item * prisoners_required)

# (Main UI branches continue in Part 2)
errors = validate_inputs()
# -----------------------------
# Production pricing helper (Contractual model)
# -----------------------------
def calculate_production_contractual(items, output_percents):
    """
    Apportions weekly overheads + instructor time by assigned labour minutes
    (assigned prisoners × weekly hours × 60). Computes unit costs accordingly.
    """
    overheads_weekly, _detail = weekly_overheads_total()
    inst_weekly_total = (
        sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
        if not st.session_state.get("customer_covers_supervisors", False) else 0.0
    )
    denom = sum(int(it.get("assigned", 0)) * workshop_hours * 60.0 for it in items)
    results = []
    for idx, item in enumerate(items):
        name = (item.get("name", "") or "").strip() or f"Item {idx+1}"
        mins_per_unit = float(item.get("minutes", 0))
        prisoners_required = int(item.get("required", 1))
        prisoners_assigned = int(item.get("assigned", 0))
        output_pct = int(output_percents[idx]) if idx < len(output_percents) else 100

        # Weekly capacity at 100% for this line
        if prisoners_assigned > 0 and mins_per_unit > 0 and prisoners_required > 0 and workshop_hours > 0:
            cap_100 = (prisoners_assigned * workshop_hours * 60.0) / (mins_per_unit * prisoners_required)
        else:
            cap_100 = 0.0

        # Share for apportionment
        share = ((prisoners_assigned * workshop_hours * 60.0) / denom) if denom > 0 else 0.0

        # Weekly costs for this line
        prisoner_weekly_item = prisoners_assigned * prisoner_salary
        inst_weekly_item = inst_weekly_total * share
        overheads_weekly_item = overheads_weekly * share
        weekly_cost_item = prisoner_weekly_item + inst_weekly_item + overheads_weekly_item

        actual_units = cap_100 * (output_pct / 100.0)
        unit_cost_base = (weekly_cost_item / actual_units) if actual_units > 0 else None

        unit_price_ex_vat = unit_cost_base
        if unit_price_ex_vat is not None and (customer_type == "Commercial" and apply_vat):
            unit_price_inc_vat = unit_price_ex_vat * (1 + (vat_rate / 100.0))
        else:
            unit_price_inc_vat = unit_price_ex_vat

        results.append({
            "Item": name,
            "Output %": output_pct,
            "Units/week": 0 if actual_units <= 0 else int(round(actual_units)),
            "Unit Cost (£)": unit_cost_base,
            "Unit Price ex VAT (£)": unit_price_ex_vat,
            "Unit Price inc VAT (£)": unit_price_inc_vat,
        })
    return results

# -----------------------------
# Main UI branches (Host / Production)
# -----------------------------
errors_top = validate_inputs()

# HOST branch
if workshop_mode == "Host":
    if st.button("Generate Costs"):
        if errors_top:
            st.error("Fix errors:\n- " + "\n- ".join(errors_top))
        else:
            heading_name = customer_name if str(customer_name).strip() else "Customer"
            st.subheader(f"Host Contract for {heading_name} (costs are per month)")

            # Build host breakdown (monthly)
            breakdown = {}
            breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52 / 12)

            instructor_cost = 0.0
            if not st.session_state.get("customer_covers_supervisors", False):
                instructor_cost = sum((s / 12) * (effective_pct / 100) for s in supervisor_salaries)
            breakdown["Instructors"] = instructor_cost

            elec_m, gas_m = monthly_energy_costs()
            water_m = monthly_water_costs()
            breakdown["Electricity (estimated)"] = elec_m
            breakdown["Gas (estimated)"] = gas_m
            breakdown["Water (estimated)"] = water_m
            breakdown["Administration"] = float(st.session_state.get("admin_monthly", 150.0))

            # Maintenance per chosen method
            if st.session_state.get("maint_method", "£/m² per year").startswith("£/m² per year"):
                rate = float(st.session_state.get("maint_rate_per_m2_y", TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["maint_gbp_per_m2"]))
                breakdown["Depreciation/Maintenance (estimated)"] = (rate * (area_m2 or 0.0)) / 12.0
            elif st.session_state.get("maint_method") == "Set a fixed monthly amount":
                breakdown["Depreciation/Maintenance (estimated)"] = float(st.session_state.get("maint_monthly", 0.0))
            else:
                reinstate_val = float(st.session_state.get("reinstate_val", 0.0))
                pct = float(st.session_state.get("reinstate_pct", 0.0))
                breakdown["Depreciation/Maintenance (estimated)"] = (reinstate_val * (pct / 100.0)) / 12.0

            overheads_subtotal = (
                breakdown["Electricity (estimated)"] +
                breakdown["Gas (estimated)"] +
                breakdown["Water (estimated)"] +
                breakdown["Administration"] +
                breakdown["Depreciation/Maintenance (estimated)"]
            )

            # Development charge rules (Commercial only)
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

            rows = list(breakdown.items()) + [
                ("Subtotal", subtotal),
                (f"VAT ({vat_rate:.1f}%)" if (customer_type == "Commercial" and apply_vat) else "VAT (0.0%)", vat_amount),
                ("Grand Total (£/month)", grand_total),
            ]
            host_df = pd.DataFrame(rows, columns=["Item", "Amount (£)"])
            st.markdown(_render_host_df_to_html(host_df), unsafe_allow_html=True)

            # Downloads (two columns; full‑width buttons via CSS)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("Download CSV (Host)", data=export_csv_bytes(host_df), file_name="host_quote.csv", mime="text/csv")
            with c2:
                st.download_button("Download PDF-ready HTML (Host)", data=export_html(host_df, None, title="Host Quote"),
                                   file_name="host_quote.html", mime="text/html")

# PRODUCTION branch
elif workshop_mode == "Production":
    st.subheader("Production Settings")

    prod_type = st.radio(
        "Do you want ad-hoc costs with a deadline, or contractual work?",
        ["Contractual work", "Ad-hoc costs (multiple lines) with deadlines"],
        index=0,
        help="Contractual work = ongoing weekly production. Ad‑hoc = one‑off job(s) with delivery deadlines; feasibility uses working days (Mon–Fri).",
        key="prod_type"
    )

    # ---------------- A) CONTRACTUAL WORK (labour-minutes apportionment) ----------------
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
            "100% assumes assigned prisoners and weekly hours are fully available; reduce for ramp‑up/changeovers/downtime."
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
                if prisoners_assigned > 0 and minutes_per_item > 0 and prisoners_required > 0 and workshop_hours > 0:
                    cap_preview = (prisoners_assigned * workshop_hours * 60.0) / (minutes_per_item * prisoners_required)
                else:
                    cap_preview = 0.0
                st.markdown(f"{display_name} capacity @ 100%: **{cap_preview:.0f} units/week**")
                items.append({
                    "name": name,
                    "required": int(prisoners_required),
                    "minutes": float(minutes_per_item),
                    "assigned": int(prisoners_assigned),
                })

        if validate_inputs():
            st.error("Fix errors before production calculations:\n- " + "\n- ".join(validate_inputs()))
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

                prod_df = pd.DataFrame([
                    {k: (None if r[k] is None else (round(float(r[k]), 2) if isinstance(r[k], (int, float)) else r[k]))
                     for k in ["Item", "Output %", "Units/week", "Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]}
                    for r in results
                ])
                st.markdown(_render_generic_df_to_html(prod_df), unsafe_allow_html=True)

                # Downloads
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button("Download CSV (Production)", data=export_csv_bytes(prod_df),
                                       file_name="production_quote.csv", mime="text/csv")
                with d2:
                    st.download_button("Download PDF-ready HTML (Production)",
                                       data=export_html(None, prod_df, title="Production Quote"),
                                       file_name="production_quote.html", mime="text/html")

    # ---------------- B) AD‑HOC COSTS (MULTI‑LINE) — working-day feasibility & concise summary ----------------
    else:
        def working_days_between(start: date, end: date) -> int:
            """Inclusive working days Mon–Fri between start and end."""
            if end < start:
                return 0
            days, d = 0, start
            while d <= end:
                if d.weekday() < 5:
                    days += 1
                d += timedelta(days=1)
            return days

        num_lines = st.number_input("How many product lines are needed?", min_value=1, value=1, step=1, key="adhoc_num_lines")

        lines = []
        for i in range(int(num_lines)):
            with st.expander(f"Product line {i+1}", expanded=(i == 0)):
                # Row 1: Item, Units, Deadline
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    item_name = st.text_input("Item name", key=f"adhoc_name_{i}")
                with c2:
                    units_requested = st.number_input("Units requested", min_value=1, value=100, step=1, key=f"adhoc_units_{i}")
                with c3:
                    deadline = st.date_input("Deadline", value=date.today(), key=f"adhoc_deadline_{i}")

                # Row 2: Prisoners to make one, Minutes to make one
                c4, c5 = st.columns([1, 1])
                with c4:
                    pris_per_item = st.number_input("Prisoners to make one", min_value=1, value=1, step=1, key=f"adhoc_pris_req_{i}")
                with c5:
                    minutes_per_item = st.number_input("Minutes to make one", min_value=1.0, value=10.0, format="%.2f", key=f"adhoc_mins_{i}")

                lines.append({
                    "name": (item_name.strip() or f"Item {i+1}") if isinstance(item_name, str) else f"Item {i+1}",
                    "units": int(units_requested),
                    "deadline": deadline,
                    "pris_per_item": int(pris_per_item),
                    "mins_per_item": float(minutes_per_item),
                })

        if st.button("Calculate Ad‑hoc Cost", key="calc_adhoc"):
            errs = validate_inputs()
            if workshop_hours <= 0:
                errs.append("Hours per week must be > 0 for Ad‑hoc")
            for i, ln in enumerate(lines):
                if ln["units"] <= 0:
                    errs.append(f"Line {i+1}: Units requested must be > 0")
                if ln["pris_per_item"] <= 0:
                    errs.append(f"Line {i+1}: Prisoners to make one must be > 0")
                if ln["mins_per_item"] <= 0:
                    errs.append(f"Line {i+1}: Minutes to make one must be > 0")

            if errs:
                st.error("Fix errors:\n- " + "\n- ".join(errs))
            else:
                # Capacity per working day
                hours_per_day = float(workshop_hours) / 5.0  # Mon–Fri
                daily_minutes_capacity_per_prisoner = hours_per_day * 60.0
                current_daily_capacity = num_prisoners * daily_minutes_capacity_per_prisoner

                # Weekly costs → per-minute cost (concise; no breakdown shown)
                overheads_weekly, _detail = weekly_overheads_total()
                inst_weekly_total = (
                    sum((s / 52) * (effective_pct / 100) for s in supervisor_salaries)
                    if not st.session_state.get("customer_covers_supervisors", False) else 0.0
                )
                prisoners_weekly_cost = num_prisoners * prisoner_salary
                weekly_cost_total = prisoners_weekly_cost + inst_weekly_total + overheads_weekly
                minutes_per_week_capacity = max(1e-9, num_prisoners * workshop_hours * 60.0)
                cost_per_minute = weekly_cost_total / minutes_per_week_capacity

                # Per-line metrics
                per_line = []
                total_job_minutes = 0.0
                earliest_wd_available = None
                today = date.today()

                for ln in lines:
                    mins_per_unit = ln["mins_per_item"] * ln["pris_per_item"]
                    unit_cost_ex_vat = cost_per_minute * mins_per_unit
                    unit_cost_inc_vat = (unit_cost_ex_vat * (1 + (vat_rate/100.0))) if (customer_type == "Commercial" and apply_vat) else unit_cost_ex_vat

                    total_line_minutes = ln["units"] * mins_per_unit
                    total_job_minutes += total_line_minutes

                    wd_available = working_days_between(today, ln["deadline"])
                    if earliest_wd_available is None or wd_available < earliest_wd_available:
                        earliest_wd_available = wd_available

                    if current_daily_capacity > 0:
                        wd_needed_line_alone = math.ceil(total_line_minutes / current_daily_capacity)
                    else:
                        wd_needed_line_alone = float("inf")

                    per_line.append({
                        "name": ln["name"],
                        "units": ln["units"],
                        "unit_cost_ex_vat": unit_cost_ex_vat,
                        "unit_cost_inc_vat": unit_cost_inc_vat,
                        "line_total_ex_vat": unit_cost_ex_vat * ln["units"],
                        "line_total_inc_vat": unit_cost_inc_vat * ln["units"],
                        "wd_available": wd_available,
                        "wd_needed_line_alone": wd_needed_line_alone,
                    })

                # Overall job feasibility (aggregate)
                if current_daily_capacity > 0:
                    wd_needed_all = math.ceil(total_job_minutes / current_daily_capacity)
                else:
                    wd_needed_all = float("inf")
                earliest_wd_available = earliest_wd_available or 0

                # Extra prisoners required to hit the tightest deadline
                if earliest_wd_available > 0 and current_daily_capacity > 0:
                    required_minutes_per_day = total_job_minutes / earliest_wd_available
                    deficit_per_day = max(0.0, required_minutes_per_day - current_daily_capacity)
                    extra_prisoners_needed = int(math.ceil(deficit_per_day / daily_minutes_capacity_per_prisoner)) if deficit_per_day > 0 else 0
                else:
                    extra_prisoners_needed = 0

                # Output summary table (Item, Units, Unit cost, Line total)
                show_inc = (customer_type == "Commercial" and apply_vat)
                col_headers = [
                    "Item", "Units",
                    "Unit Cost (£" + (" inc VAT" if show_inc else "") + ")",
                    "Line Total (£" + (" inc VAT" if show_inc else "") + ")"
                ]
                data_rows = []
                total_ex_vat = 0.0
                total_inc_vat = 0.0
                for p in per_line:
                    data_rows.append([
                        p["name"],
                        f"{p['units']:,}",
                        f"{(p['unit_cost_inc_vat'] if show_inc else p['unit_cost_ex_vat']):.2f}",
                        f"{(p['line_total_inc_vat'] if show_inc else p['line_total_ex_vat']):.2f}",
                    ])
                    total_ex_vat += p["line_total_ex_vat"]
                    total_inc_vat += p["line_total_inc_vat"]

                table_html = ["<table><thead><tr>"] + [f"<th>{h}</th>" for h in col_headers] + ["</tr></thead><tbody>"]
                for r in data_rows:
                    table_html.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
                table_html.append("</tbody></table>")
                st.markdown("".join(table_html), unsafe_allow_html=True)

                # Totals
                if show_inc:
                    st.markdown(f"**Total Job Cost (inc VAT): £{total_inc_vat:,.2f}**")
                    st.caption(f"Total Job Cost (ex VAT): £{total_ex_vat:,.2f}")
                else:
                    st.markdown(f"**Total Job Cost: £{total_ex_vat:,.2f}**")

                # Feasibility message (working days only)
                if current_daily_capacity <= 0:
                    st.error("No production capacity (0 prisoners or 0 hours).")
                else:
                    if wd_needed_all <= earliest_wd_available:
                        st.success(f"Based on the data entered, the products will be ready in **{wd_needed_all} working day(s)**.")
                    else:
                        st.warning(
                            f"Not feasible by the earliest deadline (in **{earliest_wd_available} working day(s)**). "
                            f"With current staffing, you need **{wd_needed_all} working day(s)**. "
                            f"**Extra prisoners required:** {extra_prisoners_needed}"
                        )

                # Summary export (CSV/HTML) — Ad‑hoc Items title in export_html()
                summary_df = pd.DataFrame([
                    {
                        "Item": p["name"],
                        "Units": p["units"],
                        ("Unit Cost inc VAT (£)" if show_inc else "Unit Cost (£)"): round(p["unit_cost_inc_vat"] if show_inc else p["unit_cost_ex_vat"], 2),
                        ("Line Total inc VAT (£)" if show_inc else "Line Total (£)"): round(p["line_total_inc_vat"] if show_inc else p["line_total_ex_vat"], 2),
                    }
                    for p in per_line
                ])
                totals_row = {
                    "Item": "TOTAL",
                    "Units": sum(p["units"] for p in per_line),
                    ("Unit Cost inc VAT (£)" if show_inc else "Unit Cost (£)"): "",
                    ("Line Total inc VAT (£)" if show_inc else "Line Total (£)"): round(total_inc_vat if show_inc else total_ex_vat, 2),
                }
                summary_df = pd.concat([summary_df, pd.DataFrame([totals_row])], ignore_index=True)

                # Downloads (two columns; full‑width via CSS)
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button("Download CSV (Ad‑hoc)", data=export_csv_bytes(summary_df),
                                       file_name="adhoc_summary.csv", mime="text/csv")
                with d2:
                    st.download_button(
                        "Download PDF-ready HTML (Ad‑hoc)",
                        data=export_html(None, summary_df, title="Ad‑hoc Quote — Summary"),
                        file_name="adhoc_quote.html",
                        mime="text/html"
                    )

# -----------------------------
# Footer: Reset Selections
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

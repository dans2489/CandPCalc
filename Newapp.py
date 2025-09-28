from __future__ import annotations
from io import BytesIO
from datetime import date, timedelta
import math
import pandas as pd
import streamlit as st

import config
from style import inject_govuk_style

# -----------------------------
# Page config & styling
# -----------------------------
st.set_page_config(
    page_title="Cost and Price Calculator",
    page_icon="💷",
    layout="centered"
)
inject_govuk_style(st)

st.markdown("## Cost and Price Calculator\n")

# -----------------------------
# Helper functions
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
        section_title = "Ad-hoc Items" if "Ad-hoc" in str(title) else "Production Items"
        parts += [f"<h2>{section_title}</h2>", _render_generic_df_to_html(prod_df)]
    parts.append("<p class='muted'>Prices are indicative and may change based on final scope and site conditions.</p>")
    b = BytesIO("".join(parts).encode("utf-8"))
    b.seek(0)
    return b

# -----------------------------
# Base inputs
# -----------------------------
prisons_sorted = ["Select"] + sorted(config.PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0, key="prison_choice")
region = config.PRISON_TO_REGION.get(prison_choice, "Select") if prison_choice != "Select" else "Select"
st.session_state["region"] = region
st.text_input("Region", value=region if region != "Select" else "", key="region_display", disabled=True)

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
area_m2 = area_ft2 * config.FT2_TO_M2 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ft²** · **{area_m2:,.0f} m²**")

# Usage band selector
workshop_usage = st.radio(
    "Workshop usage tariff",
    ["Low usage", "Medium usage", "High usage"],
    horizontal=True,
    key="workshop_usage",
)
USAGE_KEY = ("low" if "Low" in workshop_usage else "medium" if "Medium" in workshop_usage else "high")

# -----------------------------
# Cost functions
# -----------------------------
def monthly_energy_costs(area_m2: float, workshop_hours: float, USAGE_KEY: str) -> tuple[float, float]:
    band = config.TARIFF_BANDS[USAGE_KEY]
    elec_kwh_y = band["intensity_per_year"]["elec_kwh_per_m2"] * area_m2
    gas_kwh_y  = band["intensity_per_year"]["gas_kwh_per_m2"] * area_m2
    hours_scale = max(0.0, float(workshop_hours)) / float(config.BASE_HOURS_PER_WEEK)
    uplift = config.REGION_UPLIFT.get(region, 1.0)
    elec_unit  = float(st.session_state.get("electricity_rate", band["rates"]["elec_unit"])) * uplift
    gas_unit   = float(st.session_state.get("gas_rate", band["rates"]["gas_unit"])) * uplift
    elec_daily = float(st.session_state.get("elec_daily", band["rates"]["elec_daily"]))
    gas_daily  = float(st.session_state.get("gas_daily", band["rates"]["gas_daily"]))
    elec_var_m = (elec_kwh_y / 12.0) * elec_unit * hours_scale
    gas_var_m  = (gas_kwh_y  / 12.0) * gas_unit  * hours_scale
    elec_fix_m = elec_daily * config.DAYS_PER_MONTH
    gas_fix_m  = gas_daily  * config.DAYS_PER_MONTH
    return elec_var_m + elec_fix_m, gas_var_m + gas_fix_m

def monthly_maintenance_cost(area_m2: float, workshop_hours: float, USAGE_KEY: str) -> float:
    maint_method = st.session_state.get("maint_method", "£/m² per year")
    uplift = config.REGION_UPLIFT.get(region, 1.0)
    if maint_method.startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", config.TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["maint_gbp_per_m2"])
        hours_scale = max(0.0, float(workshop_hours)) / float(config.BASE_HOURS_PER_WEEK)
        return ((float(rate) * uplift) * area_m2 / 12.0) * hours_scale
    elif maint_method == "Set a fixed monthly amount":
        return float(st.session_state.get("maint_monthly", 0.0))
    else:
        reinstate_val = float(st.session_state.get("reinstate_val", 0.0))
        pct = float(st.session_state.get("reinstate_pct", 0.0))
        return (reinstate_val * (pct / 100.0)) / 12.0

# -----------------------------
# Validation
# -----------------------------
def validate_inputs(prison_choice, region, customer_type, customer_name,
                    workshop_mode, workshop_size, area_ft2,
                    workshop_hours, num_prisoners, prisoner_salary,
                    num_supervisors, supervisor_salaries,
                    customer_covers_supervisors):
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
# Overheads
# -----------------------------
def weekly_overheads_total(area_m2, workshop_hours, USAGE_KEY):
    elec_m, gas_m = monthly_energy_costs(area_m2, workshop_hours, USAGE_KEY)
    water_m = (num_prisoners + (0 if customer_covers_supervisors else num_supervisors)) \
              * config.TARIFF_BANDS[USAGE_KEY]["intensity_per_year"]["water_m3_per_employee"] / 12.0 \
              * float(st.session_state.get("water_rate", config.TARIFF_BANDS[USAGE_KEY]["rates"]["water_unit"]))
    admin_m = float(st.session_state.get("admin_monthly", 150.0))
    maint_m = monthly_maintenance_cost(area_m2, workshop_hours, USAGE_KEY)

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
# Host branch
# -----------------------------
if workshop_mode == "Host":
    if st.button("Generate Costs"):
        supervisor_salaries = []  # placeholder, can be filled from UI
        errors = validate_inputs(prison_choice, region, customer_type, customer_name,
                                 workshop_mode, workshop_size, area_ft2,
                                 0, 0, 0, 0, supervisor_salaries, True)
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            st.subheader(f"Host Contract for {customer_name} (per month)")
            breakdown = {}
            breakdown["Administration"] = float(st.session_state.get("admin_monthly", 150.0))
            breakdown["Depreciation/Maintenance (estimated)"] = monthly_maintenance_cost(area_m2, 0, USAGE_KEY)
            elec_m, gas_m = monthly_energy_costs(area_m2, 0, USAGE_KEY)
            breakdown["Electricity (estimated)"] = elec_m
            breakdown["Gas (estimated)"] = gas_m
            breakdown["Water (estimated)"] = 0.0

            subtotal = sum(breakdown.values())
            vat_amount = (subtotal * (20.0 / 100.0)) if (customer_type == "Commercial" and True) else 0.0
            grand_total = subtotal + vat_amount

            rows = list(breakdown.items()) + [
                ("Subtotal", subtotal),
                (f"VAT (20%)" if (customer_type == "Commercial") else "VAT (0%)", vat_amount),
                ("Grand Total (£/month)", grand_total),
            ]
            host_df = pd.DataFrame(rows, columns=["Item", "Amount (£)"])
            st.markdown(_render_host_df_to_html(host_df), unsafe_allow_html=True)
            st.download_button("Download CSV (Host)", data=export_csv_bytes(host_df),
                               file_name="host_quote.csv", mime="text/csv")

# -----------------------------
# Production branch (simplified)
# -----------------------------
elif workshop_mode == "Production":
    st.subheader("Production Settings")
    st.write("Production logic goes here – contractual or ad-hoc, using overheads and instructor apportionment.")
    # For brevity, detailed production logic can be copied from original file and updated
    # to use monthly_energy_costs(), monthly_maintenance_cost(), weekly_overheads_total()

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
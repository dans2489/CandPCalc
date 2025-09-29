# newapp.py
# UI shell: original aesthetics, short, robust.
# - Sidebar moved to sidebar.py
# - Dev charge applied to Host & Production (same question; can be 0%)
# - Unit prices include salaries + overheads + dev charge (apportioned by labour minutes)
# - Output slider changes BOTH planned available and planned used minutes (hard limit enforced)
# - Per-item assignment with hard constraints; Ad-hoc feasibility check by earliest deadline

from io import BytesIO
from datetime import date
import pandas as pd
import streamlit as st

from config import CFG
from style import inject_govuk_css
from tariff import PRISON_TO_REGION, SUPERVISOR_PAY, TARIFF_BANDS
from sidebar import draw_sidebar
from production import (
    labour_minutes_budget,
    calculate_production_contractual,
    calculate_adhoc,
)
from host import generate_host_quote


# ----------------------------
# Page config & minimal styling
# ----------------------------
st.set_page_config(page_title="Cost and Price Calculator", page_icon="💷", layout="centered")
inject_govuk_css()
st.markdown("## Cost and Price Calculator")


# ----------------------------
# Utilities (render/export)
# ----------------------------
def _currency(v) -> str:
    try:
        return f"£{float(v):,.2f}"
    except Exception:
        return ""

def render_host_df_to_html(host_df: pd.DataFrame) -> str:
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
    header = "<tr><th>Item</th><th>Amount (£)</th></tr>"
    return f"<table>{header}{''.join(rows_html)}</table>"

def render_generic_df_to_html(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    thead = "<tr>" + "".join([f"<th>{c}</th>" for c in cols]) + "</tr>"
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
    return f"<table>{thead}{''.join(body_rows)}</table>"

def export_csv_bytes(df: pd.DataFrame) -> BytesIO:
    b = BytesIO()
    df.to_csv(b, index=False)
    b.seek(0)
    return b

def export_html(host_df: pd.DataFrame | None, prod_df: pd.DataFrame | None, title="Quote") -> BytesIO:
    css = """
    <style>
      body{font-family:Arial,Helvetica,sans-serif;color:#0b0c0c;}
      table{width:100%;border-collapse:collapse;margin:12px 0;}
      th,td{border-bottom:1px solid #b1b4b6;padding:8px;text-align:left;}
      th{background:#f3f2f1;}
      td.neg{color:#d4351c;}
      tr.grand td{font-weight:700;}
      h1,h2,h3{margin:0.2rem 0;}
    </style>
    """
    meta = (
        f"<p>Date: {date.today().isoformat()}<br/>"
        f"Customer: {st.session_state.get('customer_name','')}<br/>"
        f"Prison: {st.session_state.get('prison_choice','')}<br/>"
        f"Region: {st.session_state.get('region','')}</p>"
    )
    parts = [css, f"<h2>{title}</h2>", meta]
    if host_df is not None:
        parts += ["<h3>Host Costs</h3>", render_host_df_to_html(host_df)]
    if prod_df is not None:
        section_title = "Ad‑hoc Items" if "Ad‑hoc" in str(title) else "Production Items"
        parts += [f"<h3>{section_title}</h3>", render_generic_df_to_html(prod_df)]
    parts.append("<p>Prices are indicative and may change based on final scope and site conditions.</p>")
    b = BytesIO("".join(parts).encode("utf-8"))
    b.seek(0)
    return b


# ----------------------------
# Base inputs (main area)
# ----------------------------
prisons_sorted = ["Select"] + sorted(PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0, key="prison_choice")
region = PRISON_TO_REGION.get(prison_choice, "Select") if prison_choice != "Select" else "Select"
st.session_state["region"] = region

customer_type = st.selectbox("I want to quote for", ["Select", "Commercial", "Another Government Department"], key="customer_type")
customer_name = st.text_input("Customer Name", key="customer_name")
workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"], key="workshop_mode")

# Workshop size
SIZE_LABELS = ["Select", "Small (500 ft²)", "Medium (2,500 ft²)", "Large (5,000 ft²)", "Enter dimensions in ft"]
SIZE_MAP = {"Small (500 ft²)": 500, "Medium (2,500 ft²)": 2500, "Large (5,000 ft²)": 5000}
workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS, key="workshop_size")
if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area_ft2 = (width or 0.0) * (length or 0.0)
else:
    area_ft2 = SIZE_MAP.get(workshop_size, 0)
area_m2 = area_ft2 * CFG.FT2_TO_M2 if area_ft2 else 0.0
if area_ft2:
    st.markdown(f"Calculated area: **{area_ft2:,.0f} ft²** · **{area_m2:,.0f} m²**")

# Usage band
workshop_usage = st.radio(
    "Workshop usage tariff",
    ["Low usage", "Medium usage", "High usage"],
    horizontal=True, key="workshop_usage",
)
USAGE_KEY = ("low" if "Low" in workshop_usage else "medium" if "Medium" in workshop_usage else "high")
st.caption(
    "**What these mean:** "
    "**Low** – heated & lit, light plug/process loads. "
    "**Medium** – mixed light industrial. "
    "**High** – machinery‑heavy or continuous processes."
)

# ----------------------------
# Sidebar — Tariffs & Overheads (moved to sidebar.py)
# ----------------------------
draw_sidebar(USAGE_KEY)

# ----------------------------
# Hours / staffing & instructors
# ----------------------------
workshop_hours = st.number_input(
    "How many hours per week is the workshop open?",
    min_value=0.0, format="%.2f",
    help="Affects production capacity and apportionment.",
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

contracts = st.number_input("How many contracts do these instructors oversee?", min_value=1, value=1, key="contracts")
recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if contracts and workshop_hours >= 0 else 0
st.subheader("Instructor Time Allocation")
st.info(f"Recommended: {recommended_pct}%")
chosen_pct = st.slider("Adjust instructor % allocation", 0, 100, int(recommended_pct), key="chosen_pct")
if chosen_pct < int(round(recommended_pct)):
    st.warning("You have selected less than recommended — please explain why here.")
    reason = st.text_area("Reason for using a lower allocation", key="alloc_reason")
    action = st.radio("Apply allocation", ["Keep recommended", "Set new"], index=0, horizontal=True, key="alloc_action")
    if action == "Set new" and not str(reason).strip():
        st.error("Please provide a brief explanation before setting a lower allocation.")
        effective_pct = int(round(recommended_pct))
    else:
        effective_pct = int(chosen_pct) if action == "Set new" else int(round(recommended_pct))
else:
    effective_pct = int(round(recommended_pct))

# ----------------------------
# Employment support -> Development charge (Host & Production)
# ----------------------------
dev_rate = 0.0
if customer_type == "Commercial":
    support = st.selectbox(
        "Customer employment support?",
        ["None", "Employment on release/RoTL", "Post release", "Both"],
        help="Affects development charge (on overheads). 'Both' reduces dev charge to 0%."
    )
    if support == "None":
        dev_rate = 0.20
    elif support in ("Employment on release/RoTL", "Post release"):
        dev_rate = 0.10
    else:  # "Both"
        dev_rate = 0.00

# ----------------------------
# Pricing (Commercial): VAT only
# ----------------------------
st.markdown("---")
st.subheader("Pricing (Commercial)")
colp1, colp2 = st.columns([1, 1])
with colp1:
    apply_vat = st.checkbox("Apply VAT?", key="apply_vat")
with colp2:
    vat_rate = st.number_input("VAT rate %", min_value=0.0, max_value=100.0, value=20.0, step=0.5, format="%.1f", key="vat_rate")

# ----------------------------
# Validation
# ----------------------------
def validate_inputs():
    errors = []
    if prison_choice == "Select": errors.append("Select prison")
    if region == "Select": errors.append("Region could not be derived from prison selection")
    if customer_type == "Select": errors.append("Select customer type")
    if not str(customer_name).strip(): errors.append("Enter customer name")
    if workshop_mode == "Select": errors.append("Select contract type")
    if workshop_size == "Select": errors.append("Select workshop size")
    if area_ft2 <= 0: errors.append("Area must be greater than zero")
    if workshop_mode == "Production" and workshop_hours <= 0: errors.append("Hours per week must be > 0 (Production)")
    if num_prisoners < 0: errors.append("Prisoners employed cannot be negative")
    if prisoner_salary < 0: errors.append("Prisoner salary per week cannot be negative")
    if not customer_covers_supervisors:
        if num_supervisors <= 0: errors.append("Enter number of instructors (>0) or tick 'Customer provides instructor(s)'")
        if region == "Select": errors.append("Select a prison/region to populate instructor titles")
        if len(supervisor_salaries) != int(num_supervisors): errors.append("Choose a title for each instructor")
        if any(s <= 0 for s in supervisor_salaries): errors.append("Instructor Avg Total must be > 0")
    return errors


# ----------------------------
# HOST branch
# ----------------------------
def run_host():
    errors_top = validate_inputs()
    if st.button("Generate Costs"):
        if errors_top:
            st.error("Fix errors:\n- " + "\n- ".join(errors_top))
            return
        host_df, _ctx = generate_host_quote(
            workshop_hours=float(workshop_hours),
            area_m2=float(area_m2),
            usage_key=USAGE_KEY,
            num_prisoners=int(num_prisoners),
            prisoner_salary=float(prisoner_salary),
            num_supervisors=int(num_supervisors),
            customer_covers_supervisors=bool(customer_covers_supervisors),
            supervisor_salaries=supervisor_salaries,
            effective_pct=float(effective_pct),
            customer_type=customer_type,
            apply_vat=bool(apply_vat),
            vat_rate=float(vat_rate),
            dev_rate=float(dev_rate),
        )
        st.markdown(render_host_df_to_html(host_df), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download CSV (Host)", data=export_csv_bytes(host_df),
                               file_name="host_quote.csv", mime="text/csv")
        with c2:
            st.download_button("Download PDF-ready HTML (Host)", data=export_html(host_df, None, title="Host Quote"),
                               file_name="host_quote.html", mime="text/html")


# ----------------------------
# PRODUCTION branch
# ----------------------------
def run_production():
    errors_top = validate_inputs()
    if errors_top:
        st.error("Fix errors before production:\n- " + "\n- ".join(errors_top))
        return

    st.markdown("---")
    st.subheader("Production settings")

    # Output slider scales BOTH planned available and planned used minutes (clear constraint)
    planned_output_pct = st.slider(
        "Planned Output (%)", min_value=0, max_value=100, value=CFG.GLOBAL_OUTPUT_DEFAULT,
        help="Scales both planned available and planned used labour minutes."
    )

    prod_type = st.radio(
        "Do you want ad‑hoc costs with a deadline, or contractual work?",
        ["Contractual work", "Ad‑hoc costs (multiple lines) with deadlines"],
        index=0, key="prod_type"
    )

    if prod_type == "Contractual work":
        run_production_contractual(planned_output_pct)
    else:
        run_production_adhoc(planned_output_pct)


def run_production_contractual(planned_output_pct: int):
    # Planned available minutes respond to Output%
    budget_minutes_raw = labour_minutes_budget(int(num_prisoners), float(workshop_hours))
    output_scale = float(planned_output_pct) / 100.0
    budget_minutes_planned = budget_minutes_raw * output_scale
    st.markdown(f"**Planned available Labour minutes @ {planned_output_pct}%:** {budget_minutes_planned:,.0f}")

    # Number of items
    num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")

    items = []
    # Enforce sum(assigned) ≤ total prisoners live via remainder
    for i in range(int(num_items)):
        with st.expander(f"Item {i+1} details", expanded=(i == 0)):
            name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
            disp = (name.strip() or f"Item {i+1}") if isinstance(name, str) else f"Item {i+1}"

            required = st.number_input(
                f"Prisoners required to make 1 item ({disp})",
                min_value=1, value=1, step=1, key=f"req_{i}"
            )
            minutes_per = st.number_input(
                f"How many minutes to make 1 item ({disp})",
                min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}"
            )

            # running remainder based on previously entered assignments
            total_assigned_before = sum(int(st.session_state.get(f"assigned_{j}", 0)) for j in range(i))
            remaining = max(0, int(num_prisoners) - total_assigned_before)
            assigned = st.number_input(
                f"How many prisoners work solely on this item ({disp})",
                min_value=0, max_value=remaining, value=int(st.session_state.get(f"assigned_{i}", 0)),
                step=1, key=f"assigned_{i}"
            )

            # Preview @100%
            if assigned > 0 and minutes_per > 0 and required > 0 and workshop_hours > 0:
                cap_100 = (assigned * workshop_hours * 60.0) / (minutes_per * required)
            else:
                cap_100 = 0.0
            st.markdown(f"{disp} capacity @ 100%: **{cap_100:.0f} units/week**")

            items.append({"name": name, "required": int(required), "minutes": float(minutes_per), "assigned": int(assigned)})

    # Hard 1: total assigned ≤ total prisoners
    total_assigned = sum(it["assigned"] for it in items)
    if total_assigned > int(num_prisoners):
        st.error(f"Prisoners assigned across items ({total_assigned}) exceed total prisoners ({int(num_prisoners)}).")
        return

    # Planned used minutes respond to Output%
    used_minutes_raw = total_assigned * workshop_hours * 60.0
    used_minutes_planned = used_minutes_raw * output_scale
    st.markdown(f"**Planned used Labour minutes @ {planned_output_pct}%:** {used_minutes_planned:,.0f}")

    # Hard 2: planned used ≤ planned available
    if used_minutes_planned > budget_minutes_planned:
        st.error("Planned used minutes exceed planned available minutes. Adjust assignments, add prisoners, increase hours, or lower Output%.")
        return

    # Results (unit prices include prisoner wages + instructors + overheads + development)
    results = calculate_production_contractual(
        items, planned_output_pct,
        workshop_hours=float(workshop_hours),
        prisoner_salary=float(prisoner_salary),
        supervisor_salaries=supervisor_salaries,
        effective_pct=float(effective_pct),
        customer_covers_supervisors=bool(customer_covers_supervisors),
        customer_type=customer_type,
        apply_vat=bool(apply_vat),
        vat_rate=float(vat_rate),
        area_m2=float(area_m2),
        usage_key=USAGE_KEY,
        num_prisoners=int(num_prisoners),
        num_supervisors=int(num_supervisors),
        dev_rate=float(dev_rate),
    )

    # Defensive: units within planned minutes (tolerate rounding)
    units_minutes = 0.0
    for r, it in zip(results, items):
        units = r.get("Units/week", 0) or 0
        units_minutes += float(units) * float(it["minutes"]) * float(it["required"])
    if units_minutes > used_minutes_planned + 1e-6:
        st.error("Total minutes implied by units exceed planned labour minutes. Re-check Output% and timings.")
        return

    prod_df = pd.DataFrame([{
        k: (None if r[k] is None else (round(float(r[k]), 2) if isinstance(r[k], (int, float)) else r[k]))
        for k in ["Item", "Output %", "Units/week", "Unit Cost (£)", "Unit Price ex VAT (£)", "Unit Price inc VAT (£)"]
    } for r in results])
    st.markdown(render_generic_df_to_html(prod_df), unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button("Download CSV (Production)", data=export_csv_bytes(prod_df),
                           file_name="production_quote.csv", mime="text/csv")
    with d2:
        st.download_button("Download PDF-ready HTML (Production)", data=export_html(None, prod_df, title="Production Quote"),
                           file_name="production_quote.html", mime="text/html")


def run_production_adhoc(planned_output_pct: int):
    num_lines = st.number_input("How many product lines are needed?", min_value=1, value=1, step=1, key="adhoc_num_lines")
    lines = []
    for i in range(int(num_lines)):
        with st.expander(f"Product line {i+1}", expanded=(i == 0)):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item_name = st.text_input("Item name", key=f"adhoc_name_{i}")
            with c2: units_requested = st.number_input("Units requested", min_value=1, value=100, step=1, key=f"adhoc_units_{i}")
            with c3: deadline = st.date_input("Deadline", value=date.today(), key=f"adhoc_deadline_{i}")
            c4, c5 = st.columns([1, 1])
            with c4: pris_per_item = st.number_input("Prisoners to make one", min_value=1, value=1, step=1, key=f"adhoc_pris_req_{i}")
            with c5: minutes_per_item = st.number_input("Minutes to make one", min_value=1.0, value=10.0, format="%.2f", key=f"adhoc_mins_{i}")
            lines.append({
                "name": (item_name.strip() or f"Item {i+1}") if isinstance(item_name, str) else f"Item {i+1}",
                "units": int(units_requested),
                "deadline": deadline,
                "pris_per_item": int(pris_per_item),
                "mins_per_item": float(minutes_per_item),
            })

    if st.button("Calculate Ad‑hoc Cost", key="calc_adhoc"):
        errs = validate_inputs()
        if workshop_hours <= 0: errs.append("Hours per week must be > 0 for Ad‑hoc")
        for i, ln in enumerate(lines):
            if ln["units"] <= 0: errs.append(f"Line {i+1}: Units requested must be > 0")
            if ln["pris_per_item"] <= 0: errs.append(f"Line {i+1}: Prisoners to make one must be > 0")
            if ln["mins_per_item"] <= 0: errs.append(f"Line {i+1}: Minutes to make one must be > 0")
        if errs:
            st.error("Fix errors:\n- " + "\n- ".join(errs))
            return

        result = calculate_adhoc(
            lines, planned_output_pct,
            workshop_hours=float(workshop_hours),
            num_prisoners=int(num_prisoners),
            prisoner_salary=float(prisoner_salary),
            supervisor_salaries=supervisor_salaries,
            effective_pct=float(effective_pct),
            customer_covers_supervisors=bool(customer_covers_supervisors),
            customer_type=customer_type,
            apply_vat=bool(apply_vat),
            vat_rate=float(vat_rate),
            area_m2=float(area_m2),
            usage_key=USAGE_KEY,
            dev_rate=float(dev_rate),
            today=date.today(),
        )

        if result["feasibility"]["hard_block"]:
            st.error(result["feasibility"]["reason"])
            return

        show_inc = (customer_type == "Commercial" and apply_vat)
        col_headers = [
            "Item", "Units",
            f"Unit Cost (£{' inc VAT' if show_inc else ''})",
            f"Line Total (£{' inc VAT' if show_inc else ''})"
        ]
        data_rows = []
        for p in result["per_line"]:
            data_rows.append([
                p["name"], f"{p['units']:,}",
                f"{(p['unit_cost_inc_vat'] if show_inc else p['unit_cost_ex_vat']):.2f}",
                f"{(p['line_total_inc_vat'] if show_inc else p['line_total_ex_vat']):.2f}",
            ])
        table_html = ["<table><tr>"] + [f"<th>{h}</th>" for h in col_headers] + ["</tr>"]
        for r in data_rows:
            table_html.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
        table_html.append("</table>")
        st.markdown("".join(table_html), unsafe_allow_html=True)

        totals = result["totals"]
        if show_inc:
            st.markdown(f"**Total Job Cost (inc VAT): £{totals['inc_vat']:,.2f}**")
            st.caption(f"Total Job Cost (ex VAT): £{totals['ex_vat']:,.2f}")
        else:
            st.markdown(f"**Total Job Cost: £{totals['ex_vat']:,.2f}**")

        feas = result["feasibility"]
        st.success(
            f"Based on the data entered, the products will be ready in **{feas['wd_needed_all']} working day(s)** "
            f"(earliest deadline in **{feas['earliest_wd_available']} working day(s)**)."
        )


# ----------------------------
# MAIN BRANCHING
# ----------------------------
if workshop_mode == "Host":
    run_host()
elif workshop_mode == "Production":
    run_production()

# ----------------------------
# Footer: Reset
# ----------------------------
st.markdown('\n', unsafe_allow_html=True)
if st.button("Reset Selections", key="reset_app_footer"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
st.markdown('\n', unsafe_allow_html=True)

# App.py - Prison Workshop costing (Activity-based + 61% overhead)
import streamlit as st

# ---------- Page style ----------
st.set_page_config(page_title="Prison Workshop Cost (Host / Production)", layout="centered")
st.markdown("""
<style>
body {background-color: #f7f7f7; color: #222;}
.header {background: #1d70b8; color: white; padding: 12px 14px; border-radius: 6px; margin-bottom:8px;}
.govbox {background:white; border:1px solid #dfe3e8; padding:14px; border-radius:6px; margin-bottom:12px;}
.small {font-size:0.9em; color:#444;}
.kv {font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h2>Prison Workshop Cost Model</h2></div>', unsafe_allow_html=True)
st.markdown('<div class="govbox small">Select Host (show monthly cost breakdown) or Production (collect items & calculate per-unit prices).</div>', unsafe_allow_html=True)

# ---------- Inputs ----------
with st.form("main_form"):
    st.markdown("### Basic details")
    region = st.selectbox("Region?", ["National", "Inner London", "Outer London"])
    quote_for = st.selectbox("Quote for a?", ["Commercial", "Another Government Department"])
    workshop_size = st.selectbox("Workshop size?", ["Small", "Medium", "Large", "Enter dimensions"])
    width = length = None
    if workshop_size == "Enter dimensions":
        width = st.number_input("Width (m)", min_value=1.0, value=10.0, format="%.2f")
        length = st.number_input("Length (m)", min_value=1.0, value=20.0, format="%.2f")
    workshop_type = st.selectbox("Workshop type?",
                                 ["Woodwork", "Metalwork", "Warehousing", "Packing/Assembly", "Textiles", "Empty space (no machinery)", "Other"])
    customer = st.text_input("Customer? (free text)")
    hours_per_week = st.number_input("How many hours per week is it open?", min_value=1, max_value=168, value=27)
    num_prisoners = st.number_input("How many prisoners employed?", min_value=0, value=11)
    prisoner_wage = st.number_input("Prisoners salary per week? (average with bonuses) £", min_value=0.0, value=18.0, format="%.2f")
    num_supervisors = st.number_input("How many supervisors?", min_value=0, value=1)
    st.markdown("### Supervisors salaries (annual total per person, incl on-costs)")
    supervisors_salaries = []
    for i in range(int(num_supervisors)):
        s = st.number_input(f"Supervisor {i+1} salary (£/year)", min_value=0.0, value=42000.0, format="%.2f", key=f"sup{i}")
        supervisors_salaries.append(s)
    num_contracts = st.number_input("How many contracts do these supervise in this workshop?", min_value=1, value=1)

    # Employment support only for Commercial quotes; for Government Dept it's assumed 'Both'
    if quote_for == "Commercial":
        support = st.selectbox("What employment support does this customer offer?",
                               ["None", "Employment on release and/or RoTL", "Post release support", "Both"])
    else:
        support = "Both"

    contract_type = st.selectbox("Contract type?", ["Host", "Production"])
    submitted = st.form_submit_button("Continue")

if not submitted:
    st.stop()

# ---------- Constants & baseline estimates ----------
base_fte_hours = 37.5
weeks_per_year = 48

# Region overhead multiplier (affects utilities/maintenance baseline)
region_overhead_multiplier = {"National": 1.0, "Inner London": 1.25, "Outer London": 1.1}
area_sq_m = None
if workshop_size == "Small":
    area_sq_m = 200.0
elif workshop_size == "Medium":
    area_sq_m = 600.0
elif workshop_size == "Large":
    area_sq_m = 1500.0
else:
    area_sq_m = (width * length) if width and length else 200.0

# Baseline utilities & maintenance (annual if full-time) per workshop type
base_util = {
    "Woodwork": 5000.0, "Metalwork": 7000.0, "Warehousing": 3000.0,
    "Packing/Assembly": 2500.0, "Textiles": 2000.0,
    "Empty space (no machinery)": 1000.0, "Other": 2000.0
}
util_maint_full = base_util.get(workshop_type, 2000.0)
# Scale by area (baseline per ~200m2) and region
util_maint_full = util_maint_full * max(0.5, area_sq_m / 200.0) * region_overhead_multiplier.get(region, 1.0)

total_supervisor_salary = sum(supervisors_salaries)
total_prisoner_hours_per_year = num_prisoners * hours_per_week * weeks_per_year if num_prisoners > 0 else 0.0

# development charge rules (applies differently per model; we'll implement accordingly)
if quote_for == "Another Government Department":
    development_charge = 0.0
else:
    if support == "None":
        development_charge = 0.20
    elif support == "Both":
        development_charge = 0.0
    else:
        development_charge = 0.10

# ---------- Supervisor allocation recommendation ----------
recommended_pct = (hours_per_week / base_fte_hours) / num_contracts if num_contracts > 0 else 1.0
recommended_pct = min(1.0, recommended_pct)
st.markdown("### Supervisor allocation recommendation")
col1, col2 = st.columns([2, 3])
with col1:
    st.write(f"Based on {hours_per_week} hrs/week and {num_contracts} contract(s) the recommended allocation of supervisors' salary to this contract is **{recommended_pct*100:.1f}%**")
with col2:
    slider_pct = st.slider("Adjust % allocation (use if supervisors split time across contracts)", min_value=0, max_value=100, value=int(round(recommended_pct*100)))
    applied_pct = slider_pct / 100.0

# ---------- Activity-based calculations ----------
# Supervisor allocated annual = total supervisor salary * applied_pct
supervisor_allocated_annual = total_supervisor_salary * applied_pct

# For activity-based: development charge adds to overheads
overheads_with_development = util_maint_full * (1.0 + development_charge)

# prisoner hourly based on actual hours/week
prisoner_hourly = (prisoner_wage / hours_per_week) if hours_per_week > 0 else 0.0

# guard against division by zero
if total_prisoner_hours_per_year > 0:
    overhead_per_prisoner_hour = overheads_with_development / total_prisoner_hours_per_year
    supervisor_alloc_per_prisoner_hour = supervisor_allocated_annual / total_prisoner_hours_per_year
else:
    overhead_per_prisoner_hour = 0.0
    supervisor_alloc_per_prisoner_hour = 0.0

activity_cost_per_prisoner_hour = supervisor_alloc_per_prisoner_hour + prisoner_hourly + overhead_per_prisoner_hour

# Annual totals (activity)
prisoner_pay_annual = prisoner_wage * num_prisoners * weeks_per_year
activity_total_annual = supervisor_allocated_annual + prisoner_pay_annual + overheads_with_development
activity_total_monthly = activity_total_annual / 12.0

# ---------- 61% Full FTE model calculations ----------
# For 61% method development charge is added to supervisor salary (per your rule)
supervisor_salary_with_dev = total_supervisor_salary * (1.0 + development_charge)
overhead_pct = 0.61
total_annual_61 = supervisor_salary_with_dev * (1.0 + overhead_pct)

if total_prisoner_hours_per_year > 0:
    cost_per_prisoner_hour_61 = total_annual_61 / total_prisoner_hours_per_year
else:
    cost_per_prisoner_hour_61 = 0.0

# Breakdowns monthly for display
activity_breakdown = {
    "Supervisor allocated (annual)": supervisor_allocated_annual,
    "Prisoner pay (annual)": prisoner_pay_annual,
    "Overheads incl. development (annual)": overheads_with_development,
    "Total (annual)": activity_total_annual,
    "Monthly total": activity_total_monthly,
    "Supervisor alloc per prisoner-hour": supervisor_alloc_per_prisoner_hour,
    "Prisoner wage per hour": prisoner_hourly,
    "Overhead per prisoner-hour": overhead_per_prisoner_hour,
    "Total cost per prisoner-hour": activity_cost_per_prisoner_hour
}

model61_breakdown = {
    "Supervisor salary (with development if any) (annual)": supervisor_salary_with_dev,
    "61% overhead on supervisor (annual)": supervisor_salary_with_dev * overhead_pct,
    "Total (annual)": total_annual_61,
    "Monthly total": total_annual_61 / 12.0,
    "Cost per prisoner-hour": cost_per_prisoner_hour_61
}

# ---------- Output behaviour ----------
st.markdown("---")
if contract_type == "Host":
    st.header("Host contract — Monthly cost breakdown")
    st.markdown("Below are **itemised annual & monthly** figures and important rates for both models.")

    st.subheader("Activity-based model (detailed)")
    st.write(f"**Annual** and **Monthly** values (rounded to 2 dp):")
    # show each line with annual and monthly
    rows = []
    rows.append(("Supervisor allocated (annual)", f"£{activity_breakdown['Supervisor allocated (annual)']:.2f}", f"£{(activity_breakdown['Supervisor allocated (annual)']/12):.2f}"))
    rows.append(("Prisoner pay (annual)", f"£{activity_breakdown['Prisoner pay (annual)']:.2f}", f"£{(activity_breakdown['Prisoner pay (annual)']/12):.2f}"))
    rows.append(("Overheads incl. development (annual)", f"£{activity_breakdown['Overheads incl. development (annual)']:.2f}", f"£{(activity_breakdown['Overheads incl. development (annual)']/12):.2f}"))
    rows.append(("Total (annual)", f"£{activity_breakdown['Total (annual)']:.2f}", f"£{activity_breakdown['Monthly total']:.2f}"))
    st.table([{"Line":r[0], "Annual":r[1], "Monthly":r[2]} for r in rows])

    st.markdown("**Rates (per prisoner-hour)**")
    st.write(f"- Supervisor allocation per prisoner-hour: £{activity_breakdown['Supervisor alloc per prisoner-hour']:.4f}/hr")
    st.write(f"- Prisoner wage per hour: £{activity_breakdown['Prisoner wage per hour']:.4f}/hr")
    st.write(f"- Overhead per prisoner-hour: £{activity_breakdown['Overhead per prisoner-hour']:.4f}/hr")
    st.write(f"**Total cost per prisoner-hour:** £{activity_breakdown['Total cost per prisoner-hour']:.4f}/hr")

    st.markdown("---")
    st.subheader("Full FTE + 61% overhead model (summary)")
    rows61 = []
    rows61.append(("Supervisor salary (with dev if any) (annual)", f"£{model61_breakdown['Supervisor salary (with development if any) (annual)']:.2f}", f"£{(model61_breakdown['Supervisor salary (with development if any) (annual)']/12):.2f}"))
    rows61.append(("61% overhead on supervisor (annual)", f"£{model61_breakdown['61% overhead on supervisor (annual)']:.2f}", f"£{(model61_breakdown['61% overhead on supervisor (annual)']/12):.2f}"))
    rows61.append(("Total (annual)", f"£{model61_breakdown['Total (annual)']:.2f}", f"£{model61_breakdown['Monthly total']:.2f}"))
    st.table([{"Line":r[0], "Annual":r[1], "Monthly":r[2]} for r in rows61])

    st.markdown("**Rate**")
    st.write(f"- Cost per prisoner-hour (61% method): £{model61_breakdown['Cost per prisoner-hour']:.4f}/hr")

    st.markdown("---")
    st.write("You can adjust the Supervisor allocation slider above and re-run to see how activity-based numbers change.")

else:
    # Production workflow
    st.header("Production contract — enter item details")
    st.markdown("Fill the item list below and press **Calculate** to show per-unit prices for both models.")
    num_items = st.number_input("How many different items are produced? (enter count)", min_value=1, value=1)
    items = []
    # Use a child form to require pressing calculate
    with st.form("production_items"):
        for i in range(int(num_items)):
            st.markdown(f"**Item {i+1}**")
            item_name = st.text_input(f"Item name {i+1}", value=f"Item_{i+1}", key=f"iname{i}")
            prisoners_per_unit = st.number_input(f"How many prisoners to make 1 unit? (Item {i+1})", min_value=1, value=1, key=f"ip{i}")
            minutes_per_unit = st.number_input(f"How long to make 1 unit (minutes) (Item {i+1})", min_value=0.1, value=1.0, format="%.2f", key=f"im{i}")
            items.append((item_name, prisoners_per_unit, minutes_per_unit))
        calc = st.form_submit_button("Calculate per-unit prices")

    if calc:
        st.subheader("Per-unit prices (both models)")
        table = []
        for idx, (name, ppunit, mins) in enumerate(items, start=1):
            hours = mins / 60.0
            labour_hours = hours * ppunit  # sum prisoner-hours required for one unit

            # activity-based unit cost
            activity_unit_cost = activity_cost_per_prisoner_hour * labour_hours

            # 61% model unit cost
            unit_cost_61 = cost_per_prisoner_hour_61 * labour_hours

            # format
            table.append({
                "Item": name,
                "Time (min)": f"{mins:.2f}",
                "Prisoners/unit": f"{ppunit}",
                "Activity-based (£ per unit)": f"£{activity_unit_cost:.4f} ({activity_unit_cost*100:.1f}p)",
                "61% model (£ per unit)": f"£{unit_cost_61:.4f} ({unit_cost_61*100:.1f}p)"
            })
        st.table(table)
    else:
        st.info("Enter the items above and press **Calculate per-unit prices** to see results.")

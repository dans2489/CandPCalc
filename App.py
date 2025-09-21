import streamlit as st
from math import isclose

st.set_page_config(page_title="Prison Workshop Cost - Activity-Based", layout="centered")

# Basic government-style CSS
st.markdown("""
<style>
body {background-color: #f7f7f7; color: #222222;}
.header {background: #1d70b8; color: white; padding: 12px 16px; border-radius: 6px;}
.govbox {background: white; border: 1px solid #dfe3e8; padding: 18px; border-radius: 6px; margin-bottom: 12px;}
.label {font-weight:600; color:#0b0c0c;}
.small {font-size:0.9em; color:#444;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h2>Prison Workshop Cost Model — Activity-Based</h2></div>', unsafe_allow_html=True)
st.markdown('<div class="govbox">This form calculates activity-based costs for a prison workshop. Fill in the fields below.</div>', unsafe_allow_html=True)

# Inputs
with st.form("inputs"):
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
    supervisors_salaries = []
    st.markdown("### Supervisors salaries (per person)")
    for i in range(int(num_supervisors)):
        s = st.number_input(f"Supervisor {i+1} salary (total annual, £)", min_value=0.0, value=42000.0, format="%.2f", key=f"sup{i}")
        supervisors_salaries.append(s)
    num_contracts = st.number_input("How many contracts do these supervise in this workshop?", min_value=1, value=1)
    support = None
    if quote_for == "Commercial":
        support = st.selectbox("What employment support does this customer offer?",
                               ["None", "Employment on release and/or RoTL", "Post release support", "Both"])
    contract_type = st.selectbox("Contract type?", ["Host", "Production"])
    development_charge = 0.0
    if quote_for == "Another Government Department":
        support = "Both"  # no dev charge
    if support == "None":
        development_charge = 0.20
    elif support == "Both":
        development_charge = 0.0
    else:
        development_charge = 0.10
    submitted = st.form_submit_button("Calculate activity-based costs")

if submitted:
    region_overhead_multiplier = {"National": 1.0, "Inner London": 1.25, "Outer London": 1.1}
    if workshop_size == "Small":
        area_sq_m = 200.0
    elif workshop_size == "Medium":
        area_sq_m = 600.0
    elif workshop_size == "Large":
        area_sq_m = 1500.0
    else:
        area_sq_m = (width * length) if width and length else 200.0

    base_fte_hours = 37.5
    weeks_per_year = 48

    # Utilities baseline
    base_util = {
        "Woodwork": 5000.0, "Metalwork": 7000.0, "Warehousing": 3000.0,
        "Packing/Assembly": 2500.0, "Textiles": 2000.0,
        "Empty space (no machinery)": 1000.0, "Other": 2000.0
    }
    util_maint_full = base_util.get(workshop_type, 2000.0)
    util_maint_full = util_maint_full * max(0.5, area_sq_m / 200.0) * region_overhead_multiplier.get(region, 1.0)

    total_supervisor_salary = sum(supervisors_salaries)
    sup_hourly = total_supervisor_salary / base_fte_hours / 52.0
    total_prisoner_hours_per_year = num_prisoners * hours_per_week * weeks_per_year if num_prisoners>0 else 0.0
    recommended_pct = (hours_per_week / base_fte_hours) / num_contracts if num_contracts>0 else 1.0
    recommended_pct = min(1.0, recommended_pct)

    st.markdown("### Supervisor allocation")
    slider_pct = st.slider("Adjust percentage allocation (%)", min_value=0, max_value=100, value=int(round(recommended_pct*100)))
    applied_pct = slider_pct / 100.0

    supervisor_allocated_annual = total_supervisor_salary * applied_pct
    overheads_with_dev = util_maint_full * (1.0 + development_charge)
    overhead_per_hour = overheads_with_dev / total_prisoner_hours_per_year if total_prisoner_hours_per_year>0 else 0.0
    prisoner_hourly = prisoner_wage / hours_per_week if hours_per_week>0 else 0.0
    supervisor_alloc_per_hour = supervisor_allocated_annual / total_prisoner_hours_per_year if total_prisoner_hours_per_year>0 else 0.0
    total_cost_per_hour = supervisor_alloc_per_hour + prisoner_hourly + overhead_per_hour

    st.write("**Total cost per prisoner-hour:** £{:.4f}".format(total_cost_per_hour))

    if contract_type == "Production":
        st.markdown("### Production items")
        num_items = st.number_input("Number of items", min_value=1, value=1)
        for i in range(int(num_items)):
            name = st.text_input(f"Item {i+1} name", f"Item_{i+1}")
            ppunit = st.number_input(f"Prisoners per unit {i+1}", min_value=1, value=1, key=f"pp{i}")
            mins = st.number_input(f"Minutes per unit {i+1}", min_value=0.1, value=1.0, key=f"mins{i}")
            hours = mins/60.0
            labour_hours = hours * ppunit
            cost = total_cost_per_hour * labour_hours
            st.write(f"{name}: £{cost:.4f} ({cost*100:.1f}p)")

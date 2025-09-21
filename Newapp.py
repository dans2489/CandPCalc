import streamlit as st

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="Prison Workshop Costing Tool",
    layout="centered",
)

# ------------------------------
# CUSTOM CSS FOR GOV STYLE
# ------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #ffffff; color: #0b0c0c; }
    .stApp h1 { color: #005ea5; font-weight: bold; margin-bottom: 20px; }
    .stApp h2, .stApp h3 { color: #005ea5; margin-top: 15px; margin-bottom: 10px; }
    div.stButton > button:first-child { background-color: #10703c; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; margin-top: 10px; margin-bottom: 10px; }
    div.stTextInput > label, div.stNumberInput > label, div.stSelectbox > label, div.stRadio > label { font-weight: bold; margin-bottom: 5px; }
    .stSlider > div > div:nth-child(1) > div > div > div { color: #005ea5; }
    .stForm, .stContainer { box-shadow: 0 0 5px #e1e1e1; padding: 12px 15px; border-radius: 5px; margin-bottom: 15px; }
    table { width: 100%; border-collapse: collapse; }
    table th { background-color: #f3f2f1; text-align: left; padding: 8px; border-bottom: 2px solid #b1b4b6; }
    table td { padding: 8px; border-bottom: 1px solid #e1e1e1; }
    table tr.total-row { font-weight: bold; background-color: #e6f0fa; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# APP TITLE
# ------------------------------
st.title("Prison Workshop Costing Tool")

# ------------------------------
# WORKSHOP TYPE ENERGY CONSUMPTION (kWh/m²/year)
# ------------------------------
workshop_energy = {
    "Woodwork": 75,
    "Metalwork": 80,
    "Textiles": 120,
    "Warehousing": 33,
    "Packing": 50,
    "Empty space (no machinery)": 10,
}

# ------------------------------
# INPUTS
# ------------------------------
region = st.selectbox("Region?", ["Select", "National", "Inner London", "Outer London"], index=0)
customer_type = st.radio("Quote for a?", ["Select", "Commercial", "Another Government Department"], index=0)
customer_name = st.text_input("Customer?")
workshop_mode = st.radio("Contract type?", ["Select", "Host", "Production"], index=0)
workshop_size = st.selectbox("Workshop size?", ["Select", "Small", "Medium", "Large", "Enter dimensions"], index=0)

area = 0
if workshop_size == "Enter dimensions":
    width = st.number_input("Width (m)", min_value=0.0, format="%.2f", value=0.0)
    length = st.number_input("Length (m)", min_value=0.0, format="%.2f", value=0.0)
    if width > 0 and length > 0:
        area = width * length
else:
    area_map = {"Small": 100, "Medium": 250, "Large": 500}
    area = area_map.get(workshop_size, 0)

workshop_type = st.selectbox("Workshop type?", ["Select"] + list(workshop_energy.keys()), index=0)
workshop_hours = st.number_input("How many hours per week is it open?", min_value=0.0, format="%.2f", value=0.0)
num_prisoners = st.number_input("How many prisoners employed?", min_value=0, value=0)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f", value=0.0)
num_supervisors = st.number_input("How many supervisors?", min_value=0, value=0)

supervisor_salaries = []
for i in range(num_supervisors):
    sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, format="%.2f", value=0.0)
    supervisor_salaries.append(sup_salary)

contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=0, value=0)

# ------------------------------
# SUPERVISOR % CALCULATION
# ------------------------------
st.subheader("Supervisor Time Allocation")
st.markdown("**Recommended allocation based on hours and number of contracts:**")
recommended_pct = 0
if workshop_hours > 0 and contracts > 0:
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)
    st.info(f"{recommended_pct}% recommended supervisor allocation")
chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), step=1)
apply_pct = st.button("Set Supervisor %")
if apply_pct:
    if chosen_pct < recommended_pct:
        reason = st.text_area("Please explain why you are choosing a lower percentage:")
        if reason.strip() != "":
            st.success(f"Supervisor percentage set to {chosen_pct}% with explanation: {reason}")
        else:
            st.warning("Please provide a reason for choosing a lower percentage.")
    else:
        st.success(f"Supervisor percentage set to {chosen_pct}%")

# ------------------------------
# COST CALCULATIONS
# ------------------------------
def calculate_host_costs():
    breakdown = {}
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * 4.33
    supervisor_cost = sum((s / 12) * (chosen_pct / 100) for s in supervisor_salaries)
    breakdown["Supervisors"] = supervisor_cost
    # Energy cost based on workshop type
    energy_rate_per_kwh = 0.34  # £/kWh typical
    if workshop_type in workshop_energy:
        energy_cost = area * (workshop_energy[workshop_type] / 12) * energy_rate_per_kwh
        breakdown["Energy Cost (£)"] = energy_cost
    breakdown["Administration"] = 150
    breakdown["Depreciation/Maintenance"] = area * 0.5
    region_mult = {"National": 1.0, "Outer London": 1.1, "Inner London": 1.2}.get(region, 1.0)
    breakdown["Regional overhead uplift"] = (sum(breakdown.values())) * (region_mult - 1)
    breakdown["Development charge"] = supervisor_cost * 0.10 if customer_type == "Commercial" else 0
    return breakdown, sum(breakdown.values())

def calculate_production_items(items):
    results = []
    sup_monthly = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
    prisoner_monthly = num_prisoners * prisoner_salary * 4.33
    for name, workers_needed, mins_per_unit, prisoners_on_item in items:
        available_minutes = prisoners_on_item * workshop_hours * 60 * 4.33
        max_units = available_minutes / mins_per_unit if mins_per_unit > 0 else 0
        total_cost = sup_monthly + prisoner_monthly
        unit_cost = round(total_cost / max(max_units, 1), 2) if max_units > 0 else 0
        weekly_units_needed = round((total_cost / 4.33) / unit_cost, 1) if unit_cost > 0 else 0
        results.append({
            "Item": name,
            "Unit Cost (£)": unit_cost,
            "Max Units/Month": int(max_units),
            "Units Needed/Week": weekly_units_needed
        })
    return results

# ------------------------------
# DISPLAY GOV STYLE TABLE
# ------------------------------
def display_gov_table(breakdown, total_label="Total Monthly Cost"):
    html_table = "<table style='width:100%; border-collapse: collapse;'>"
    html_table += "<thead><tr style='background-color:#f3f2f1; text-align:left;'><th style='padding:8px; border-bottom: 2px solid #b1b4b6;'>Cost Item</th><th style='padding:8px; border-bottom: 2px solid #b1b4b6;'>Amount (£)</th></tr></thead><tbody>"
    for k, v in breakdown.items():
        html_table += f"<tr style='border-bottom:1px solid #e1e1e1;'><td style='padding:8px;'>{k}</td><td style='padding:8px;'>£{v:,.2f}</td></tr>"
    total_value = sum(breakdown.values())
    html_table += f"<tr style='font-weight:bold; background-color:#e6f0fa;'><td style='padding:8px;'>{total_label}</td><td style='padding:8px;'>£{total_value:,.2f}</td></tr></tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)

# ------------------------------
# HOST MODE
# ------------------------------
if workshop_mode == "Host" and apply_pct:
    st.subheader("Monthly Cost Breakdown (Host)")
    breakdown, total = calculate_host_costs()
    display_gov_table(breakdown)

# ------------------------------
# PRODUCTION MODE
# ------------------------------
elif workshop_mode == "Production":
    num_items = st.number_input("How many items are produced?", min_value=0, value=0)
    items = []
    for i in range(num_items):
        name = st.text_input(f"Item {i+1} name")
        workers_needed = st.number_input(f"Prisoners needed to make 1 unit of {name}", min_value=0, value=0, key=f"workers_{i}")
        mins_per_unit = st.number_input(f"Minutes to make 1 unit of {name}", min_value=0.0, value=0.0, key=f"mins_{i}")
        prisoners_on_item = st.number_input(f"How many of the {num_prisoners} prisoners work on {name}?", min_value=0, max_value=num_prisoners, value=0, key=f"prisoners_{i}")
        items.append((name, workers_needed, mins_per_unit, prisoners_on_item))

    if st.button("Calculate Item Costs"):
        results = calculate_production_items(items)
        st.subheader("Production Details per Item")
        st.table(results)

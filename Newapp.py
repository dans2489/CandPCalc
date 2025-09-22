import streamlit as st

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Prison Workshop Costing Tool", layout="wide")

# ------------------------------
# ENERGY RATES (UK GOV COMMERCIAL AVERAGE 2025)
# ------------------------------
ELECTRICITY_RATE = 0.25   # £/kWh
GAS_RATE = 0.07           # £/kWh
WATER_RATE = 2.0          # £/m³

# ------------------------------
# WORKSHOP ENERGY INTENSITY (kWh/m²/year)
# ------------------------------
workshop_energy = {
    "Empty/basic": {"electric": 40, "gas": 10, "water": 0.55},
    "Low energy": {"electric": 70, "gas": 20, "water": 0.55},
    "Medium energy": {"electric": 115, "gas": 40, "water": 0.55},
    "High energy": {"electric": 170, "gas": 70, "water": 0.55},
}

# ------------------------------
# CUSTOM CSS
# ------------------------------
st.markdown("""
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
""", unsafe_allow_html=True)

# ------------------------------
# TITLE
# ------------------------------
st.title("Cost and Pricing Calculator")

# ------------------------------
# RESET BUTTON
# ------------------------------
if st.button("Reset App"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

# ------------------------------
# INPUTS
# ------------------------------
region = st.selectbox("Region?", ["Select", "National", "Inner London", "Outer London"])
prison_name = st.text_input("Prison Name")
customer_type = st.selectbox("Quote for a?", ["Select", "Commercial", "Another Government Department"])
customer_name = st.text_input("Customer?")
workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"])
workshop_size = st.selectbox("Workshop size?", ["Select", "Small (Classroom ~25 prisoners)", "Medium (~50 prisoners)", "Large (~75 prisoners)", "Enter dimensions in ft"])
area = 0
if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f")
    area = width * length
else:
    size_map = {"Small (Classroom ~25 prisoners)": 900, "Medium (~50 prisoners)": 1600, "Large (~75 prisoners)": 2500}
    area = size_map.get(workshop_size, 0)

workshop_type = st.selectbox("Workshop type?", ["Select"] + list(workshop_energy.keys()))
workshop_hours = st.number_input("How many hours per week is it open?", min_value=0.0, format="%.2f")

num_prisoners = st.number_input("How many prisoners employed?", min_value=0)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")

num_supervisors = st.number_input("How many supervisors?", min_value=0)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s) (no salary cost to prison)?")

supervisor_salaries = []
if not customer_covers_supervisors:
    for i in range(num_supervisors):
        sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, format="%.2f")
        supervisor_salaries.append(sup_salary)
    contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=1)
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)
    st.subheader("Supervisor Time Allocation")
    st.info(f"Recommended: {recommended_pct}%")
    chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct))
else:
    chosen_pct = 0

# Employment support for commercial
dev_charge = 0.0
if customer_type == "Commercial":
    support = st.selectbox("Customer employment support?", ["Select", "None", "Employment on release/RoTL", "Post release", "Both"])
    if support == "None":
        dev_charge = 0.20
    elif support in ["Employment on release/RoTL", "Post release"]:
        dev_charge = 0.10
    else:
        dev_charge = 0.0

reason_for_low_pct = ""
if not customer_covers_supervisors and chosen_pct < recommended_pct:
    reason_for_low_pct = st.text_area("Explain why choosing lower supervisor % allocation:")

# ------------------------------
# VALIDATION
# ------------------------------
def validate_inputs():
    errors = []
    if region=="Select": errors.append("Select region")
    if not prison_name.strip(): errors.append("Enter prison name")
    if customer_type=="Select": errors.append("Select customer type")
    if not customer_name.strip(): errors.append("Enter customer name")
    if workshop_mode=="Select": errors.append("Select contract type")
    if workshop_size=="Select": errors.append("Select workshop size")
    if workshop_type=="Select": errors.append("Select workshop type")
    if workshop_hours <= 0: errors.append("Enter hours open")
    if num_prisoners <= 0: errors.append("Enter prisoners employed")
    if prisoner_salary <=0: errors.append("Enter prisoner salary")
    if not customer_covers_supervisors:
        if num_supervisors <=0: errors.append("Enter number of supervisors")
        if any(s<=0 for s in supervisor_salaries): errors.append("Enter all supervisor salaries")
        if chosen_pct < recommended_pct and not reason_for_low_pct.strip(): errors.append("Provide reason for low supervisor %")
    return errors

# ------------------------------
# COST CALCULATIONS
# ------------------------------
def calculate_host_costs():
    breakdown = {}
    # Prisoner wages
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52/12)
    # Supervisors
    supervisor_cost = 0
    if not customer_covers_supervisors:
        supervisor_cost = sum([(s/12)*(chosen_pct/100) for s in supervisor_salaries])
        breakdown["Supervisors"] = supervisor_cost
    # Utilities
    if workshop_type in workshop_energy:
        e = workshop_energy[workshop_type]
        hours_factor = workshop_hours / 37.5
        breakdown["Electricity"] = area * (e["electric"]/12) * ELECTRICITY_RATE * hours_factor
        breakdown["Gas"] = area * (e["gas"]/12) * GAS_RATE * hours_factor
        breakdown["Water"] = area * (e["water"]/12) * WATER_RATE * hours_factor
    breakdown["Administration"] = 150
    breakdown["Depreciation/Maintenance"] = area*0.5
    region_mult = {"National":1.0,"Outer London":1.1,"Inner London":1.2}.get(region,1.0)
    breakdown["Regional uplift"] = sum(breakdown.values())*(region_mult-1)
    breakdown["Development charge"] = supervisor_cost*dev_charge if customer_type=="Commercial" else 0
    return breakdown, sum(breakdown.values())

# ------------------------------
# Production calculations
# ------------------------------
def calculate_production(items):
    results=[]
    sup_monthly = sum([(s/12)*(chosen_pct/100) for s in supervisor_salaries]) if not customer_covers_supervisors else 0
    prisoner_monthly = num_prisoners*prisoner_salary*(52/12)
    for item in items:
        name = item["name"]
        mins_per_unit = item["minutes"]
        prisoners_assigned = item["assigned"]
        available_mins = prisoners_assigned * workshop_hours * 60 * (52/12)
        max_units = available_mins / mins_per_unit if mins_per_unit>0 else 0
        total_cost = sup_monthly + prisoner_monthly
        unit_cost = total_cost / max(max_units,1)
        weekly_cost = total_cost*(12/52)
        min_units_week = weekly_cost / unit_cost if unit_cost>0 else 0
        results.append({
            "Item": name,
            "Unit Cost (£)": round(unit_cost,2),
            "Min Units/Week": round(min_units_week,0),
            "Max Units/Week": round(max_units/4.33,0)
        })
    return results

# ------------------------------
# DISPLAY TABLE
# ------------------------------
def display_table(breakdown, total_label="Total Monthly Cost"):
    html="<table><thead><tr><th>Cost Item</th><th>Amount (£)</th></tr></thead><tbody>"
    for k,v in breakdown.items():
        html+=f"<tr><td>{k}</td><td>£{v:,.2f}</td></tr>"
    total=sum(breakdown.values())
    html+=f"<tr class='total-row'><td>{total_label}</td><td>£{total:,.2f}</td></tr></tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# ------------------------------
# GENERATE COSTS
# ------------------------------
if workshop_mode=="Host":
    if st.button("Generate Costs"):
        errors = validate_inputs()
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            st.subheader("Host Contract Costs")
            breakdown,total = calculate_host_costs()
            display_table(breakdown)

elif workshop_mode=="Production":
    st.subheader("Production Contract Costs")
    num_items = st.number_input("Number of items produced?", min_value=1, value=1)
    items=[]
    for i in range(num_items):
        with st.expander(f"Item {i+1} details"):
            name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
            minutes_per_item = st.number_input(f"Minutes per unit", min_value=1.0, key=f"mins_{i}")
            prisoners_assigned = st.number_input(f"Prisoners assigned to this item", min_value=1, max_value=num_prisoners, key=f"assigned_{i}")
            items.append({
                "name": name,
                "minutes": minutes_per_item,
                "assigned": prisoners_assigned
            })

    if st.button("Calculate Production Costs"):
        errors = validate_inputs()
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            results = calculate_production(items)
            for r in results:
                st.write(f"**{r['Item']}**")
                st.write(f"- Unit Cost (£): £{r['Unit Cost (£)']:.2f}")
                st.write(f"- Minimum units/week to cover costs: {r['Min Units/Week']}")
                st.write(f"- Maximum units/week: {r['Max Units/Week']}")
                percent = st.slider(f"Output % for {r['Item']}", min_value=0, max_value=100, value=100, key=f"percent_{r['Item']}")
                adjusted_units = round(r['Max Units/Week']*percent/100,0)
                st.write(f"- Adjusted units/week at {percent}% output: {adjusted_units}")

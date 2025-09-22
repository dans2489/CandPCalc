import streamlit as st

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="Prison Workshop Costing Tool",
    layout="wide",
)

# ------------------------------
# COMMERCIAL UTILITY TARIFFS (2025 AVERAGES, UK GOV DATA)
# ------------------------------
ELECTRICITY_RATE = 0.25   # £/kWh
GAS_RATE = 0.07           # £/kWh
WATER_RATE = 2.00         # £/m³ (approx commercial average)

# ------------------------------
# WORKSHOP TYPE ENERGY INTENSITY (kWh/m²/year)
# ------------------------------
workshop_energy = {
    "Workshop (Empty/basic)": {"electric": 40, "gas": 10, "water": 0.55},
    "Workshop (Low energy)": {"electric": 70, "gas": 20, "water": 0.55},
    "Workshop (Medium energy)": {"electric": 115, "gas": 40, "water": 0.55},
    "Workshop (High energy)": {"electric": 170, "gas": 70, "water": 0.55},
}

# ------------------------------
# CUSTOM CSS FOR GOV STYLE
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
# TITLE ONLY (NO LOGO)
# ------------------------------
st.title("Cost and Price Calculator")

# ------------------------------
# INPUTS
# ------------------------------
region = st.selectbox("Region?", ["Select", "National", "Inner London", "Outer London"], index=0)
prison_name = st.text_input("Prison Name")
customer_type = st.radio("Quote for a?", ["Select", "Commercial", "Another Government Department"], index=0)
customer_name = st.text_input("Customer?")
workshop_mode = st.radio("Contract type?", ["Select", "Host", "Production"], index=0)
workshop_size = st.selectbox("Workshop size?", ["Select", "Small", "Medium", "Large", "Enter dimensions"], index=0)

# Area
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

# Prisoner employment
num_prisoners = st.number_input("How many prisoners employed?", min_value=0, value=0)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f", value=0.0)

# Supervisors
num_supervisors = st.number_input("How many supervisors?", min_value=0, value=0)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s) (no salary cost to prison)?")

supervisor_salaries = []
if not customer_covers_supervisors:
    for i in range(num_supervisors):
        sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, format="%.2f", value=0.0)
        supervisor_salaries.append(sup_salary)

contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=0, value=0)

# Employment support (for commercial)
support = None
dev_charge = 0.0
if customer_type == "Commercial":
    support = st.radio(
        "What employment support does this customer offer?",
        ["Select", "None", "Employment on release and/or RoTL", "Post release support", "Both"],
        index=0
    )
    if support not in (None, "Select"):
        if support == "None":
            dev_charge = 0.20
        elif support in ["Employment on release and/or RoTL", "Post release support"]:
            dev_charge = 0.10
        else:
            dev_charge = 0.0

# Supervisor % allocation
st.subheader("Supervisor Time Allocation")
recommended_pct = 0
if workshop_hours > 0 and contracts > 0:
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)
    st.info(f"{recommended_pct}% recommended supervisor allocation")
chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), step=1)

reason_for_low_pct = ""
if chosen_pct < recommended_pct:
    reason_for_low_pct = st.text_area("Please explain why you are choosing a lower percentage:")

# ------------------------------
# VALIDATION
# ------------------------------
def validate_inputs():
    errors = []
    if region == "Select":
        errors.append("Please select a region.")
    if not prison_name.strip():
        errors.append("Please enter the prison name.")
    if customer_type == "Select":
        errors.append("Please select a customer type.")
    if customer_type == "Commercial" and (support is None or support == "Select"):
        errors.append("Please select the customer employment support option.")
    if not customer_name.strip():
        errors.append("Please enter the customer name.")
    if workshop_mode == "Select":
        errors.append("Please select a contract type.")
    if workshop_size == "Select":
        errors.append("Please select a workshop size.")
    if workshop_type == "Select":
        errors.append("Please select a workshop type.")
    if workshop_hours <= 0:
        errors.append("Please enter the number of workshop hours.")
    if num_prisoners <= 0:
        errors.append("Please enter the number of prisoners employed.")
    if prisoner_salary <= 0:
        errors.append("Please enter the prisoner salary per week.")
    if not customer_covers_supervisors:
        if num_supervisors <= 0:
            errors.append("Please enter the number of supervisors.")
        if not supervisor_salaries or any(s <= 0 for s in supervisor_salaries):
            errors.append("Please enter all supervisor salaries.")
    if contracts <= 0:
        errors.append("Please enter the number of contracts overseen.")
    if chosen_pct < recommended_pct and not reason_for_low_pct.strip():
        errors.append("Please provide a reason for choosing a lower supervisor % allocation.")
    return errors

# ------------------------------
# COST CALCULATIONS
# ------------------------------
def calculate_host_costs():
    breakdown = {}
    # Prisoner wages (monthly)
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52/12)

    # Supervisors
    if not customer_covers_supervisors:
        supervisor_cost = sum((s / 12) * (chosen_pct / 100) for s in supervisor_salaries)
        breakdown["Supervisors"] = supervisor_cost
    else:
        supervisor_cost = 0

    # Utilities
    if workshop_type in workshop_energy:
        factors = workshop_energy[workshop_type]
        electric_cost = area * (factors["electric"]/12) * ELECTRICITY_RATE
        gas_cost = area * (factors["gas"]/12) * GAS_RATE
        water_cost = area * (factors["water"]/12) * WATER_RATE
        breakdown["Electricity"] = electric_cost
        breakdown["Gas"] = gas_cost
        breakdown["Water"] = water_cost

    breakdown["Administration"] = 150
    breakdown["Depreciation/Maintenance"] = area * 0.5

    region_mult = {"National": 1.0, "Outer London": 1.1, "Inner London": 1.2}.get(region, 1.0)
    breakdown["Regional uplift"] = (sum(breakdown.values())) * (region_mult - 1)

    breakdown["Development charge"] = supervisor_cost * dev_charge if customer_type == "Commercial" else 0

    return breakdown, sum(breakdown.values())

def calculate_production_items(items):
    results = []
    sup_monthly = 0
    if not customer_covers_supervisors:
        sup_monthly = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
    prisoner_monthly = num_prisoners * prisoner_salary * (52/12)

    for name, mins_per_unit, prisoners_on_item in items:
        available_minutes = prisoners_on_item * workshop_hours * 60 * (52/12)
        max_units = available_minutes / mins_per_unit if mins_per_unit > 0 else 0

        total_cost = sup_monthly + prisoner_monthly
        unit_cost = round(total_cost / max(max_units, 1), 2) if max_units > 0 else 0

        weekly_total_cost = total_cost * (12/52)
        min_items_per_week = round(weekly_total_cost / unit_cost, 1) if unit_cost > 0 else 0

        results.append({
            "Item": name,
            "Unit Cost (£)": unit_cost,
            "Min Items/Week": min_items_per_week
        })
    return results

# ------------------------------
# DISPLAY TABLE
# ------------------------------
def display_gov_table(breakdown, total_label="Total Monthly Cost"):
    html_table = "<table>"
    html_table += "<thead><tr><th>Cost Item</th><th>Amount (£)</th></tr></thead><tbody>"
    for k, v in breakdown.items():
        html_table += f"<tr><td>{k}</td><td>£{v:,.2f}</td></tr>"
    total_value = sum(breakdown.values())
    html_table += f"<tr class='total-row'><td>{total_label}</td><td>£{total_value:,.2f}</td></tr>"
    html_table += "</tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)

# ------------------------------
# RUN CALCULATIONS
# ------------------------------
if st.button("Generate Costing"):
    errors = validate_inputs()
    if errors:
        st.error("Please fix the following before continuing:\n- " + "\n- ".join(errors))
    else:
        if workshop_mode == "Host":
            st.subheader("Host Contract Costing")
            breakdown, total = calculate_host_costs()
            display_gov_table(breakdown)

        elif workshop_mode == "Production":
            st.subheader("Production Contract Costing")
            num_items = st.number_input("How many different items are produced?", min_value=1, value=1)
            items = []
            for i in range(num_items):
                name = st.text_input(f"Item {i+1} name")
                mins_per_unit = st.number_input(f"Minutes to make one {name}", min_value=1.0, format="%.1f")
                prisoners_on_item = st.number_input(f"How many prisoners work on {name}?", min_value=1)
                items.append((name, mins_per_unit, prisoners_on_item))
            if st.button("Calculate Production Costs"):
                results = calculate_production_items(items)
                for r in results:
                    st.write(f"**{r['Item']}**")
                    st.write(f"- Unit Cost (£): £{r['Unit Cost (£)']:.2f}")
                    st.write(f"- Minimum items needed per week to cover costs: {r['Min Items/Week']}")

import streamlit as st

# ------------------------------
# PAGE CONFIG
# ------------------------------
# Set title and layout of the Streamlit app
st.set_page_config(
    page_title="Prison Workshop Costing Tool",
    layout="centered",
)

# ------------------------------
# CUSTOM CSS FOR GOV STYLE
# ------------------------------
# This is purely styling to mimic government website look
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
# APP TITLE
# ------------------------------
st.title("Cost and Price Calculator")

# ------------------------------
# WORKSHOP TYPE UTILITIES (Commercial Rates)
# Units: electricity/gas in kWh/m²/year, water in m³/m²/year
# Rates in £/unit commercial
# ------------------------------
workshop_utilities = {
    "Woodwork": {"electric": 75, "gas": 40, "water": 0.55},
    "Metalwork": {"electric": 80, "gas": 45, "water": 0.55},
    "Textiles": {"electric": 120, "gas": 35, "water": 0.55},
    "Warehousing": {"electric": 33, "gas": 20, "water": 0.55},
    "Packing": {"electric": 50, "gas": 25, "water": 0.55},
    "Empty space (no machinery)": {"electric": 10, "gas": 5, "water": 0.55},
}

unit_costs = {"electric": 0.257, "gas": 0.063, "water": 2.47}  # £ per kWh or £ per m³

# ------------------------------
# INPUTS
# ------------------------------
region = st.selectbox("Region?", ["Select", "National", "Inner London", "Outer London"], index=0)
prison_name = st.text_input("Prison Name")
customer_type = st.radio("Quote for a?", ["Select", "Commercial", "Another Government Department"], index=0)
customer_name = st.text_input("Customer?")
workshop_mode = st.radio("Contract type?", ["Select", "Host", "Production"], index=0)
workshop_size = st.selectbox("Workshop size?", ["Select", "Small", "Medium", "Large", "Enter dimensions"], index=0)

# Area calculation
area = 0
if workshop_size == "Enter dimensions":
    width = st.number_input("Width (m)", min_value=0.0, format="%.2f", value=0.0)
    length = st.number_input("Length (m)", min_value=0.0, format="%.2f", value=0.0)
    if width > 0 and length > 0:
        area = width * length  # m²
else:
    area_map = {"Small": 100, "Medium": 250, "Large": 500}
    area = area_map.get(workshop_size, 0)

workshop_type = st.selectbox("Workshop type?", ["Select"] + list(workshop_utilities.keys()), index=0)
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
# EMPLOYMENT SUPPORT (Commercial)
# ------------------------------
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
reason_for_low_pct = ""
if chosen_pct < recommended_pct:
    reason_for_low_pct = st.text_area("Please explain why you are choosing a lower percentage:")

# ------------------------------
# VALIDATION FUNCTION
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
# HOST COST CALCULATION FUNCTION
# ------------------------------
def calculate_host_costs():
    breakdown = {}
    weeks_to_month = 52/12  # weeks per month conversion

    # 1. Prisoner wages (weekly salary × num prisoners × weeks per month)
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * weeks_to_month

    # 2. Supervisor cost (monthly allocation based on chosen %)
    supervisor_cost = sum((s / 12) * (chosen_pct / 100) for s in supervisor_salaries)
    breakdown["Supervisors"] = supervisor_cost

    # 3. Utilities (electric, gas, water)
    if workshop_type in workshop_utilities:
        util = workshop_utilities[workshop_type]
        breakdown["Electricity (£)"] = area * (util["electric"] / 12) * unit_costs["electric"]
        breakdown["Gas (£)"] = area * (util["gas"] / 12) * unit_costs["gas"]
        breakdown["Water (£)"] = area * (util["water"] / 12) * unit_costs["water"]

    # 4. Administration and Maintenance
    breakdown["Administration (£)"] = 150
    breakdown["Maintenance / Depreciation (£)"] = area * 0.50

    # 5. Regional uplift
    region_mult_map = {"National": 1.00, "Outer London": 1.10, "Inner London": 1.28}
    region_mult = region_mult_map.get(region, 1.0)
    breakdown["Regional overhead uplift"] = sum(breakdown.values()) * (region_mult - 1)

    # 6. Development charge
    breakdown["Development charge"] = supervisor_cost * dev_charge if customer_type == "Commercial" else 0

    return breakdown, sum(breakdown.values())

# ------------------------------
# PRODUCTION ITEMS INPUT (DYNAMIC)
# ------------------------------
st.subheader("Production Items")
num_items = st.number_input("How many different items will be produced?", min_value=0, value=0, step=1)
production_items = []

for i in range(num_items):
    st.markdown(f"**Item {i+1}**")
    name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
    workers_needed = st.number_input(f"Number of prisoners needed for {name}", min_value=0, value=1, key=f"workers_{i}")
    mins_per_unit = st.number_input(f"Minutes to produce one unit of {name}", min_value=1, value=60, key=f"mins_{i}")
    prisoners_on_item = st.number_input(f"Number of prisoners working on {name}", min_value=1, value=workers_needed, key=f"prisoners_{i}")
    production_items.append((name, workers_needed, mins_per_unit, prisoners_on_item))

# ------------------------------
# DISPLAY COSTS
# ------------------------------
if st.button("Calculate Costs"):
    errors = validate_inputs()
    if errors:
        st.error("Please fix the following errors:")
        for err in errors:
            st.write(f"- {err}")
    else:
        weeks_to_month = 52/12  # weeks per month
        month_to_weeks = 12/52  # months per week

        # HOST COSTS
        if workshop_mode == "Host":
            host_breakdown, host_total = calculate_host_costs()
            st.subheader("Host Workshop Costs")
            for k, v in host_breakdown.items():
                st.write(f"{k}: £{v:,.2f}")
            st.write(f"**Total Monthly Cost: £{host_total:,.2f}**")

        # PRODUCTION COSTS
        elif workshop_mode == "Production" and production_items:
            st.subheader("Production Item Costs")
            sup_monthly = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
            prisoner_monthly = num_prisoners * prisoner_salary * weeks_to_month

            for name, workers_needed, mins_per_unit, prisoners_on_item in production_items:
                # Available minutes per month
                available_minutes_per_month = prisoners_on_item * workshop_hours * 60 * weeks_to_month

                # Total monthly cost
                total_monthly_cost = sup_monthly + prisoner_monthly

                # Unit cost per item
                unit_cost = total_monthly_cost / max(available_minutes_per_month / mins_per_unit, 1)

                # Minimum items per week to cover costs
                weekly_total_cost = total_monthly_cost * month_to_weeks
                min_items_per_week = round(weekly_total_cost / unit_cost, 1) if unit_cost > 0 else 0

                st.write(f"**Item: {name}**")
                st.write(f"- Unit Cost (£): £{unit_cost:,.2f}")
                st.write(f"- Minimum items needed per week to cover costs: {min_items_per_week:,.1f}")

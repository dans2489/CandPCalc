import streamlit as st

st.set_page_config(page_title="Prison Workshop Costing Tool", layout="centered")

st.title("Prison Workshop Costing Tool")

# ------------------------------
# INPUTS
# ------------------------------
region = st.selectbox("Region?", ["National", "Inner London", "Outer London"])

customer_type = st.radio("Quote for a?", ["Commercial", "Another Government Department"])

customer_name = st.text_input("Customer?")

workshop_mode = st.radio("Contract type?", ["Host", "Production"])

workshop_size = st.selectbox("Workshop size?", ["Small", "Medium", "Large", "Enter dimensions"])
if workshop_size == "Enter dimensions":
    width = st.number_input("Width (m)", min_value=1)
    length = st.number_input("Length (m)", min_value=1)
    area = width * length
else:
    area_map = {"Small": 100, "Medium": 250, "Large": 500}
    area = area_map[workshop_size]

workshop_type = st.selectbox(
    "Workshop type?",
    ["Woodwork", "Metalwork", "Warehousing", "Packing", "Textiles", "Empty space (no machinery)"]
)

workshop_hours = st.number_input("How many hours per week is it open?", min_value=1, max_value=168, value=27)

num_prisoners = st.number_input("How many prisoners employed?", min_value=0, value=10)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, value=18.0)

num_supervisors = st.number_input("How many supervisors?", min_value=0, value=1)

supervisor_salaries = []
for i in range(num_supervisors):
    sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, value=42000.0, step=1000.0)
    supervisor_salaries.append(sup_salary)

contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=1, value=1)

# ------------------------------
# SUPERVISOR % CALCULATION
# ------------------------------
st.subheader("Supervisor Time Allocation")

recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)

st.write(f"📌 Based on {workshop_hours} hrs/week and {contracts} contracts, "
         f"recommended supervisor allocation = **{recommended_pct}%**")

chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), step=1)

apply_pct = st.button("Set Supervisor %")

if apply_pct:
    st.success(f"Supervisor percentage set to {chosen_pct}%")

# ------------------------------
# EMPLOYMENT SUPPORT
# ------------------------------
if customer_type == "Commercial":
    support = st.radio(
        "What employment support does this customer offer?",
        ["None", "Employment on release and/or RoTL", "Post release support", "Both"]
    )
else:
    support = "N/A"

# Development charge logic
if customer_type == "Commercial":
    if support == "None":
        dev_charge = 0.20
    elif support in ["Employment on release and/or RoTL", "Post release support"]:
        dev_charge = 0.10
    else:
        dev_charge = 0.0
else:
    dev_charge = 0.0

# ------------------------------
# COST CALCULATIONS
# ------------------------------
def calculate_host_costs():
    """Calculate Host model monthly costs with breakdown"""
    breakdown = {}

    # Prisoners
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * 4.33  # monthly

    # Supervisors
    supervisor_cost = 0
    for s in supervisor_salaries:
        monthly = (s / 12) * (chosen_pct / 100)
        supervisor_cost += monthly
    breakdown["Supervisors"] = supervisor_cost

    # Utilities estimate (simplified by area and type)
    utility_rate = {
        "Woodwork": 12,
        "Metalwork": 15,
        "Warehousing": 6,
        "Packing": 5,
        "Textiles": 8,
        "Empty space (no machinery)": 2
    }
    utilities = area * utility_rate[workshop_type] * (workshop_hours / 37.5) * 4.33 / 100
    breakdown["Utilities"] = utilities

    # Maintenance / depreciation (flat % of utilities + area)
    breakdown["Maintenance"] = area * 0.5

    # Overheads (region multiplier)
    region_mult = {"National": 1.0, "Outer London": 1.1, "Inner London": 1.2}[region]
    overheads = (sum(breakdown.values())) * (region_mult - 1)
    breakdown["Regional overhead uplift"] = overheads

    # Development charge
    dev_amount = (supervisor_cost if customer_type == "Commercial" else 0) * dev_charge
    breakdown["Development charge"] = dev_amount

    # Total
    total = sum(breakdown.values())
    return breakdown, total


def calculate_production_items(items):
    """Calculate per-unit costs for Production model"""
    results = {}
    # Supervisor monthly cost
    sup_monthly = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
    prisoner_monthly = num_prisoners * prisoner_salary * 4.33

    for i, item in enumerate(items, 1):
        name, workers, mins = item
        units_per_month = (workers * (workshop_hours * 60 * 4.33)) / mins
        total_cost = sup_monthly + prisoner_monthly
        unit_cost = total_cost / max(units_per_month, 1)
        results[name] = round(unit_cost, 2)
    return results


# ------------------------------
# HOST MODE
# ------------------------------
if workshop_mode == "Host":
    if apply_pct:
        st.subheader("Monthly Cost Breakdown (Host)")
        breakdown, total = calculate_host_costs()
        for k, v in breakdown.items():
            st.write(f"- {k}: £{v:,.2f}")
        st.write(f"### 💰 Total Monthly Cost: £{total:,.2f}")

# ------------------------------
# PRODUCTION MODE
# ------------------------------
elif workshop_mode == "Production":
    num_items = st.number_input("How many items are produced?", min_value=1, value=1)
    items = []
    for i in range(num_items):
        name = st.text_input(f"Item {i+1} name")
        workers = st.number_input(f"Prisoners needed to make 1 unit of {name}", min_value=1, value=1, key=f"workers_{i}")
        mins = st.number_input(f"Minutes to make 1 unit of {name}", min_value=1.0, value=1.0, key=f"mins_{i}")
        items.append((name, workers, mins))

    if st.button("Calculate Item Costs"):
        results = calculate_production_items(items)
        st.subheader("Per-Unit Costs")
        for k, v in results.items():
            st.write(f"- {k}: £{v}")

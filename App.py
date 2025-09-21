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
    /* Overall background and text */
    .main {
        background-color: #ffffff;
        color: #0b0c0c;
    }

    /* Page title */
    .stApp h1 {
        color: #005ea5;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* Subheaders */
    .stApp h2, .stApp h3 {
        color: #005ea5;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    /* Buttons */
    div.stButton > button:first-child {
        background-color: #10703c;
        color: white;
        font-weight: bold;
        padding: 6px 12px;
        border-radius: 4px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* Inputs */
    div.stTextInput > label, 
    div.stNumberInput > label, 
    div.stSelectbox > label, 
    div.stRadio > label {
        font-weight: bold;
        margin-bottom: 5px;
    }

    /* Sliders */
    .stSlider > div > div:nth-child(1) > div > div > div {
        color: #005ea5;
    }

    /* Input sections styling */
    .stForm, .stContainer {
        box-shadow: 0 0 5px #e1e1e1;
        padding: 12px 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }

    /* GOV.uk style table */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    table th {
        background-color: #f3f2f1;
        text-align: left;
        padding: 8px;
        border-bottom: 2px solid #b1b4b6;
    }
    table td {
        padding: 8px;
        border-bottom: 1px solid #e1e1e1;
    }
    table tr.total-row {
        font-weight: bold;
        background-color: #e6f0fa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# APP TITLE
# ------------------------------
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
st.markdown("**Recommended allocation based on hours and number of contracts:**")

recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)

st.info(f"{recommended_pct}% recommended supervisor allocation")

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
    breakdown = {}
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * 4.33

    supervisor_cost = 0
    for s in supervisor_salaries:
        monthly = (s / 12) * (chosen_pct / 100)
        supervisor_cost += monthly
    breakdown["Supervisors"] = supervisor_cost

    commercial_rates = {"Electric": 1.5, "Gas": 0.8, "Water": 0.3}
    hours_factor = workshop_hours / 37.5
    for util, rate in commercial_rates.items():
        cost = area * rate * hours_factor
        breakdown[f"{util} (£{rate}/m²)"] = cost

    breakdown["Administration"] = 150
    breakdown["Depreciation/Maintenance"] = area * 0.5

    region_mult = {"National": 1.0, "Outer London": 1.1, "Inner London": 1.2}[region]
    overheads = (sum(breakdown.values())) * (region_mult - 1)
    breakdown["Regional overhead uplift"] = overheads

    dev_amount = (supervisor_cost if customer_type == "Commercial" else 0) * dev_charge
    breakdown["Development charge"] = dev_amount

    total = sum(breakdown.values())
    return breakdown, total


def calculate_production_items(items):
    results = {}
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
# FUNCTION TO DISPLAY GOV-STYLE TABLE
# ------------------------------
def display_gov_table(breakdown, total_label="Total Monthly Cost"):
    html_table = """
    <table>
    <thead>
    <tr>
        <th>Cost Item</th>
        <th>Amount (£)</th>
    </tr>
    </thead>
    <tbody>
    """
    for k, v in breakdown.items():
        html_table += f"""
        <tr>
            <td>{k}</td>
            <td>£{v:,.2f}</td>
        </tr>
        """

    html_table += f"""
    <tr class="total-row">
        <td>{total_label}</td>
        <td>£{sum(breakdown.values()):,.2f}</td>
    </tr>
    </tbody></table>
    """
    st.markdown(html_table, unsafe_allow_html=True)

# ------------------------------
# HOST MODE
# ------------------------------
if workshop_mode == "Host":
    if apply_pct:
        st.subheader("Monthly Cost Breakdown (Host)")
        breakdown, total = calculate_host_costs()
        display_gov_table(breakdown)

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
        display_gov_table(results, total_label="Unit Cost")

import streamlit as st
import datetime

# ------------------------------
# SESSION STATE SETUP
# ------------------------------
if "users" not in st.session_state:
    st.session_state["users"] = {}  # email -> password
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "quotes" not in st.session_state:
    st.session_state["quotes"] = []
if "quote_counter" not in st.session_state:
    st.session_state["quote_counter"] = 1

# ------------------------------
# LOGIN / REGISTER LOGIC
# ------------------------------
def login_screen():
    st.title("🔐 Prison Workshop Costing Tool - Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login to your account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if email in st.session_state["users"] and st.session_state["users"][email] == password:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = email
                st.success("Login successful ✅")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        st.subheader("Create a new account")
        new_email = st.text_input("Justice Email (must end with @justice.gov.uk)")
        new_password = st.text_input("Password", type="password")
        if st.button("Register"):
            if not new_email.endswith("@justice.gov.uk"):
                st.error("Only @justice.gov.uk emails are allowed")
            elif new_email in st.session_state["users"]:
                st.error("User already exists")
            else:
                # Mock email validation
                st.session_state["users"][new_email] = new_password
                st.success("Registration successful ✅ You can now log in.")


# ------------------------------
# COSTING TOOL
# ------------------------------
def costing_tool():
    st.title("Prison Workshop Costing Tool")

    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.experimental_rerun()

    # ------------------------------
    # INPUTS
    # ------------------------------
    region = st.selectbox("Region?", ["", "National", "Inner London", "Outer London"])
    prison_name = st.text_input("Prison Name")
    customer_type = st.radio("Quote for a?", ["", "Commercial", "Another Government Department"])
    customer_name = st.text_input("Customer?")
    workshop_mode = st.radio("Contract type?", ["", "Host", "Production"])
    workshop_size = st.selectbox("Workshop size?", ["", "Small", "Medium", "Large", "Enter dimensions"])
    if workshop_size == "Enter dimensions":
        width = st.number_input("Width (m)", min_value=1, value=1)
        length = st.number_input("Length (m)", min_value=1, value=1)
        area = width * length
    elif workshop_size in ["Small", "Medium", "Large"]:
        area_map = {"Small": 100, "Medium": 250, "Large": 500}
        area = area_map[workshop_size]
    else:
        area = 0

    workshop_type = st.selectbox(
        "Workshop type?",
        ["", "Woodwork", "Metalwork", "Warehousing", "Packing", "Textiles", "Empty space (no machinery)"]
    )

    workshop_hours = st.number_input("How many hours per week is it open?", min_value=1, max_value=168, value=1)
    num_prisoners = st.number_input("How many prisoners employed?", min_value=0, value=0)
    prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, value=0.0)
    num_supervisors = st.number_input("How many supervisors?", min_value=0, value=0)

    supervisor_salaries = []
    for i in range(num_supervisors):
        sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, value=0.0, step=1000.0)
        supervisor_salaries.append(sup_salary)

    contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=1, value=1)

    # ------------------------------
    # SUPERVISOR % CALCULATION
    # ------------------------------
    if workshop_hours > 0 and contracts > 0:
        st.subheader("Supervisor Time Allocation")
        recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)
        st.info(f"Recommended supervisor allocation: {recommended_pct}%")
        chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), step=1)

        reason = ""
        if chosen_pct < recommended_pct:
            reason = st.text_area(
                "You have selected a supervisor contribution less than the recommended. Please explain why here..."
            )

    # ------------------------------
    # EMPLOYMENT SUPPORT
    # ------------------------------
    if customer_type == "Commercial":
        support = st.radio(
            "What employment support does this customer offer?",
            ["", "None", "Employment on release and/or RoTL", "Post release support", "Both"]
        )
    else:
        support = "N/A"

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
    energy_rates = {
        "Woodwork": {"Electric": 2.0, "Gas": 1.0, "Water": 0.4},
        "Metalwork": {"Electric": 2.5, "Gas": 1.2, "Water": 0.5},
        "Warehousing": {"Electric": 1.0, "Gas": 0.5, "Water": 0.3},
        "Packing": {"Electric": 1.2, "Gas": 0.6, "Water": 0.3},
        "Textiles": {"Electric": 1.5, "Gas": 0.7, "Water": 0.35},
        "Empty space (no machinery)": {"Electric": 0.5, "Gas": 0.2, "Water": 0.1}
    }

    def calculate_host_costs():
        breakdown = {}
        breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * 4.33
        supervisor_cost = sum((s / 12) * (chosen_pct / 100) for s in supervisor_salaries)
        breakdown["Supervisors"] = supervisor_cost

        rates = energy_rates.get(workshop_type, {"Electric": 0, "Gas": 0, "Water": 0})
        hours_factor = workshop_hours / 37.5
        for k, v in rates.items():
            breakdown[f"{k} (£{v}/m²)"] = area * v * hours_factor

        breakdown["Administration"] = 150
        breakdown["Depreciation/Maintenance"] = area * 0.5

        region_mult = {"National": 1.0, "Outer London": 1.1, "Inner London": 1.2}.get(region, 1.0)
        breakdown["Regional overhead uplift"] = sum(breakdown.values()) * (region_mult - 1)

        breakdown["Development charge"] = supervisor_cost * dev_charge if customer_type == "Commercial" else 0
        return breakdown, sum(breakdown.values())

    def calculate_production_items(items, total_costs):
        results = {}
        sup_monthly = sum([(s / 12) * (chosen_pct / 100) for s in supervisor_salaries])
        prisoner_monthly = num_prisoners * prisoner_salary * 4.33
        overhead_per_prisoner = (total_costs / num_prisoners) if num_prisoners > 0 else 0

        for name, assigned, mins, secs in items:
            total_mins = mins + secs / 60
            max_units = (assigned * workshop_hours * 60 * 4.33) / max(total_mins, 0.01)
            share_costs = overhead_per_prisoner * assigned
            unit_cost = (sup_monthly + prisoner_monthly + share_costs) / max(max_units, 1)
            min_units = share_costs / max(unit_cost, 0.01)
            results[name] = {
                "Unit cost": round(unit_cost, 2),
                "Max units/month": int(max_units),
                "Min units/month to cover costs": int(min_units)
            }
        return results

    def display_table(breakdown, total_label="Total Monthly Cost"):
        st.write("### Monthly Cost Breakdown")
        for k, v in breakdown.items():
            st.write(f"- {k}: £{v:,.2f}")
        st.success(f"{total_label}: £{sum(breakdown.values()):,.2f}")

    # ------------------------------
    # HOST MODE
    # ------------------------------
    if workshop_mode == "Host":
        if st.button("Calculate Host Costs"):
            breakdown, total = calculate_host_costs()
            display_table(breakdown)

            # Save quote
            quote_num = f"HMPPS{st.session_state['quote_counter']:04d}"
            st.session_state["quote_counter"] += 1
            st.session_state["quotes"].append({
                "quote_num": quote_num,
                "region": region,
                "prison": prison_name,
                "customer": customer_name,
                "total": total,
                "date": datetime.date.today()
            })
            st.success(f"Quote {quote_num} saved ✅ (and would be emailed incl. Dan.smith1@justice.gov.uk)")

    # ------------------------------
    # PRODUCTION MODE
    # ------------------------------
    elif workshop_mode == "Production":
        num_items = st.number_input("How many items are produced?", min_value=1, value=1)
        items = []
        for i in range(num_items):
            name = st.text_input(f"Item {i+1} name")
            assigned = st.number_input(
                f"Prisoners assigned to {name}", min_value=0, max_value=num_prisoners, value=0, key=f"assigned_{i}"
            )
            mins = st.number_input(f"Minutes to make 1 unit of {name}", min_value=0, value=0, key=f"mins_{i}")
            secs = st.number_input(f"Seconds to make 1 unit of {name}", min_value=0, max_value=59, value=0, key=f"secs_{i}")
            items.append((name, assigned, mins, secs))

        if st.button("Calculate Production Costs"):
            breakdown, total = calculate_host_costs()  # base costs
            results = calculate_production_items(items, total)
            st.write("### Production Costing Results")
            for k, v in results.items():
                st.write(f"- {k}: Unit cost £{v['Unit cost']}, Max {v['Max units/month']} units, Min {v['Min units/month to cover costs']} units")

            # Save quote
            quote_num = f"HMPPS{st.session_state['quote_counter']:04d}"
            st.session_state["quote_counter"] += 1
            st.session_state["quotes"].append({
                "quote_num": quote_num,
                "region": region,
                "prison": prison_name,
                "customer": customer_name,
                "total": total,
                "date": datetime.date.today()
            })
            st.success(f"Quote {quote_num} saved ✅ (and would be emailed incl. Dan.smith1@justice.gov.uk)")

    # ------------------------------
    # QUOTE HISTORY
    # ------------------------------
    st.subheader("My Quotes")
    if len(st.session_state["quotes"]) == 0:
        st.info("No quotes yet.")
    else:
        for q in st.session_state["quotes"]:
            st.write(f"📌 {q['quote_num']} | {q['prison']} | {q['region']} | £{q['total']:,.2f} | {q['date']}")


# ------------------------------
# MAIN APP
# ------------------------------
if not st.session_state["logged_in"]:
    login_screen()
else:
    costing_tool()

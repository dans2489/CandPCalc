import streamlit as st
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# ------------------------------
# SESSION STATE SETUP
# ------------------------------
if "users" not in st.session_state:
    st.session_state["users"] = {}
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "quotes" not in st.session_state:
    st.session_state["quotes"] = []
if "quote_counter" not in st.session_state:
    st.session_state["quote_counter"] = 1

# ------------------------------
# LOGIN / REGISTER MOCKUP
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
                st.session_state["users"][new_email] = new_password
                st.success("Registration successful ✅ You can now log in.")

# ------------------------------
# PDF GENERATION
# ------------------------------
def generate_pdf(quote_num, region, prison, customer, workshop_mode, breakdown, production_results, supervisor_justification):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header GOV.UK style
    c.setFillColor(colors.HexColor("#005ea5"))  # Blue
    c.rect(0, height-40, width, 40, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(10*mm, height-30, "Ministry of Justice - Official Prison Workshop Quote")

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(10*mm, height-60, f"Quote Number: {quote_num}")
    c.drawString(10*mm, height-75, f"Date: {datetime.date.today()}")
    c.drawString(10*mm, height-90, f"Prison: {prison}")
    c.drawString(10*mm, height-105, f"Region: {region}")
    c.drawString(10*mm, height-120, f"Customer: {customer}")
    c.drawString(10*mm, height-135, f"Workshop Mode: {workshop_mode}")

    y = height - 160
    c.setFont("Helvetica-Bold", 12)
    c.drawString(10*mm, y, "Cost Breakdown:")
    y -= 15
    c.setFont("Helvetica", 10)
    for k, v in breakdown.items():
        c.drawString(15*mm, y, f"{k}: £{v:,.2f}")
        y -= 12

    if supervisor_justification:
        y -= 5
        c.setFont("Helvetica-Bold", 10)
        c.drawString(10*mm, y, "Supervisor Justification:")
        y -= 12
        c.setFont("Helvetica", 10)
        c.drawString(15*mm, y, supervisor_justification)
        y -= 15

    if production_results:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(10*mm, y, "Production Details:")
        y -= 15
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15*mm, y, "Item | Unit Cost | Max Units/Month | Min Units/Month")
        y -= 12
        c.setFont("Helvetica", 10)
        for item, v in production_results.items():
            line = f"{item} | £{v['Unit cost']} | {v['Max units/month']} | {v['Min units/month to cover costs']}"
            c.drawString(15*mm, y, line)
            y -= 12

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(10*mm, 15*mm, "Official – Ministry of Justice")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ------------------------------
# COSTING TOOL
# ------------------------------
def costing_tool():
    st.title("Prison Workshop Costing Tool")
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.experimental_rerun()

    # Inputs
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

    workshop_hours = st.number_input("Hours per week open", min_value=1, max_value=168, value=1)
    num_prisoners = st.number_input("Prisoners employed", min_value=0, value=0)
    prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, value=0.0)
    num_supervisors = st.number_input("Supervisors", min_value=0, value=0)

    supervisor_salaries = []
    for i in range(num_supervisors):
        sup_salary = st.number_input(f"Supervisor {i+1} annual salary (£)", min_value=0.0, value=0.0, step=1000.0)
        supervisor_salaries.append(sup_salary)

    contracts = st.number_input("Contracts these supervisors oversee", min_value=1, value=1)

    # Supervisor allocation
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if workshop_hours > 0 else 0
    st.info(f"Recommended supervisor allocation: {recommended_pct}%")
    chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), step=1)
    supervisor_justification = ""
    if chosen_pct < recommended_pct:
        supervisor_justification = st.text_area(
            "Supervisor contribution below recommended. Please explain..."
        )

    # Employment support
    if customer_type == "Commercial":
        support = st.radio("Employment support offered?", ["", "None", "Employment on release and/or RoTL", "Post release support", "Both"])
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

    # Energy rates
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

    # Production mode
    production_results = None
    if workshop_mode == "Production":
        num_items = st.number_input("How many items?", min_value=1, value=1)
        items = []
        for i in range(num_items):
            name = st.text_input(f"Item {i+1} name")
            assigned = st.number_input(f"Prisoners assigned to {name}", min_value=0, max_value=num_prisoners, value=0, key=f"assigned_{i}")
            mins = st.number_input(f"Minutes to make 1 unit of {name}", min_value=0, value=0, key=f"mins_{i}")
            secs = st.number_input(f"Seconds to make 1 unit of {name}", min_value=0, max_value=59, value=0, key=f"secs_{i}")
            items.append((name, assigned, mins, secs))

    # ------------------------------
    # GENERATE QUOTE BUTTON
    # ------------------------------
    if st.button("Generate Quote, Email & Exit"):
        if st.confirm("Are you sure you want to generate and send this official quote?"):
            breakdown, total = calculate_host_costs()
            if workshop_mode == "Production":
                production_results = {}
                sup_monthly = sum((s/12)*(chosen_pct/100) for s in supervisor_salaries)
                prisoner_monthly = num_prisoners * prisoner_salary * 4.33
                overhead_per_prisoner = (total / num_prisoners) if num_prisoners > 0 else 0
                for name, assigned, mins, secs in items:
                    total_mins = mins + secs/60
                    max_units = (assigned * workshop_hours * 60 * 4.33) / max(total_mins,0.01)
                    share_costs = overhead_per_prisoner * assigned
                    unit_cost = (sup_monthly + prisoner_monthly + share_costs)/max(max_units,1)
                    min_units = share_costs / max(unit_cost,0.01)
                    production_results[name] = {
                        "Unit cost": round(unit_cost,2),
                        "Max units/month": int(max_units),
                        "Min units/month to cover costs": int(min_units)
                    }

            # Generate PDF
            quote_num = f"HMPPS{st.session_state['quote_counter']:04d}"
            st.session_state["quote_counter"] +=1
            pdf_buffer = generate_pdf(
                quote_num, region, prison_name, customer_name, workshop_mode, breakdown,
                production_results, supervisor_justification
            )

            # Save quote in session
            st.session_state["quotes"].append({
                "quote_num": quote_num,
                "region": region,
                "prison": prison_name,
                "customer": customer_name,
                "total": total,
                "date": datetime.date.today()
            })

            # MOCK EMAIL SEND
            st.success(f"Quote {quote_num} generated and would be emailed to customer with CC Dan.smith1@justice.gov.uk ✅")
            st.download_button("Download PDF", pdf_buffer, file_name=f"{quote_num}.pdf")

            # Log out
            st.session_state["logged_in"] = False
            st.session_state["current_user"] = None
            st.experimental_rerun()

    # ------------------------------
    # MY QUOTES
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

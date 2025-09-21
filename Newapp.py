import streamlit as st
import smtplib
from email.message import EmailMessage

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Prison Workshop Costing Tool", layout="centered")

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
# RESET BUTTON
# ------------------------------
if st.button("Reset App"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

# ------------------------------
# APP TITLE
# ------------------------------
st.title("Prison Workshop Costing Tool")

# ------------------------------
# INPUTS
# ------------------------------
region = st.selectbox("Region?", ["", "National", "Inner London", "Outer London"])
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
if workshop_hours>0 and contracts>0:
    st.subheader("Supervisor Time Allocation")
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1)
    st.info(f"Recommended supervisor allocation: {recommended_pct}%")
    chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), step=1)

    reason = ""
    if chosen_pct < recommended_pct:
        reason = st.text_area("You have selected a supervisor contribution less than the recommended. Please explain why here...")

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
    "Woodwork": {"Electric":2.0, "Gas":1.0, "Water":0.4},
    "Metalwork": {"Electric":2.5, "Gas":1.2, "Water":0.5},
    "Warehousing": {"Electric":1.0, "Gas":0.5, "Water":0.3},
    "Packing": {"Electric":1.2, "Gas":0.6, "Water":0.3},
    "Textiles": {"Electric":1.5, "Gas":0.7, "Water":0.35},
    "Empty space (no machinery)": {"Electric":0.5, "Gas":0.2, "Water":0.1}
}

def calculate_host_costs():
    breakdown = {}
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * 4.33
    supervisor_cost = sum((s / 12)*(chosen_pct/100) for s in supervisor_salaries)
    breakdown["Supervisors"] = supervisor_cost

    rates = energy_rates.get(workshop_type, {"Electric":0,"Gas":0,"Water":0})
    hours_factor = workshop_hours/37.5
    for k,v in rates.items():
        breakdown[f"{k} (£{v}/m²)"] = area*v*hours_factor

    breakdown["Administration"] = 150
    breakdown["Depreciation/Maintenance"] = area*0.5

    region_mult = {"National":1.0,"Outer London":1.1,"Inner London":1.2}.get(region,1.0)
    breakdown["Regional overhead uplift"] = sum(breakdown.values())*(region_mult-1)

    breakdown["Development charge"] = supervisor_cost*dev_charge if customer_type=="Commercial" else 0
    return breakdown, sum(breakdown.values())

def calculate_production_items(items):
    results = {}
    sup_monthly = sum([(s/12)*(chosen_pct/100) for s in supervisor_salaries])
    prisoner_monthly = num_prisoners*prisoner_salary*4.33
    for name, workers, mins, secs in items:
        total_mins = mins + secs/60
        units_per_month = (workers*workshop_hours*60*4.33)/max(total_mins,0.01)
        total_cost = sup_monthly + prisoner_monthly
        results[name] = round(total_cost/units_per_month,2)
    return results

def display_gov_table(breakdown, total_label="Total Monthly Cost"):
    html_table = "<table style='width:100%; border-collapse: collapse;'>"
    html_table += "<thead><tr style='background-color:#f3f2f1; text-align:left;'><th style='padding:8px; border-bottom: 2px solid #b1b4b6;'>Cost Item</th><th style='padding:8px; border-bottom: 2px solid #b1b4b6;'>Amount (£)</th></tr></thead><tbody>"
    for k,v in breakdown.items():
        html_table += f"<tr style='border-bottom:1px solid #e1e1e1;'><td style='padding:8px;'>{k}</td><td style='padding:8px;'>£{v:,.2f}</td></tr>"
    total_value = sum(breakdown.values()) if isinstance(breakdown, dict) else sum([v for v in breakdown.values()])
    html_table += f"<tr style='font-weight:bold; background-color:#e6f0fa;'><td style='padding:8px;'>{total_label}</td><td style='padding:8px;'>£{total_value:,.2f}</td></tr></tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)

# ------------------------------
# HOST MODE
# ------------------------------
if workshop_mode=="Host" and apply_pct:
    st.subheader("Monthly Cost Breakdown (Host)")
    breakdown, total = calculate_host_costs()
    display_gov_table(breakdown)

# ------------------------------
# PRODUCTION MODE
# ------------------------------
elif workshop_mode=="Production":
    num_items = st.number_input("How many items are produced?", min_value=1, value=1)
    items=[]
    for i in range(num_items):
        name = st.text_input(f"Item {i+1} name")
        workers = st.number_input(f"Prisoners needed to make 1 unit of {name}", min_value=1, value=1, key=f"workers_{i}")
        mins = st.number_input(f"Minutes to make 1 unit of {name}", min_value=0, value=0, key=f"mins_{i}")
        secs = st.number_input(f"Seconds to make 1 unit of {name}", min_value=0, max_value=59, value=0, key=f"secs_{i}")
        items.append((name,workers,mins,secs))
    if st.button("Calculate Item Costs"):
        results = calculate_production_items(items)
        st.subheader("Per-Unit Costs")
        display_gov_table(results,total_label="Unit Cost")

# ------------------------------
# EMAIL FUNCTIONALITY
# ------------------------------
def send_email(to_email, subject, body, sender_email, sender_password):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Email results if breakdown exists
if ('breakdown' in locals() or 'results' in locals()):
    st.subheader("Email Results")
    recipient_email = st.text_input("Recipient email address")
    sender_email = st.text_input("Your email address")
    sender_password = st.text_input("Your email password", type="password")
    if st.button("Send Email"):
        body=""
        if workshop_mode=="Host":
            for k,v in breakdown.items():
                body+=f"{k}: £{v:,.2f}\n"
            body+=f"Total Monthly Cost: £{sum(breakdown.values()):,.2f}\n"
        else:
            for k,v in results.items():
                body+=f"{k}: £{v}\n"
        try:
            send_email(recipient_email,"Prison Workshop Costing Results",body,sender_email,sender_password)
            st.success("Email sent successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")

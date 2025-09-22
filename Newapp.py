import streamlit as st
from pathlib import Path

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Prison Workshop Costing Tool", layout="wide")

# ------------------------------
# THEME: NFN blue header + GOV.UK green actions
# ------------------------------
NFN_BLUE = "#1D428A"
NFN_BLUE_DARK = "#153163"
GOV_GREEN = "#00703C"   # GOV.UK success/green
GOV_GREEN_DARK = "#005A30"
GOV_FOCUS = "#FFDD00"   # GOV.UK focus yellow

st.markdown(
    f"""
    <style>
        :root {{
            --nfn-blue: {NFN_BLUE};
            --nfn-blue-dark: {NFN_BLUE_DARK};
            --gov-green: {GOV_GREEN};
            --gov-green-dark: {GOV_GREEN_DARK};
            --gov-focus: {GOV_FOCUS};
        }}

        /* Header styling (keep NFN brand) */
        .nfn-title {{
            margin: 0; color: var(--nfn-blue);
            font-size: 1.6rem; font-weight: 700;
            padding-bottom: 4px;
            border-bottom: 3px solid var(--nfn-blue);
            margin-bottom: 8px;
        }}

        /* Primary buttons use GOV.UK green */
        .stButton > button[kind="primary"] {{
            background-color: var(--gov-green) !important;
            border: 1px solid var(--gov-green) !important;
            color: #fff !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: var(--gov-green-dark) !important;
            border-color: var(--gov-green-dark) !important;
        }}

        /* Add a GOV.UK-style focus treatment (yellow) */
        .stButton > button:focus,
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stSelectbox [data-baseweb="select"] div:focus,
        .stSlider [role="slider"]:focus {{
            outline: 3px solid var(--gov-focus) !important;
            outline-offset: 0 !important;
            box-shadow: 0 0 0 3px var(--gov-focus) inset !important;
        }}

        /* Secondary buttons keep NFN accent */
        .stButton > button:not([kind="primary"]) {{
            border: 1px solid var(--nfn-blue) !important;
            color: var(--nfn-blue) !important;
            background: #fff !important;
        }}
        .stButton > button:not([kind="primary"]):hover {{
            background: rgba(29,66,138,0.08) !important;
        }}

        /* Expanders with NFN blue headings */
        .st-expanderHeader, .stExpander > details > summary {{
            color: var(--nfn-blue) !important;
            font-weight: 600 !important;
        }}

        /* Links */
        a, a:visited {{ color: var(--nfn-blue); }}

        /* Read-only inputs look consistent */
        input[disabled], .stTextInput [disabled] {{
            color: #333 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# LOGO (URL -> local -> text link)
# ------------------------------
def render_header():
    """
    1) Sidebar-provided URL (direct image link)
    2) Local 'assets/nfn_logo.png'
    3) Text fallback (no crash)
    """
    logo_url = st.session_state.get("nfn_logo_url", "").strip()
    local_logo = Path("assets/nfn_logo.png")

    c_logo, c_title = st.columns([1, 8])
    with c_logo:
        shown = False
        if logo_url:
            try:
                st.image(logo_url, use_column_width=True)
                shown = True
            except Exception:
                shown = False
        if not shown and local_logo.exists():
            try:
                st.image(str(local_logo), use_column_width=True)
                shown = True
            except Exception:
                shown = False
        if not shown:
            st.markdown(
                '<div style="font-weight:700;"><a href="https://newfuturesnetwork.gov.uk/" target="_blank">New Futures Network</a></div>',
                unsafe_allow_html=True,
            )
    with c_title:
        st.markdown('<div class="nfn-title">Prison Workshop Costing Tool</div>', unsafe_allow_html=True)


with st.sidebar:
    st.header("Brand options")
    st.text_input(
        "Logo URL (optional – paste a direct image URL)",
        key="nfn_logo_url",
        placeholder="https://newfuturesnetwork.gov.uk/.../logo.png",
        help="Leave blank to use local file at assets/nfn_logo.png. Falls back to a text link if neither is available."
    )

render_header()

# ------------------------------
# CONSTANTS
# ------------------------------
ELECTRICITY_RATE = 0.25  # £/kWh
GAS_RATE = 0.07          # £/kWh
WATER_RATE = 2.0         # £/m³

workshop_energy = {
    "Empty/basic": {"electric": 40, "gas": 10, "water": 0.55},
    "Low energy": {"electric": 70, "gas": 20, "water": 0.55},
    "Medium energy": {"electric": 115, "gas": 40, "water": 0.55},
    "High energy": {"electric": 170, "gas": 70, "water": 0.55},
}

# ------------------------------
# PRISON → REGION mapping (auto-fill)
# ------------------------------
PRISON_TO_REGION = {
    "Altcourse": "National", "Ashfield": "National", "Askham Grange": "National", "Aylesbury": "National",
    "Bedford": "National", "Belmarsh": "Inner London", "Berwyn": "National", "Birmingham": "National",
    "Brinsford": "National", "Bristol": "National", "Brixton": "Inner London", "Bronzefield": "Outer London",
    "Buckley Hall": "National", "Bullingdon": "National", "Bure": "National", "Cardiff": "National",
    "Channings Wood": "National", "Chelmsford": "National", "Coldingley": "Outer London", "Cookham Wood": "National",
    "Dartmoor": "National", "Deerbolt": "National", "Doncaster": "National", "Dovegate": "National",
    "Downview": "Outer London", "Drake Hall": "National", "Durham": "National", "East Sutton Park": "National",
    "Eastwood Park": "National", "Elmley": "National", "Erlestoke": "National", "Exeter": "National",
    "Featherstone": "National", "Feltham A": "Outer London", "Feltham B": "Outer London", "Five Wells": "National",
    "Ford": "National", "Forest Bank": "National", "Fosse Way": "National", "Foston Hall": "National",
    "Frankland": "National", "Full Sutton": "National", "Garth": "National", "Gartree": "National",
    "Grendon": "National", "Guys Marsh": "National", "Hatfield": "National", "Haverigg": "National",
    "Hewell": "National", "High Down": "Outer London", "Highpoint": "National", "Hindley": "National",
    "Hollesley Bay": "National", "Holme House": "National", "Hull": "National", "Humber": "National",
    "Huntercombe": "National", "Isis": "Inner London", "Isle of Wight": "National", "Kirkham": "National",
    "Kirklevington Grange": "National", "Lancaster Farms": "National", "Leeds": "National", "Leicester": "National",
    "Lewes": "National", "Leyhill": "National", "Lincoln": "National", "Lindholme": "National", "Littlehey": "National",
    "Liverpool": "National", "Long Lartin": "National", "Low Newton": "National", "Lowdham Grange": "National",
    "Maidstone": "National", "Manchester": "National", "Moorland": "National", "Morton Hall": "National",
    "The Mount": "National", "New Hall": "National", "North Sea Camp": "National", "Northumberland": "National",
    "Norwich": "National", "Nottingham": "National", "Oakwood": "National", "Onley": "National", "Parc": "National",
    "Parc (YOI)": "National", "Pentonville": "Inner London", "Peterborough Female": "National",
    "Peterborough Male": "National", "Portland": "National", "Prescoed": "National", "Preston": "National",
    "Ranby": "National", "Risley": "National", "Rochester": "National", "Rye Hill": "National", "Send": "National",
    "Spring Hill": "National", "Stafford": "National", "Standford Hill": "National", "Stocken": "National",
    "Stoke Heath": "National", "Styal": "National", "Sudbury": "National", "Swaleside": "National", "Swansea": "National",
    "Swinfen Hall": "National", "Thameside": "Inner London", "Thorn Cross": "National", "Usk": "National",
    "Verne": "National", "Wakefield": "National", "Wandsworth": "Inner London", "Warren Hill": "National",
    "Wayland": "National", "Wealstun": "National", "Werrington": "National", "Wetherby": "National",
    "Whatton": "National", "Whitemoor": "National", "Winchester": "National", "Woodhill": "National",
    "Wormwood Scrubs": "Inner London", "Wymott": "National",
}

# ------------------------------
# RESET
# ------------------------------
if st.button("Reset App"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()  # fallback for older Streamlit

# ------------------------------
# BASE INPUTS (labels exactly as requested)
# ------------------------------

# Prison Name (dropdown) + auto Region (read-only)
prisons_sorted = ["Select"] + sorted(PRISON_TO_REGION.keys())
prison_choice = st.selectbox("Prison Name", prisons_sorted, index=0)

if prison_choice == "Select":
    region = "Select"
else:
    region = PRISON_TO_REGION.get(prison_choice, "Select")

st.text_input("Region", value=("" if region == "Select" else region), disabled=True)

# "I want to quote for" and "Customer Name"
customer_type = st.selectbox("I want to quote for", ["Select", "Commercial", "Another Government Department"])
customer_name = st.text_input("Customer Name")

# Contract + size (sq ft categories)
workshop_mode = st.selectbox("Contract type?", ["Select", "Host", "Production"])

SIZE_LABELS = [
    "Select",
    "Small (~2,500 ft², ~50×50 ft)",
    "Medium (~5,000 ft²)",
    "Large (~10,000 ft²)",
    "Enter dimensions in ft",
]
size_map = {
    "Small (~2,500 ft², ~50×50 ft)": 2500,
    "Medium (~5,000 ft²)": 5000,
    "Large (~10,000 ft²)": 10000,
}
workshop_size = st.selectbox("Workshop size (sq ft)?", SIZE_LABELS)

# Area
if workshop_size == "Enter dimensions in ft":
    width = st.number_input("Width (ft)", min_value=0.0, format="%.2f", key="width")
    length = st.number_input("Length (ft)", min_value=0.0, format="%.2f", key="length")
    area = width * length
    st.markdown(f"**Calculated area:** {area:,.0f} ft²")
else:
    area = size_map.get(workshop_size, 0)

workshop_type = st.selectbox("Workshop type?", ["Select"] + list(workshop_energy.keys()))
workshop_hours = st.number_input("How many hours per week is it open?", min_value=0.0, format="%.2f")

num_prisoners = st.number_input("How many prisoners employed?", min_value=0)
prisoner_salary = st.number_input("Prisoner salary per week (£)", min_value=0.0, format="%.2f")

num_supervisors = st.number_input("How many supervisors?", min_value=0)
customer_covers_supervisors = st.checkbox("Customer provides supervisor(s)?")

supervisor_salaries = []
recommended_pct = 0
if not customer_covers_supervisors:
    for i in range(int(num_supervisors)):
        sup_salary = st.number_input(
            f"Supervisor {i+1} annual salary (£)", min_value=0.0, format="%.2f", key=f"sup_salary_{i}"
        )
        supervisor_salaries.append(sup_salary)
    contracts = st.number_input("How many contracts do these supervisors oversee?", min_value=1, value=1)
    recommended_pct = round((workshop_hours / 37.5) * (1 / contracts) * 100, 1) if contracts and workshop_hours >= 0 else 0
    st.subheader("Supervisor Time Allocation")
    st.info(f"Recommended: {recommended_pct}%")
    chosen_pct = st.slider("Adjust supervisor % allocation", 0, 100, int(recommended_pct), key="chosen_pct")
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
    if prison_choice == "Select":
        errors.append("Select prison")
    if region == "Select":
        errors.append("Region could not be derived from prison selection")
    if customer_type == "Select":
        errors.append("Select customer type")
    if not str(customer_name).strip():
        errors.append("Enter customer name")
    if workshop_mode == "Select":
        errors.append("Select contract type")
    if workshop_size == "Select":
        errors.append("Select workshop size")
    if workshop_type == "Select":
        errors.append("Select workshop type")
    if workshop_hours <= 0:
        errors.append("Enter hours open")
    if num_prisoners <= 0:
        errors.append("Enter prisoners employed")
    if prisoner_salary <= 0:
        errors.append("Enter prisoner salary")
    if not customer_covers_supervisors:
        if num_supervisors <= 0:
            errors.append("Enter number of supervisors")
        if any(s <= 0 for s in supervisor_salaries):
            errors.append("Enter all supervisor salaries")
        if chosen_pct < recommended_pct and not str(reason_for_low_pct).strip():
            errors.append("Provide reason for low supervisor %")
    return errors

# ------------------------------
# HOST COSTS
# ------------------------------
def calculate_host_costs():
    breakdown = {}
    breakdown["Prisoner wages (monthly)"] = num_prisoners * prisoner_salary * (52/12)
    supervisor_cost = 0
    if not customer_covers_supervisors:
        supervisor_cost = sum([(s/12) * (chosen_pct / 100) for s in supervisor_salaries])
        breakdown["Supervisors (monthly)"] = supervisor_cost
    if workshop_type in workshop_energy:
        e = workshop_energy[workshop_type]
        hours_factor = workshop_hours / 37.5 if 37.5 else 1
        breakdown["Electricity (monthly est)"] = area * (e["electric"]/12) * ELECTRICITY_RATE * hours_factor
        breakdown["Gas (monthly est)"] = area * (e["gas"]/12) * GAS_RATE * hours_factor
        breakdown["Water (monthly est)"] = area * (e["water"]/12) * WATER_RATE * hours_factor
    breakdown["Administration (monthly)"] = 150
    breakdown["Depreciation/Maintenance (monthly)"] = area * 0.5
    region_mult = {"National": 1.0, "Outer London": 1.1, "Inner London": 1.2}.get(region, 1.0)
    breakdown["Regional uplift (monthly)"] = sum(breakdown.values()) * (region_mult - 1)
    breakdown["Development charge (monthly)"] = supervisor_cost * dev_charge if customer_type == "Commercial" else 0
    return breakdown, sum(breakdown.values())

# ------------------------------
# PRODUCTION CALCULATIONS (WEEKLY BASIS)
# ------------------------------
def calculate_production(items):
    """
    Returns a list of dicts for each item:
      - Item: name
      - Unit Cost: weekly cost per unit (None if capacity zero)
      - MinUnitsWeek: maximum units per week (float)
    """
    results = []
    sup_weekly = sum([(s/52) * (chosen_pct / 100) for s in supervisor_salaries]) if not customer_covers_supervisors else 0.0
    prisoner_weekly = num_prisoners * prisoner_salary  # prisoner_salary is per week
    total_weekly_cost = prisoner_weekly + sup_weekly

    for item in items:
        name = item.get("name", "").strip() or "(Unnamed)"
        mins_per_unit = float(item.get("minutes", 0))
        prisoners_required = int(item.get("required", 1))
        prisoners_assigned = int(item.get("assigned", 0))

        if mins_per_unit <= 0 or prisoners_required <= 0 or prisoners_assigned <= 0 or workshop_hours <= 0:
            capacity_week = 0.0
            unit_cost = None
        else:
            available_mins_week = prisoners_assigned * workshop_hours * 60.0
            minutes_per_unit_total = mins_per_unit * prisoners_required
            capacity_week = available_mins_week / minutes_per_unit_total if minutes_per_unit_total > 0 else 0.0
            unit_cost = (total_weekly_cost / capacity_week) if capacity_week > 0 else None

        results.append({
            "Item": name,
            "Unit Cost": unit_cost,
            "MinUnitsWeek": capacity_week,
        })
    return results

# ------------------------------
# DISPLAY HELPER
# ------------------------------
def display_table(breakdown, total_label="Total Monthly Cost"):
    html = "<table><thead><tr><th>Cost Item</th><th>Amount (£)</th></tr></thead><tbody>"
    for k, v in breakdown.items():
        html += f"<tr><td>{k}</td><td>£{v:,.2f}</td></tr>"
    total = sum(breakdown.values())
    html += f"<tr class='total-row'><td>{total_label}</td><td>£{total:,.2f}</td></tr></tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# ------------------------------
# UI: Host vs Production
# ------------------------------
errors = validate_inputs()

if workshop_mode == "Host":
    if st.button("Generate Costs", type="primary"):
        if errors:
            st.error("Fix errors:\n- " + "\n- ".join(errors))
        else:
            st.subheader("Host Contract Costs")
            breakdown, _ = calculate_host_costs()
            display_table(breakdown)

elif workshop_mode == "Production":
    st.subheader("Production Contract Costs")

    num_items = st.number_input("Number of items produced?", min_value=1, value=1, step=1, key="num_items_prod")
    items = []
    for i in range(int(num_items)):
        with st.expander(f"Item {i+1} details", expanded=(i == 0)):
            name = st.text_input(f"Item {i+1} Name", key=f"name_{i}")
            prisoners_required = st.number_input(
                f"Prisoners required to make 1 item (Item {i+1})", min_value=1, value=1, step=1, key=f"req_{i}"
            )
            minutes_per_item = st.number_input(
                f"How many minutes to make 1 item (Item {i+1})", min_value=1.0, value=10.0, format="%.2f", key=f"mins_{i}"
            )
            prisoners_assigned = st.number_input(
                f"How many prisoners work solely on this item (Item {i+1})",
                min_value=0, max_value=int(num_prisoners), value=0, step=1, key=f"assigned_{i}"
            )
            items.append({
                "name": name,
                "required": int(prisoners_required),
                "minutes": float(minutes_per_item),
                "assigned": int(prisoners_assigned)
            })

    if errors:
        st.error("Fix errors before production calculations:\n- " + "\n- ".join(errors))
    else:
        results = calculate_production(items)

        for i, r in enumerate(results):
            st.markdown(f"### {r['Item']}")
            if r["Unit Cost"] is None:
                st.write("- Unit Cost (£): **N/A** (insufficient capacity or missing inputs)")
            else:
                st.write(f"- Unit Cost (£): £{r['Unit Cost']:.2f}")

            cap = r["MinUnitsWeek"]
            if cap <= 0:
                st.write("- Units/week (capacity): **0** — check minutes/prisoners assigned/workshop hours")
            else:
                st.write(f"- Units/week (capacity): {cap:.0f}")

            percent = st.slider(f"Output % for Item {i+1}", min_value=0, max_value=100, value=100, key=f"percent_{i}")
            adjusted_units = int(round(cap * (percent / 100.0))) if cap > 0 else 0
            st.write(f"- Adjusted units/week at {percent}% output: {adjusted_units}")

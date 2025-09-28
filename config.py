# config.py

# -----------------------------
# Global constants
# -----------------------------
DAYS_PER_MONTH = 365.0 / 12.0   # ≈30.42
FT2_TO_M2 = 0.092903
BASE_HOURS_PER_WEEK = 27.0      # baseline for scaling energy & maintenance

# -----------------------------
# Prison → Region map
# -----------------------------
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
    "Lewes": "National", "Leyhill": "National", "Lincoln": "National", "Lindholme": "National",
    "Littlehey": "National", "Liverpool": "National", "Long Lartin": "National", "Low Newton": "National",
    "Lowdham Grange": "National", "Maidstone": "National", "Manchester": "National", "Moorland": "National",
    "Morton Hall": "National", "The Mount": "National", "New Hall": "National", "North Sea Camp": "National",
    "Northumberland": "National", "Norwich": "National", "Nottingham": "National", "Oakwood": "National",
    "Onley": "National", "Parc": "National", "Parc (YOI)": "National", "Pentonville": "Inner London",
    "Peterborough Female": "National", "Peterborough Male": "National", "Portland": "National", "Prescoed": "National",
    "Preston": "National", "Ranby": "National", "Risley": "National", "Rochester": "National",
    "Rye Hill": "National", "Send": "National", "Spring Hill": "National", "Stafford": "National",
    "Standford Hill": "National", "Stocken": "National", "Stoke Heath": "National", "Styal": "National",
    "Sudbury": "National", "Swaleside": "National", "Swansea": "National", "Swinfen Hall": "National",
    "Thameside": "Inner London", "Thorn Cross": "National", "Usk": "National", "Verne": "National",
    "Wakefield": "National", "Wandsworth": "Inner London", "Warren Hill": "National", "Wayland": "National",
    "Wealstun": "National", "Werrington": "National", "Wetherby": "National", "Whatton": "National",
    "Whitemoor": "National", "Winchester": "National", "Woodhill": "Inner London", "Wormwood Scrubs": "Inner London",
    "Wymott": "National",
}

# -----------------------------
# Regional uplift multipliers
# -----------------------------
REGION_UPLIFT = {
    "Inner London": 1.15,
    "Outer London": 1.08,
    "National": 1.0,
}

# -----------------------------
# Instructor pay bands
# -----------------------------
SUPERVISOR_PAY = {
    "Inner London": [
        {"title": "Production Instructor: Band 3", "avg_total": 49203},
        {"title": "Specialist Instructor: Band 4", "avg_total": 55632},
    ],
    "Outer London": [
        {"title": "Prison Officer Specialist - Instructor: Band 4", "avg_total": 69584},
        {"title": "Production Instructor: Band 3", "avg_total": 45856},
    ],
    "National": [
        {"title": "Prison Officer Specialist - Instructor: Band 4", "avg_total": 48969},
        {"title": "Production Instructor: Band 3", "avg_total": 42248},
    ],
}

# -----------------------------
# Tariff bands (baseline — no uplift)
# -----------------------------
TARIFF_BANDS = {
    "low": {
        "intensity_per_year": {
            "elec_kwh_per_m2": 65,
            "gas_kwh_per_m2": 80,
            "water_m3_per_employee": 15,
            "maint_gbp_per_m2": 8,
        },
        "rates": {
            "elec_unit": 0.2597,
            "elec_daily": 0.487,
            "gas_unit": 0.0629,
            "gas_daily": 0.3403,
            "water_unit": 1.30,
            "admin_monthly": 150.0,
        },
    },
    "medium": {
        "intensity_per_year": {
            "elec_kwh_per_m2": 110,
            "gas_kwh_per_m2": 120,
            "water_m3_per_employee": 15,
            "maint_gbp_per_m2": 12,
        },
        "rates": {
            "elec_unit": 0.2597,
            "elec_daily": 0.487,
            "gas_unit": 0.0629,
            "gas_daily": 0.3403,
            "water_unit": 1.30,
            "admin_monthly": 150.0,
        },
    },
    "high": {
        "intensity_per_year": {
            "elec_kwh_per_m2": 160,
            "gas_kwh_per_m2": 180,
            "water_m3_per_employee": 15,
            "maint_gbp_per_m2": 15,
        },
        "rates": {
            "elec_unit": 0.2597,
            "elec_daily": 0.487,
            "gas_unit": 0.0629,
            "gas_daily": 0.3403,
            "water_unit": 1.30,
            "admin_monthly": 150.0,
        },
    },
}
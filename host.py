# host.py
# Host monthly breakdown; Development charge uses same question as Production.
from typing import List, Dict, Tuple
import pandas as pd
import streamlit as st
from config import CFG
from production import monthly_energy_costs, monthly_water_costs, monthly_maintenance

def generate_host_quote(
    *,
    workshop_hours: float,
    area_m2: float,
    usage_key: str,
    num_prisoners: int,
    prisoner_salary: float,
    num_supervisors: int,
    customer_covers_supervisors: bool,
    supervisor_salaries: List[float],
    effective_pct: float,
    customer_type: str,
    apply_vat: bool,          # kept in signature for compatibility; we'll pass True
    vat_rate: float,          # we will pass 20.0
    dev_rate: float,          # 0..0.2 (or your chosen scale)
) -> Tuple[pd.DataFrame, Dict]:
    breakdown: Dict[str, float] = {}
    breakdown["Prisoner wages"] = float(num_prisoners) * float(prisoner_salary) * (52.0 / 12.0)

    instructor_cost = 0.0
    if not customer_covers_supervisors:
        instructor_cost = sum((s / 12.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)
    breakdown["Instructors"] = instructor_cost

    elec_m, gas_m = monthly_energy_costs(workshop_hours, area_m2, usage_key)
    water_m = monthly_water_costs(num_prisoners, num_supervisors, customer_covers_supervisors, usage_key)
    maint_m = monthly_maintenance(workshop_hours, area_m2, usage_key)
    admin_m = float(st.session_state.get("admin_monthly", CFG.DEFAULT_ADMIN_MONTHLY))

    breakdown["Electricity (estimated)"] = elec_m
    breakdown["Gas (estimated)"]        = gas_m
    breakdown["Water (estimated)"]      = water_m
    breakdown["Administration"]         = admin_m
    breakdown["Depreciation/Maintenance (estimated)"] = maint_m

    # Development charge applies only to Commercial (as per your rule)
    overheads_subtotal = elec_m + gas_m + water_m + admin_m + maint_m
    breakdown["Development charge (applied)"] = overheads_subtotal * (float(dev_rate) if customer_type == "Commercial" else 0.0)

    subtotal = sum(breakdown.values())

    # === VAT: always apply at 20% (no checkbox) ===
    vat_amount = subtotal * (float(vat_rate) / 100.0)

    grand_total = subtotal + vat_amount

    rows = list(breakdown.items()) + [
        ("Subtotal", subtotal),
        (f"VAT ({float(vat_rate):.1f}%)", vat_amount),
        ("Grand Total (£/month)", grand_total),
    ]
    host_df = pd.DataFrame(rows, columns=["Item", "Amount (£)"])

    ctx = {
        "overheads_subtotal": overheads_subtotal,
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "grand_total": grand_total,
    }
    return host_df, ctx

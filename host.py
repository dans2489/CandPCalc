# host.py
# Host cost breakdown (monthly) using shared overhead functions from production.py

from __future__ import annotations

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
    apply_vat: bool,
    vat_rate: float,
    dev_applied_rate: float,  # <-- passed from UI (same question as Production)
) -> Tuple[pd.DataFrame, Dict]:
    """
    Builds a monthly Host breakdown DataFrame and returns (df, context_dict).
    Standing charges are not apportioned; variable energy and maintenance are apportioned by hours.
    Includes Development charge per 'employment support' selection (Commercial only).
    """
    breakdown = {}

    # Prisoner wages: weekly to monthly
    breakdown["Prisoner wages"] = num_prisoners * prisoner_salary * (52.0 / 12.0)

    # Instructors (if not provided by customer)
    instructor_cost = 0.0
    if not customer_covers_supervisors:
        instructor_cost = sum((s / 12.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)
    breakdown["Instructors"] = instructor_cost

    # Overheads
    elec_m, gas_m = monthly_energy_costs(workshop_hours, area_m2, usage_key)
    water_m = monthly_water_costs(num_prisoners, num_supervisors, customer_covers_supervisors, usage_key)
    maint_m = monthly_maintenance(workshop_hours, area_m2, usage_key)
    admin_m = float(st.session_state.get("admin_monthly", CFG.DEFAULT_ADMIN_MONTHLY))

    breakdown["Electricity (estimated)"] = elec_m
    breakdown["Gas (estimated)"] = gas_m
    breakdown["Water (estimated)"] = water_m
    breakdown["Administration"] = admin_m
    breakdown["Depreciation/Maintenance (estimated)"] = maint_m

    overheads_subtotal = elec_m + gas_m + water_m + admin_m + maint_m

    # Development charge (Commercial only) — same logic as Production
    dev_applied_m = overheads_subtotal * (float(dev_applied_rate) if customer_type == "Commercial" else 0.0)
    breakdown["Development charge (applied)"] = dev_applied_m

    subtotal = sum(breakdown.values())
    vat_amount = (subtotal * (float(vat_rate) / 100.0)) if (customer_type == "Commercial" and apply_vat) else 0.0
    grand_total = subtotal + vat_amount

    rows = list(breakdown.items()) + [
        ("Subtotal", subtotal),
        ((f"VAT ({float(vat_rate):.1f}%)") if (customer_type == "Commercial" and apply_vat) else "VAT (0.0%)", vat_amount),
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

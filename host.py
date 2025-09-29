# host.py
# Pure calculation for Host breakdown.

from __future__ import annotations
from typing import Dict, List, Tuple

def build_host_breakdown(
    num_prisoners: int,
    prisoner_salary: float,
    supervisor_salaries: List[float],
    effective_pct: int,
    elec_m: float,
    gas_m: float,
    water_m: float,
    admin_m: float,
    maint_m: float,
    customer_type: str,
    apply_vat: bool,
    vat_rate: float,
) -> Tuple[list[tuple[str, float]], float, float, float]:
    """
    Returns (rows list[(label, value)], subtotal, vat_amount, grand_total)
    """
    breakdown: Dict[str, float] = {}
    breakdown["Prisoner wages"] = float(num_prisoners) * float(prisoner_salary) * (52.0 / 12.0)

    instructor_cost = 0.0
    if supervisor_salaries:
        instructor_cost = sum((s / 12.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)
    breakdown["Instructors"] = instructor_cost

    breakdown["Electricity (estimated)"] = float(elec_m)
    breakdown["Gas (estimated)"] = float(gas_m)
    breakdown["Water (estimated)"] = float(water_m)
    breakdown["Administration"] = float(admin_m)
    breakdown["Depreciation/Maintenance (estimated)"] = float(maint_m)

    # Development charge (simple rule – keep as-is or extend)
    if customer_type == "Commercial":
        dev_applied_rate = 0.20
        breakdown["Development charge (applied)"] = (
            (elec_m + gas_m + water_m + admin_m + maint_m) * dev_applied_rate
        )
    else:
        breakdown["Development charge (applied)"] = 0.0

    subtotal = sum(breakdown.values())
    vat_amount = (subtotal * (float(vat_rate) / 100.0)) if (customer_type == "Commercial" and apply_vat) else 0.0
    grand_total = subtotal + vat_amount

    rows = list(breakdown.items()) + [
        ("Subtotal", subtotal),
        (f"VAT ({float(vat_rate):.1f}%)" if (customer_type == "Commercial" and apply_vat) else "VAT (0.0%)", vat_amount),
        ("Grand Total (£/month)", grand_total),
    ]
    return rows, subtotal, vat_amount, grand_total

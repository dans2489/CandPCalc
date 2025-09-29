# production.py
# Pure calculations + constraints for Contractual and Ad‑hoc flows.
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil, floor
from typing import List, Dict, Tuple

# ---------- Shared helpers ----------

def labour_minutes_budget(num_pris: int, hours: float) -> float:
    """Total weekly labour minutes available."""
    return max(0.0, float(num_pris) * float(hours) * 60.0)

def working_days_between(start: date, end: date) -> int:
    """Inclusive Mon–Fri working days."""
    if end < start:
        return 0
    days, d = 0, start
    while d <= end:
        if d.weekday() < 5:
            days += 1
        d += timedelta(days=1)
    return days

# ---------- Contractual ----------

def contractual_enforce_and_calculate(
    items: List[Dict],
    output_pct: int,
    workshop_hours: float,
    num_prisoners: int,
    prisoner_salary: float,
    supervisor_salaries: List[float],
    effective_pct: int,           # instructor allocation %
    overheads_weekly: float,
    customer_type: str,
    apply_vat: bool,
    vat_rate: float,
) -> Tuple[List[str], List[Dict], float, float]:
    """
    items: [{name, required:int, minutes:float, assigned:int}, ...]
    Returns (errors, results, used_minutes_raw, used_minutes_planned)
    """
    errors: List[str] = []
    output_scale = float(output_pct) / 100.0

    # 1) Prisoner assignment cannot exceed total prisoners
    total_assigned = sum(int(it.get("assigned", 0)) for it in items)
    if total_assigned > int(num_prisoners):
        errors.append(
            f"Prisoners assigned across items ({total_assigned}) exceed total prisoners ({int(num_prisoners)})."
        )

    # 2) Minutes capacity constraints
    used_minutes_raw = total_assigned * float(workshop_hours) * 60.0
    used_minutes_planned = used_minutes_raw * output_scale
    budget_minutes = labour_minutes_budget(num_prisoners, workshop_hours)
    if used_minutes_planned > budget_minutes:
        errors.append(
            "Planned used minutes exceed the available weekly labour minutes. "
            "Adjust assignments, add prisoners, increase hours, or lower Output%."
        )

    # Early exit on hard violations
    if errors:
        return errors, [], used_minutes_raw, used_minutes_planned

    # 3) Costing
    # Weekly instructor total (apportioned by effective_pct)
    inst_weekly_total = sum((s / 52.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)

    # Denominator for shares (assigned labour minutes at 100%)
    denom = sum(int(it.get("assigned", 0)) * float(workshop_hours) * 60.0 for it in items)
    results: List[Dict] = []
    for idx, it in enumerate(items):
        name = (it.get("name", "") or "").strip() or f"Item {idx+1}"
        mins_per_unit = float(it.get("minutes", 0.0))
        pris_req     = int(it.get("required", 1))
        pris_ass     = int(it.get("assigned", 0))

        # Capacity @ 100%
        if pris_ass > 0 and mins_per_unit > 0 and pris_req > 0 and workshop_hours > 0:
            cap_100 = (pris_ass * float(workshop_hours) * 60.0) / (mins_per_unit * pris_req)
        else:
            cap_100 = 0.0

        units_week = cap_100 * output_scale

        share = ((pris_ass * float(workshop_hours) * 60.0) / denom) if denom > 0 else 0.0

        prisoner_weekly_item   = pris_ass * float(prisoner_salary)
        inst_weekly_item       = inst_weekly_total * share
        overheads_weekly_item  = overheads_weekly * share
        weekly_cost_item       = prisoner_weekly_item + inst_weekly_item + overheads_weekly_item

        unit_cost_ex_vat = (weekly_cost_item / units_week) if units_week > 0 else None
        unit_price_ex_vat = unit_cost_ex_vat
        if unit_price_ex_vat is not None and (customer_type == "Commercial" and apply_vat):
            unit_price_inc_vat = unit_price_ex_vat * (1.0 + (float(vat_rate) / 100.0))
        else:
            unit_price_inc_vat = unit_price_ex_vat

        results.append({
            "Item": name,
            "Output %": int(output_pct),
            "Units/week": 0 if units_week <= 0 else int(round(units_week)),
            "Unit Cost (£)": unit_cost_ex_vat,
            "Unit Price ex VAT (£)": unit_price_ex_vat,
            "Unit Price inc VAT (£)": unit_price_inc_vat,
        })

    # Defensive: units minutes vs planned minutes
    units_minutes = 0.0
    for r, it in zip(results, items):
        units = r.get("Units/week", 0) or 0
        units_minutes += float(units) * float(it["minutes"]) * float(it["required"])
    if units_minutes > used_minutes_planned + 1e-6:
        errors.append("Total minutes implied by units exceed planned labour minutes. Re-check Output% and timings.")

    return errors, results, used_minutes_raw, used_minutes_planned

# ---------- Ad-hoc ----------

@dataclass
class AdhocLine:
    name: str
    units: int
    deadline: date
    pris_per_item: int
    mins_per_item: float

def adhoc_enforce_and_calculate(
    lines: List[AdhocLine],
    output_pct: int,
    workshop_hours: float,
    num_prisoners: int,
    prisoner_salary: float,
    supervisor_salaries: List[float],
    effective_pct: int,
    overheads_weekly: float,
    customer_type: str,
    apply_vat: bool,
    vat_rate: float,
    today: date | None = None,
) -> Tuple[List[str], List[Dict], Dict]:
    """
    Returns (errors, per_line_results, summary)
      - errors: list of blocking errors (empty when OK)
      - per_line_results: [{name, units, unit_cost_ex_vat, unit_cost_inc_vat,
                            line_total_ex_vat, line_total_inc_vat, wd_available, wd_needed_line_alone}]
      - summary: {
            total_ex_vat, total_inc_vat, feasible: bool,
            wd_needed_all, earliest_wd_available,
            extra_prisoners_needed, suggestions: {max_units_per_line: [...]}
        }
    """
    errors: List[str] = []
    if today is None:
        today = date.today()

    output_scale = float(output_pct) / 100.0
    hours_per_day = float(workshop_hours) / 5.0
    current_daily_capacity = float(num_prisoners) * hours_per_day * 60.0 * output_scale

    # Weekly costing → cost per minute (like before)
    inst_weekly_total = sum((s / 52.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)
    prisoners_weekly_cost = float(num_prisoners) * float(prisoner_salary)
    weekly_cost_total = prisoners_weekly_cost + inst_weekly_total + float(overheads_weekly)

    minutes_per_week_capacity = max(1e-9, float(num_prisoners) * float(workshop_hours) * 60.0 * output_scale)
    cost_per_minute = weekly_cost_total / minutes_per_week_capacity

    # Build per-line results and feasibility data
    per_line = []
    total_job_minutes = 0.0
    earliest_wd_available = None

    for ln in lines:
        mins_per_unit = float(ln.mins_per_item) * float(ln.pris_per_item)
        if mins_per_unit <= 0:
            errors.append(f"{ln.name}: minutes per unit must be > 0.")
        line_minutes = ln.units * mins_per_unit
        total_job_minutes += line_minutes

        wd_available = working_days_between(today, ln.deadline)
        if earliest_wd_available is None or wd_available < earliest_wd_available:
            earliest_wd_available = wd_available

        unit_cost_ex_vat = cost_per_minute * mins_per_unit
        if customer_type == "Commercial" and apply_vat:
            unit_cost_inc_vat = unit_cost_ex_vat * (1.0 + (float(vat_rate)/100.0))
        else:
            unit_cost_inc_vat = unit_cost_ex_vat

        wd_needed_line_alone = ceil(line_minutes / current_daily_capacity) if current_daily_capacity > 0 else float("inf")

        per_line.append({
            "name": ln.name,
            "units": ln.units,
            "unit_cost_ex_vat": unit_cost_ex_vat,
            "unit_cost_inc_vat": unit_cost_inc_vat,
            "line_total_ex_vat": unit_cost_ex_vat * ln.units,
            "line_total_inc_vat": unit_cost_inc_vat * ln.units,
            "wd_available": wd_available,
            "wd_needed_line_alone": wd_needed_line_alone,
            "mins_per_unit": mins_per_unit,
        })

    if errors:
        return errors, [], {}

    earliest_wd_available = earliest_wd_available or 0
    capacity_to_earliest = current_daily_capacity * earliest_wd_available

    # HARD CONSTRAINT: cannot exceed capacity by earliest deadline
    suggestions = {}
    feasible = True
    if total_job_minutes > capacity_to_earliest + 1e-6:
        feasible = False

        # Suggest max feasible units per line by scaling proportionally
        if total_job_minutes > 0:
            scale = capacity_to_earliest / total_job_minutes
            max_units = []
            for p in per_line:
                suggested = int(floor(p["units"] * scale))
                max_units.append(max(0, suggested))
            suggestions["max_units_per_line"] = max_units

        # Extra prisoners needed to hit earliest deadline
        if earliest_wd_available > 0 and hours_per_day > 0:
            required_minutes_per_day = total_job_minutes / earliest_wd_available
            deficit_per_day = max(0.0, required_minutes_per_day - current_daily_capacity)
            per_prisoner_per_day = hours_per_day * 60.0 * output_scale
            extra = int(ceil(deficit_per_day / per_prisoner_per_day)) if per_prisoner_per_day > 0 else 0
        else:
            extra = 0
    else:
        extra = 0

    # Totals
    total_ex_vat = sum(p["line_total_ex_vat"] for p in per_line)
    total_inc_vat = sum(p["line_total_inc_vat"] for p in per_line)

    # Overall wd needed
    if current_daily_capacity > 0:
        wd_needed_all = ceil(total_job_minutes / current_daily_capacity)
    else:
        wd_needed_all = float("inf")

    summary = {
        "total_ex_vat": total_ex_vat,
        "total_inc_vat": total_inc_vat,
        "feasible": feasible,
        "wd_needed_all": wd_needed_all,
        "earliest_wd_available": earliest_wd_available,
        "extra_prisoners_needed": extra,
        "suggestions": suggestions
    }

    # If not feasible, return error to block calculation (hard constraint)
    if not feasible:
        errors.append(
            "Requested Ad‑hoc units exceed capacity by the earliest deadline. "
            "Reduce units, add prisoners, increase hours, or lower Output%."
        )
        return errors, [], summary

    # Strip helper field before returning
    for p in per_line:
        p.pop("mins_per_unit", None)

    return [], per_line, summary

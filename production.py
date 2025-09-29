# production.py
# Shared overhead calculations + Production (Contractual & Ad‑hoc) calculators.

from __future__ import annotations

from typing import List, Dict, Tuple
import math
from datetime import date, timedelta

import streamlit as st

from config import CFG, hours_scale
from tariff import TARIFF_BANDS


# -----------------------------
# Overhead / costs (shared)
# -----------------------------
def monthly_energy_costs(workshop_hours: float, area_m2: float, usage_key: str) -> Tuple[float, float]:
    """
    Electricity & Gas monthly cost for the workshop.
    - Variable energy (kWh) apportioned by hours (hours_scale).
    - Standing (daily) charges are NOT apportioned by hours.
    """
    band = TARIFF_BANDS[usage_key]
    elec_kwh_y = band["intensity_per_year"]["elec_kwh_per_m2"] * (area_m2 or 0.0)
    gas_kwh_y  = band["intensity_per_year"]["gas_kwh_per_m2"]  * (area_m2 or 0.0)

    hscale = hours_scale(workshop_hours)  # baseline hidden in config

    elec_unit = float(st.session_state["electricity_rate"])
    gas_unit  = float(st.session_state["gas_rate"])
    elec_daily = float(st.session_state["elec_daily"])
    gas_daily  = float(st.session_state["gas_daily"])

    elec_var_m = (elec_kwh_y / 12.0) * elec_unit * hscale
    gas_var_m  = (gas_kwh_y  / 12.0) * gas_unit  * hscale

    elec_fix_m = elec_daily * CFG.DAYS_PER_MONTH  # not apportioned
    gas_fix_m  = gas_daily  * CFG.DAYS_PER_MONTH  # not apportioned

    return elec_var_m + elec_fix_m, gas_var_m + gas_fix_m


def monthly_water_costs(num_prisoners: int, num_supervisors: int, customer_covers_supervisors: bool, usage_key: str) -> float:
    band = TARIFF_BANDS[usage_key]
    persons = num_prisoners + (0 if customer_covers_supervisors else num_supervisors)
    m3_per_year = persons * band["intensity_per_year"]["water_m3_per_employee"]
    return (m3_per_year / 12.0) * float(st.session_state["water_rate"])


def monthly_maintenance(workshop_hours: float, area_m2: float, usage_key: str) -> float:
    """
    Maintenance apportioned by hours (per your requirement).
    """
    hscale = hours_scale(workshop_hours) if CFG.APPORTION_MAINTENANCE else 1.0
    method = st.session_state.get("maint_method", "£/m² per year")

    if str(method).startswith("£/m² per year"):
        rate = st.session_state.get("maint_rate_per_m2_y", TARIFF_BANDS[usage_key]["intensity_per_year"]["maint_gbp_per_m2"])
        base_m = (float(rate) * (area_m2 or 0.0)) / 12.0
    elif method == "Set a fixed monthly amount":
        base_m = float(st.session_state.get("maint_monthly", 0.0))
    else:  # % of reinstatement value
        reinstate_val = float(st.session_state.get("reinstate_val", 0.0))
        pct = float(st.session_state.get("reinstate_pct", 0.0))
        base_m = (reinstate_val * (pct / 100.0)) / 12.0

    return base_m * hscale


def weekly_overheads_total(
    workshop_hours: float,
    area_m2: float,
    usage_key: str,
    num_prisoners: int,
    num_supervisors: int,
    customer_covers_supervisors: bool,
) -> Tuple[float, dict]:
    """
    Returns (weekly_overheads_total_gbp, detail_breakdown_dict).
    Includes Electricity, Gas, Water, Admin, Maintenance.
    """
    elec_m, gas_m = monthly_energy_costs(workshop_hours, area_m2, usage_key)
    water_m = monthly_water_costs(num_prisoners, num_supervisors, customer_covers_supervisors, usage_key)
    maint_m = monthly_maintenance(workshop_hours, area_m2, usage_key)
    admin_m = float(st.session_state.get("admin_monthly", CFG.DEFAULT_ADMIN_MONTHLY))

    overheads_m = elec_m + gas_m + water_m + admin_m + maint_m
    detail = {
        "Electricity (estimated)": elec_m,
        "Gas (estimated)": gas_m,
        "Water (estimated)": water_m,
        "Administration": admin_m,
        "Depreciation/Maintenance (estimated)": maint_m,
    }
    weekly = overheads_m * 12.0 / 52.0
    return weekly, detail


# -----------------------------
# Production helpers
# -----------------------------
def labour_minutes_budget(num_pris: int, hours: float) -> float:
    return max(0.0, float(num_pris) * float(hours) * 60.0)


def item_capacity_100(prisoners_assigned: int, minutes_per_item: float, prisoners_required: int, hours: float) -> float:
    if prisoners_assigned <= 0 or minutes_per_item <= 0 or prisoners_required <= 0 or hours <= 0:
        return 0.0
    return (prisoners_assigned * hours * 60.0) / (minutes_per_item * prisoners_required)


# -----------------------------
# Contractual calculator (Development charge INCLUDED)
# -----------------------------
def calculate_production_contractual(
    items: List[Dict],
    output_pct: int,
    *,
    workshop_hours: float,
    prisoner_salary: float,
    supervisor_salaries: List[float],
    effective_pct: float,
    customer_covers_supervisors: bool,
    customer_type: str,
    apply_vat: bool,
    vat_rate: float,
    area_m2: float,
    usage_key: str,
    num_prisoners: int,
    num_supervisors: int,
    dev_rate: float,
) -> List[Dict]:
    """
    Splits instructor time, overheads AND development charge across items by labour minutes
    (assigned × hours × 60). Prisoner wages are per-item (assigned × prisoner_salary).
    """
    overheads_weekly, _detail = weekly_overheads_total(
        workshop_hours, area_m2, usage_key, num_prisoners, num_supervisors, customer_covers_supervisors
    )
    # Development charge weekly total (Commercial only)
    dev_weekly_total = overheads_weekly * (float(dev_rate) if customer_type == "Commercial" else 0.0)

    inst_weekly_total = (
        sum((s / 52.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)
        if not customer_covers_supervisors else 0.0
    )

    denom = sum(int(it.get("assigned", 0)) * workshop_hours * 60.0 for it in items)

    results: List[Dict] = []
    for idx, item in enumerate(items):
        name = (item.get("name") or "").strip() or f"Item {idx+1}"
        mins_per_unit = float(item.get("minutes", 0))
        prisoners_required = int(item.get("required", 1))
        prisoners_assigned = int(item.get("assigned", 0))

        # Weekly capacity at 100%
        if prisoners_assigned > 0 and mins_per_unit > 0 and prisoners_required > 0 and workshop_hours > 0:
            cap_100 = (prisoners_assigned * workshop_hours * 60.0) / (mins_per_unit * prisoners_required)
        else:
            cap_100 = 0.0

        # Apply global Output %
        actual_units = cap_100 * (float(output_pct) / 100.0)

        # Apportionment share (by assigned minutes)
        share = ((prisoners_assigned * workshop_hours * 60.0) / denom) if denom > 0 else 0.0

        # Weekly costs for this line
        prisoner_weekly_item  = prisoners_assigned * prisoner_salary
        inst_weekly_item      = inst_weekly_total * share
        overheads_weekly_item = overheads_weekly * share
        dev_weekly_item       = dev_weekly_total * share

        weekly_cost_item = prisoner_weekly_item + inst_weekly_item + overheads_weekly_item + dev_weekly_item
        unit_cost_ex_vat = (weekly_cost_item / actual_units) if actual_units > 0 else None

        # Unit price ex VAT = Unit cost, VAT optional for Commercial
        unit_price_ex_vat = unit_cost_ex_vat
        if unit_price_ex_vat is not None and (customer_type == "Commercial" and apply_vat):
            unit_price_inc_vat = unit_price_ex_vat * (1 + (float(vat_rate) / 100.0))
        else:
            unit_price_inc_vat = unit_price_ex_vat

        results.append({
            "Item": name,
            "Output %": int(output_pct),
            "Units/week": 0 if actual_units <= 0 else int(round(actual_units)),
            "Unit Cost (£)": unit_cost_ex_vat,
            "Unit Price ex VAT (£)": unit_price_ex_vat,
            "Unit Price inc VAT (£)": unit_price_inc_vat,
        })

    return results


# -----------------------------
# Ad‑hoc calculator (Development charge INCLUDED)
# -----------------------------
def working_days_between(start: date, end: date) -> int:
    """Inclusive working days Mon–Fri between start and end."""
    if end < start:
        return 0
    days, d = 0, start
    while d <= end:
        if d.weekday() < 5:
            days += 1
        d += timedelta(days=1)
    return days


def calculate_adhoc(
    lines: List[Dict],
    output_pct: int,
    *,
    workshop_hours: float,
    num_prisoners: int,
    prisoner_salary: float,
    supervisor_salaries: List[float],
    effective_pct: float,
    customer_covers_supervisors: bool,
    customer_type: str,
    apply_vat: bool,
    vat_rate: float,
    area_m2: float,
    usage_key: str,
    dev_rate: float,
    today: date | None = None,
) -> Dict:
    """
    Returns:
      - per_line: list of per-line dicts (unit costs ex/inc VAT, line totals, wd_available/needed)
      - totals: {ex_vat, inc_vat}
      - capacity: {current_daily_capacity, minutes_per_week_capacity}
      - feasibility: {earliest_wd_available, wd_needed_all, hard_block (bool), reason (str|None)}
    """
    today = today or date.today()

    # Capacity per day & per week @ Output%
    output_scale = float(output_pct) / 100.0
    hours_per_day = float(workshop_hours) / 5.0  # Mon–Fri
    daily_minutes_capacity_per_prisoner = hours_per_day * 60.0 * output_scale
    current_daily_capacity = num_prisoners * daily_minutes_capacity_per_prisoner
    minutes_per_week_capacity = max(1e-9, num_prisoners * workshop_hours * 60.0 * output_scale)

    # Weekly costs -> cost per minute
    overheads_weekly, _detail = weekly_overheads_total(
        workshop_hours, area_m2, usage_key, num_prisoners, 0, customer_covers_supervisors
    )
    dev_weekly_total = overheads_weekly * (float(dev_rate) if customer_type == "Commercial" else 0.0)
    inst_weekly_total = (
        sum((s / 52.0) * (float(effective_pct) / 100.0) for s in supervisor_salaries)
        if not customer_covers_supervisors else 0.0
    )
    prisoners_weekly_cost = num_prisoners * prisoner_salary
    weekly_cost_total = prisoners_weekly_cost + inst_weekly_total + overheads_weekly + dev_weekly_total
    cost_per_minute = weekly_cost_total / minutes_per_week_capacity

    per_line: List[Dict] = []
    total_job_minutes = 0.0
    earliest_wd_available = None

    for ln in lines:
        mins_per_unit = float(ln["mins_per_item"]) * int(ln["pris_per_item"])  # minutes of labour per unit
        unit_cost_ex_vat = cost_per_minute * mins_per_unit
        if customer_type == "Commercial" and apply_vat:
            unit_cost_inc_vat = unit_cost_ex_vat * (1 + (float(vat_rate) / 100.0))
        else:
            unit_cost_inc_vat = unit_cost_ex_vat

        total_line_minutes = int(ln["units"]) * mins_per_unit
        total_job_minutes += total_line_minutes

        wd_available = working_days_between(today, ln["deadline"])
        if earliest_wd_available is None or wd_available < earliest_wd_available:
            earliest_wd_available = wd_available

        if current_daily_capacity > 0:
            wd_needed_line_alone = math.ceil(total_line_minutes / current_daily_capacity)
        else:
            wd_needed_line_alone = float("inf")

        per_line.append({
            "name": ln["name"],
            "units": int(ln["units"]),
            "unit_cost_ex_vat": unit_cost_ex_vat,
            "unit_cost_inc_vat": unit_cost_inc_vat,
            "line_total_ex_vat": unit_cost_ex_vat * int(ln["units"]),
            "line_total_inc_vat": unit_cost_inc_vat * int(ln["units"]),
            "wd_available": wd_available,
            "wd_needed_line_alone": wd_needed_line_alone,
        })

    # Feasibility for the whole job against the tightest deadline
    if current_daily_capacity > 0:
        wd_needed_all = math.ceil(total_job_minutes / current_daily_capacity)
    else:
        wd_needed_all = float("inf")

    earliest_wd_available = earliest_wd_available or 0
    available_total_minutes_by_deadline = current_daily_capacity * earliest_wd_available

    hard_block = total_job_minutes > available_total_minutes_by_deadline
    reason = None
    if hard_block:
        reason = (
            f"Requested total minutes ({total_job_minutes:,.0f}) exceed available minutes "
            f"by the earliest deadline ({available_total_minutes_by_deadline:,.0f}). "
            "Reduce units, add prisoners, increase hours, extend deadline or lower Output%."
        )

    totals_ex = sum(p["line_total_ex_vat"] for p in per_line)
    totals_inc = sum(p["line_total_inc_vat"] for p in per_line)

    return {
        "per_line": per_line,
        "totals": {"ex_vat": totals_ex, "inc_vat": totals_inc},
        "capacity": {
            "current_daily_capacity": current_daily_capacity,
            "minutes_per_week_capacity": minutes_per_week_capacity,
        },
        "feasibility": {
            "earliest_wd_available": earliest_wd_available,
            "wd_needed_all": wd_needed_all,
            "hard_block": hard_block,
            "reason": reason,
        },
    }

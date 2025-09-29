# sidebar.py
# Sidebar — Tariffs & Overheads (moved out of newapp.py)

from __future__ import annotations
import streamlit as st
from tariff import TARIFF_BANDS

def render_sidebar(usage_key: str) -> None:
    st.header("Tariffs & Overheads")
    st.markdown("← Set your tariff & overhead rates here")

    band = TARIFF_BANDS[usage_key]
    elec_low = TARIFF_BANDS["low"]["intensity_per_year"]["elec_kwh_per_m2"]
    elec_med = TARIFF_BANDS["medium"]["intensity_per_year"]["elec_kwh_per_m2"]
    elec_high = TARIFF_BANDS["high"]["intensity_per_year"]["elec_kwh_per_m2"]
    gas_low = TARIFF_BANDS["low"]["intensity_per_year"]["gas_kwh_per_m2"]
    gas_med = TARIFF_BANDS["medium"]["intensity_per_year"]["gas_kwh_per_m2"]
    gas_high = TARIFF_BANDS["high"]["intensity_per_year"]["gas_kwh_per_m2"]
    water_per_emp_y = TARIFF_BANDS["low"]["intensity_per_year"]["water_m3_per_employee"]

    def _mark(v, k): return f"**{v}** ← selected" if usage_key == k else f"{v}"
    st.caption(f"**Electricity intensity (kWh/m²/year):** Low {_mark(elec_low,'low')} • Medium {_mark(elec_med,'medium')} • High {_mark(elec_high,'high')}")
    st.caption(f"**Gas intensity (kWh/m²/year):** Low {_mark(gas_low,'low')} • Medium {_mark(gas_med,'medium')} • High {_mark(gas_high,'high')}")
    st.caption(f"**Water:** **{water_per_emp_y} m³ per employee per year**")

    # Defaults in session state
    for k, v in {
        "electricity_rate": None, "elec_daily": None,
        "gas_rate": None, "gas_daily": None,
        "water_rate": None, "admin_monthly": None,
        "maint_rate_per_m2_y": None, "last_applied_band": None,
        "maint_method": "£/m² per year (industry standard)",
    }.items():
        st.session_state.setdefault(k, v)

    needs_seed = any(st.session_state[k] is None for k in [
        "electricity_rate", "elec_daily", "gas_rate", "gas_daily",
        "water_rate", "admin_monthly", "maint_rate_per_m2_y"
    ])
    if st.session_state["last_applied_band"] != usage_key or needs_seed:
        st.session_state.update({
            "electricity_rate": band["rates"]["elec_unit"],
            "elec_daily": band["rates"]["elec_daily"],
            "gas_rate": band["rates"]["gas_unit"],
            "gas_daily": band["rates"]["gas_daily"],
            "water_rate": band["rates"]["water_unit"],
            "admin_monthly": band["rates"]["admin_monthly"],
            "maint_rate_per_m2_y": band["intensity_per_year"]["maint_gbp_per_m2"],
            "last_applied_band": usage_key,
        })

    st.markdown("**Electricity**")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.number_input("Unit rate (£/kWh)", min_value=0.0, step=0.0001, format="%.4f", key="electricity_rate")
    with col_e2:
        st.number_input("Daily charge (£/day)", min_value=0.0, step=0.001, format="%.3f", key="elec_daily")

    st.markdown("**Gas**")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.number_input("Unit rate (£/kWh)", min_value=0.0, step=0.0001, format="%.4f", key="gas_rate")
    with col_g2:
        st.number_input("Daily charge (£/day)", min_value=0.0, step=0.001, format="%.3f", key="gas_daily")

    st.markdown("**Water**")
    st.number_input("Unit rate (£/m³)", min_value=0.0, step=0.10, format="%.2f", key="water_rate")

    st.markdown("**Maintenance / Depreciation**")
    maint_method = st.radio(
        "Method",
        ["£/m² per year (industry standard)", "Set a fixed monthly amount", "% of reinstatement value"],
        index=0 if str(st.session_state.get("maint_method","")).startswith("£/m²") else
             (1 if st.session_state.get("maint_method") == "Set a fixed monthly amount" else 2),
        key="maint_method"
    )
    if maint_method.startswith("£/m² per year"):
        st.number_input(
            "Maintenance rate (£/m²/year)", min_value=0.0, step=0.5,
            value=float(st.session_state["maint_rate_per_m2_y"]), key="maint_rate_per_m2_y"
        )
    elif maint_method == "Set a fixed monthly amount":
        st.number_input("Maintenance (monthly £)", min_value=0.0, value=float(st.session_state.get("maint_monthly", 0.0)),
                        step=25.0, key="maint_monthly")
    else:
        st.number_input("Reinstatement value (£)", min_value=0.0, value=float(st.session_state.get("reinstate_val", 0.0)),
                        step=10_000.0, key="reinstate_val")
        st.number_input("Annual % of reinstatement value", min_value=0.0, value=float(st.session_state.get("reinstate_pct", 2.0)),
                        step=0.25, format="%.2f", key="reinstate_pct")

    st.markdown("**Administration**")

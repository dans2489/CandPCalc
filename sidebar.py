# sidebar.py
# Draws the Tariffs & Overheads sidebar and seeds defaults based on the selected usage band.
# Safe for Python 3.7+ (no PEP 604 unions, no fancy quotes).

import streamlit as st
from tariff import TARIFF_BANDS


def _get_default(key: str, fallback):
    """Return a numeric value for Streamlit inputs, never None."""
    val = st.session_state.get(key)
    if val is None:
        return fallback
    try:
        return float(val)
    except Exception:
        return fallback


def draw_sidebar(usage_key: str) -> None:
    """
    Render the Tariffs & Overheads sidebar and seed defaults based on the selected usage band.

    Notes:
      • Variable energy and maintenance are apportioned by hours in the calculators (not here).
      • Standing (daily) energy charges are NOT apportioned (handled in calculators).
      • This function only captures user inputs and ensures values are present in session state.
    """
    with st.sidebar:
        st.header("Tariffs & Overheads")
        st.markdown("← Set your tariff & overhead rates here")

        # ---- Validate band and show helper captions
        if usage_key not in TARIFF_BANDS:
            st.error("Invalid usage band. Choose Low, Medium, or High.")
            return

        band = TARIFF_BANDS[usage_key]
        elec_low  = TARIFF_BANDS["low"]["intensity_per_year"]["elec_kwh_per_m2"]
        elec_med  = TARIFF_BANDS["medium"]["intensity_per_year"]["elec_kwh_per_m2"]
        elec_high = TARIFF_BANDS["high"]["intensity_per_year"]["elec_kwh_per_m2"]
        gas_low   = TARIFF_BANDS["low"]["intensity_per_year"]["gas_kwh_per_m2"]
        gas_med   = TARIFF_BANDS["medium"]["intensity_per_year"]["gas_kwh_per_m2"]
        gas_high  = TARIFF_BANDS["high"]["intensity_per_year"]["gas_kwh_per_m2"]
        water_per_emp_y = TARIFF_BANDS["low"]["intensity_per_year"]["water_m3_per_employee"]

        def _mark(v, k):
            return f"**{v}** ← selected" if usage_key == k else f"{v}"

        st.caption(
            f"**Electricity intensity (kWh/m²/year):** "
            f"Low {_mark(elec_low,'low')} • Medium {_mark(elec_med,'medium')} • High {_mark(elec_high,'high')}"
        )
        st.caption(
            f"**Gas intensity (kWh/m²/year):** "
            f"Low {_mark(gas_low,'low')} • Medium {_mark(gas_med,'medium')} • High {_mark(gas_high,'high')}"
        )
        st.caption(f"**Water:** **{water_per_emp_y} m³ per employee per year**")

        # ---- Ensure keys exist in session state so we never pass None into inputs
        needed_keys = [
            "electricity_rate", "elec_daily",
            "gas_rate", "gas_daily",
            "water_rate", "admin_monthly",
            "maint_method", "maint_rate_per_m2_y",
            "maint_monthly", "reinstate_val", "reinstate_pct",
            "last_applied_band",
        ]
        for k in needed_keys:
            st.session_state.setdefault(k, None)

        # ---- Seed defaults on first load or when usage band changes
        missing_any = any(st.session_state[k] is None for k in
                          ["electricity_rate", "elec_daily", "gas_rate", "gas_daily",
                           "water_rate", "admin_monthly", "maint_rate_per_m2_y"])

        if st.session_state.get("last_applied_band") != usage_key or missing_any:
            st.session_state["electricity_rate"]   = band["rates"]["elec_unit"]
            st.session_state["elec_daily"]         = band["rates"]["elec_daily"]
            st.session_state["gas_rate"]           = band["rates"]["gas_unit"]
            st.session_state["gas_daily"]          = band["rates"]["gas_daily"]
            st.session_state["water_rate"]         = band["rates"]["water_unit"]
            st.session_state["admin_monthly"]      = band["rates"]["admin_monthly"]
            st.session_state["maint_rate_per_m2_y"]= band["intensity_per_year"]["maint_gbp_per_m2"]
            # Default maintenance method
            if st.session_state.get("maint_method") is None:
                st.session_state["maint_method"] = "£/m² per year (industry standard)"
            # Sensible numeric fallbacks
            if st.session_state.get("maint_monthly") is None:
                st.session_state["maint_monthly"] = 0.0
            if st.session_state.get("reinstate_val") is None:
                st.session_state["reinstate_val"] = 0.0

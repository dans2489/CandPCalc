# sidebar.py
# Tariffs & Overheads sidebar (editable inputs) with robust default seeding.
# Safe for Python 3.7+.

import streamlit as st
from tariff import TARIFF_BANDS


def draw_sidebar(usage_key: str) -> None:
    """
    Renders the full Tariffs & Overheads sidebar and seeds defaults when the usage band changes.
    It writes values into st.session_state keys used by the calculators:
      electricity_rate, elec_daily, gas_rate, gas_daily,
      water_rate, admin_monthly,
      maint_method, maint_rate_per_m2_y, maint_monthly, reinstate_val, reinstate_pct,
      last_applied_band
    """
    with st.sidebar:
        st.header("Tariffs & Overheads")
        st.markdown("← Set tariff and overhead rates here")

        # ---- Validate band and pick a safe fallback
        if usage_key not in TARIFF_BANDS:
            usage_key = "low"
        band = TARIFF_BANDS[usage_key]

        # ---- Ensure keys exist so inputs never see None
        required_keys = [
            "electricity_rate", "elec_daily",
            "gas_rate", "gas_daily",
            "water_rate", "admin_monthly",
            "maint_method", "maint_rate_per_m2_y",
            "maint_monthly", "reinstate_val", "reinstate_pct",
            "last_applied_band",
        ]
        for k in required_keys:
            if k not in st.session_state:
                st.session_state[k] = None

        # ---- Seed defaults on first load, when band changes, or if anything critical is missing
        critical = ["electricity_rate", "elec_daily", "gas_rate", "gas_daily", "water_rate", "admin_monthly", "maint_rate_per_m2_y"]
        band_changed = st.session_state.get("last_applied_band") != usage_key
        missing_critical = any(st.session_state[k] is None for k in critical)

        if band_changed or missing_critical:
            st.session_state["electricity_rate"]    = float(band["rates"]["elec_unit"])
            st.session_state["elec_daily"]          = float(band["rates"]["elec_daily"])
            st.session_state["gas_rate"]            = float(band["rates"]["gas_unit"])
            st.session_state["gas_daily"]           = float(band["rates"]["gas_daily"])
            st.session_state["water_rate"]          = float(band["rates"]["water_unit"])
            st.session_state["admin_monthly"]       = float(band["rates"]["admin_monthly"])
            st.session_state["maint_rate_per_m2_y"] = float(band["intensity_per_year"]["maint_gbp_per_m2"])
            if st.session_state.get("maint_method") is None:
                st.session_state["maint_method"] = "£/m² per year (industry standard)"
            if st.session_state.get("maint_monthly") is None:
                st.session_state["maint_monthly"] = 0.0
            if st.session_state.get("reinstate_val") is None:
                st.session_state["reinstate_val"] = 0.0
            if st.session_state.get("reinstate_pct") is None:
                st.session_state["reinstate_pct"] = 2.0
            st.session_state["last_applied_band"]   = usage_key

        # ---- Helper captions (intensities for context)
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
            f"Electricity intensity (kWh/m²/yr): Low {_mark(elec_low,'low')} • "
            f"Medium {_mark(elec_med,'medium')} • High {_mark(elec_high,'high')}"
        )
        st.caption(
            f"Gas intensity (kWh/m²/yr): Low {_mark(gas_low,'low')} • "
            f"Medium {_mark(gas_med,'medium')} • High {_mark(gas_high,'high')}"
        )
        st.caption(f"Water: {water_per_emp_y} m³ per employee per year")

        # --------------- Electricity ---------------
        st.markdown("**Electricity**")
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "Unit rate (£/kWh)",
                min_value=0.0,
                step=0.0001,
                format="%.4f",
                key="electricity_rate"
            )
        with c2:
            st.number_input(
                "Daily charge (£/day)",
                min_value=0.0,
                step=0.001,
                format="%.3f",
                key="elec_daily"
            )

        # --------------- Gas ---------------
        st.markdown("**Gas**")
        g1, g2 = st.columns(2)
        with g1:
            st.number_input(
                "Unit rate (£/kWh)",
                min_value=0.0,
                step=0.0001,
                format="%.4f",
                key="gas_rate"
            )
        with g2:
            st.number_input(
                "Daily charge (£/day)",
                min_value=0.0,
                step=0.001,
                format="%.3f",
                key="gas_daily"
            )

        # --------------- Water ---------------
        st.markdown("**Water**")
        st.number_input(
            "Unit rate (£/m³)",
            min_value=0.0,
            step=0.10,
            format="%.2f",
            key="water_rate"
        )

        # --------------- Maintenance / Depreciation ---------------
        st.markdown("**Maintenance / Depreciation**")
        method_options = [
            "£/m² per year (industry standard)",
            "Set a fixed monthly amount",
            "% of reinstatement value",
        ]
        current_method = st.session_state.get("maint_method") or method_options[0]
        if current_method not in method_options:
            current_method = method_options[0]
        method_index = method_options.index(current_method)

        st.radio(
            "Method",
            method_options,
            index=method_index,
            key="maint_method"
        )

        if st.session_state["maint_method"].startswith("£/m² per year"):
            st.number_input(
                "Maintenance rate (£/m²/year)",
                min_value=0.0,
                step=0.5,
                key="maint_rate_per_m2_y"
            )
        elif st.session_state["maint_method"] == "Set a fixed monthly amount":
            st.number_input(
                "Maintenance (monthly £)",
                min_value=0.0,
                step=25.0,
                key="maint_monthly"
            )
        else:  # "% of reinstatement value"
            st.number_input(
                "Reinstatement value (£)",
                min_value=0.0,
                step=10000.0,
                key="reinstate_val"
            )
            st.number_input(
                "Annual % of reinstatement value",
                min_value=0.0,
                step=0.25,
                format="%.2f",
                key="reinstate_pct"
            )

        # --------------- Administration ---------------
        st.markdown("**Administration**")
        st.number_input(
            "Admin (monthly £)",
            min_value=0.0,
            step=25.0,
            key="admin_monthly"
        )

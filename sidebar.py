# sidebar.py
# Draws the Tariffs & Overheads sidebar and seeds defaults.
# Python 3.7+ safe.

import streamlit as st
from tariff import TARIFF_BANDS


def draw_sidebar(usage_key: str) -> None:
    """
    Render the Tariffs & Overheads sidebar and seed defaults based on the selected usage band.
    - Electricity & Gas: unit rate + daily standing charge
    - Water rate
    - Maintenance / Depreciation (3 methods)
    - Administration (monthly)

    Notes:
      • Seeding happens when the usage band changes OR any key is missing.
      • Standing (daily) charges are NOT apportioned by hours (handled in production/host code).
      • Variable energy and maintenance apportionment are handled in calculators, not here.
    """
    with st.sidebar:
        st.header("Tariffs & Overheads")
        st.markdown("← Set your tariff & overhead rates here")

        # ---- Band metadata and helpful captions
        try:
            band = TARIFF_BANDS[usage_key]
        except Exception:
            st.error("Invalid usage band. Please pick Low, Medium or High.")
            return

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

        # ---- Ensure keys exist in session state
        for k in (
            "electricity_rate", "elec_daily",
            "gas_rate", "gas_daily",
            "water_rate", "admin_monthly",
            "maint_rate_per_m2_y", "maint_monthly",
            "reinstate_val", "reinstate_pct",
            "maint_method", "last_applied_band",
        ):
            st.session_state.setdefault(k, None)

        # ---- Seed defaults if band changed or missing values
        needs_seed = any(st.session_state[k] is None for k in (
            "electricity_rate", "elec_daily", "gas_rate", "gas_daily",
            "water_rate", "admin_monthly", "maint_rate_per_m2_y"
        ))

        if st.session_state.get("last_applied_band") != usage_key or needs_seed:
            st.session_state.update({
                "electricity_rate": band["rates"]["elec_unit"],
                "elec_daily":       band["rates"]["elec_daily"],
                "gas_rate":         band["rates"]["gas_unit"],
                "gas_daily":        band["rates"]["gas_daily"],
                "water_rate":       band["rates"]["water_unit"],
                "admin_monthly":    band["rates"]["admin_monthly"],
                "maint_rate_per_m2_y": band["intensity_per_year"]["maint_gbp_per_m2"],
                "maint_method": "£/m² per year (industry standard)",
                "maint_monthly": 0.0 if st.session_state.get("maint_monthly") is None else st.session_state["maint_monthly"],
                "reinstate_val": 0.0 if st.session_state.get("reinstate_val") is None else st.session_state["reinstate_val"],
                "reinstate_pct": 2.0 if st.session_state.get("reinstate_pct") is None else st.session_state["reinstate_pct"],
                "last_applied_band": usage_key,
            })

        # ---- Electricity
        st.markdown("**Electricity**")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.number_input("Unit rate (£/kWh)",
                            min_value=0.0, step=0.0001, format="%.4f",
                            key="electricity_rate")
        with col_e2:
            st.number_input("Daily charge (£/day)",
                            min_value=0.0, step=0.001, format="%.3f",
                            key="elec_daily")

        # ---- Gas
        st.markdown("**Gas**")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.number_input("Unit rate (£/kWh)",
                            min_value=0.0, step=0.0001, format="%.4f",
                            key="gas_rate")
        with col_g2:
            st.number_input("Daily charge (£/day)",
                            min_value=0.0, step=0.001, format="%.3f",
                            key="gas_daily")

        # ---- Water
        st.markdown("**Water**")
        st.number_input("Unit rate (£/m³)",
                        min_value=0.0, step=0.10, format="%.2f",
                        key="water_rate")

        # ---- Maintenance / Depreciation
        st.markdown("**Maintenance / Depreciation**")
        current_method = st.session_state.get("maint_method") or "£/m² per year (industry standard)"
        method_idx = 0
        if current_method == "Set a fixed monthly amount":
            method_idx = 1
        elif current_method == "% of reinstatement value":
            method_idx = 2

        st.radio(
            "Method",
            ["£/m² per year (industry standard)", "Set a fixed monthly amount", "% of reinstatement value"],
            index=method_idx,
            key="maint_method"
        )

        if str(st.session_state["maint_method"]).startswith("£/m² per year"):
            st.number_input(
                "Maintenance rate (£/m²/year)",
                min_value=0.0, step=0.5,
                value=float(st.session_state.get("maint_rate_per_m2_y", band["intensity_per_year"]["maint_gbp_per_m2"])),
                key="maint_rate_per_m2_y"
            )
        elif st.session_state["maint_method"] == "Set a fixed monthly amount":
            st.number_input(
                "Maintenance (monthly £)",
                min_value=0.0, step=25.0,
                value=float(st.session_state.get("maint_monthly", 0.0)),
                key="maint_monthly"
            )
        else:  # % of reinstatement value
            st.number_input(
                "Reinstatement value (£)",
                min_value=0.0, step=10_000.0,
                value=float(st.session_state.get("reinstate_val", 0.0)),
                key="reinstate_val"
            )
            st.number_input(
                "Annual % of reinstatement value",
                min_value=0.0, step=0.25, format="%.2f",
                value=float(st.session_state.get("reinstate_pct", 2.0)),
                key="reinstate_pct"
            )

        # ---- Administration
        st.markdown("**Administration**")
        st.number_input("Admin (monthly £)",
                        min_value=0.0, step=25.0,
                        value=float(st.session_state.get("admin_monthly", band["rates"]["admin_monthly"])),

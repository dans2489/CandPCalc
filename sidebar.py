# sidebar.py
# Tariffs & Overheads sidebar (editable inputs) with reliable default seeding.
# Python 3.7+ safe (no PEP 604 unions).

import streamlit as st
from tariff import TARIFF_BANDS


def _as_float(x, fallback):
    """Coerce to float; if it fails or is None, return fallback."""
    try:
        return float(x)
    except Exception:
        return float(fallback)


def _seed_from_band(usage_key: str):
    """
    Seed session_state with defaults for the selected band.
    Called whenever the band changes or any critical key is missing.
    """
    band = TARIFF_BANDS[usage_key]
    st.session_state["electricity_rate"]    = float(band["rates"]["elec_unit"])
    st.session_state["elec_daily"]          = float(band["rates"]["elec_daily"])
    st.session_state["gas_rate"]            = float(band["rates"]["gas_unit"])
    st.session_state["gas_daily"]           = float(band["rates"]["gas_daily"])
    st.session_state["water_rate"]          = float(band["rates"]["water_unit"])
    st.session_state["admin_monthly"]       = float(band["rates"]["admin_monthly"])
    st.session_state["maint_rate_per_m2_y"] = float(band["intensity_per_year"]["maint_gbp_per_m2"])
    # Defaults for maintenance method + fields
    st.session_state.setdefault("maint_method", "£/m² per year (industry standard)")
    st.session_state.setdefault("maint_monthly", 0.0)
    st.session_state.setdefault("reinstate_val", 0.0)
    st.session_state.setdefault("reinstate_pct", 2.0)
    st.session_state["last_applied_band"] = usage_key


def draw_sidebar(usage_key: str) -> None:
    """
    Render the complete Tariffs & Overheads sidebar.

    Keys written to st.session_state:
      electricity_rate, elec_daily, gas_rate, gas_daily,
      water_rate, admin_monthly,
      maint_method, maint_rate_per_m2_y, maint_monthly, reinstate_val, reinstate_pct,
      last_applied_band
    """
    with st.sidebar:
        st.header("Tariffs & Overheads")
        st.markdown("← Set your tariff & overhead rates here")

        # ---- Validate band (never early-return after this point)
        if usage_key not in TARIFF_BANDS:
            st.error("Invalid usage band. Choose Low, Medium, or High.")
            # still render disabled inputs so the layout doesn't disappear
            usage_key = "low"  # fall back safely
        band = TARIFF_BANDS[usage_key]

        # ---- Helper captions (intensities)
        elec_low  = TARIFF_BANDS["low"]["intensity_per_year"]["elec_kwh_per_m2"]
        elec_med  = TARIFF_BANDS["medium"]["intensity_per_year"]["elec_kwh_per_m2"]
        elec_high = TARIFF_BANDS["high"]["intensity_per_year"]["elec_kwh_per_m2"]
        gas_low   = TARIFF_BANDS["low"]["intensity_per_year"]["gas_kwh_per_m2"]
        gas_med   = TARIFF_BANDS["medium"]["intensity_per_year"]["gas_kwh_per_m2"]
        gas_high  = TARIFF_BANDS["high"]["intensity_per_year"]["gas_kwh_per_m2"]
        water_per_emp_y = TARIFF_BANDS["low"]["intensity_per_year"]["water_m3_per_employee"]

        def _mark(v, k): return f"**{v}** ← selected" if usage_key == k else f"{v}"
        st.caption(f"**Electricity intensity (kWh/m²/year):** Low {_mark(elec_low,'low')} • Medium {_mark(elec_med,'medium')} • High {_mark(elec_high,'high')}")
        st.caption(f"**Gas intensity (kWh/m²/year):** Low {_mark(gas_low,'low')} • Medium {_mark(gas_med,'medium')} • High {_mark(gas_high,'high')}")
        st.caption(f"**Water:** **{water_per_emp_y} m³ per employee per year**")

        # ---- Ensure keys exist so inputs have values
        critical = [
            "electricity_rate", "elec_daily",
            "gas_rate", "gas_daily",
            "water_rate", "admin_monthly",
            "maint_rate_per_m2_y",
        ]
        for k in critical + ["maint_method", "maint_monthly", "reinstate_val", "reinstate_pct", "last_applied_band"]:
            st.session_state.setdefault(k, None)

        # ---- Seed on first load OR when band changes OR if any critical key is missing
        if (st.session_state.get("last_applied_band") != usage_key) or any(st.session_state[k] is None for k in critical):
            _seed_from_band(usage_key)

        # --------------- Electricity ---------------
        st.markdown("**Electricity**")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state["electricity_rate"] = st.number_input(
                "Unit rate (£/kWh)",
                min_value=0.0,
                step=0.0001,
                format="%.4f",
                value=_as_float(st.session_state.get("electricity_rate"), band["rates"]["elec_unit"]),
                key="electricity_rate"
            )
        with c2:
            st.session_state["elec_daily"] = st.number_input(
                "Daily charge (£/day)",
                min_value=0.0,
                step=0.001,
                format="%.3f",
                value=_as_float(st.session_state.get("elec_daily"), band["rates"]["elec_daily"]),
                key="elec_daily"
            )

        # --------------- Gas ---------------
        st.markdown("**Gas**")
        g1, g2 = st.columns(2)
        with g1:
            st.session_state["gas_rate"] = st.number_input(
                "Unit rate (£/kWh)",
                min_value=0.0,
                step=0.0001,
                format="%.4f",
                value=_as_float(st.session_state.get("gas_rate"), band["rates"]["gas_unit"]),
                key="gas_rate"
            )
        with g2:
            st.session_state["gas_daily"] = st.number_input(
                "Daily charge (£/day)",
                min_value=0.0,
                step=0.001,
                format="%.3f",
                value=_as_float(st.session_state.get("gas_daily"), band["rates"]["gas_daily"]),
                key="gas_daily"
            )

        # --------------- Water ---------------
        st.markdown("**Water**")
        st.session_state["water_rate"] = st.number_input(
            "Unit rate (£/m³)",
            min_value=0.0,
            step=0.10,
            format="%.2f",
            value=_as_float(st.session_state.get("water_rate"), band["rates"]["water_unit"]),
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

        st.session_state["maint_method"] = st.radio(
            "Method",
            method_options,
            index=method_index,
            key="maint_method"
        )

        if st.session_state["maint_method"].startswith("£/m² per year"):
            st.session_state["maint_rate_per_m2_y"] = st.number_input(
                "Maintenance rate (£/m²/year)",
                min_value=0.0,
                step=0.5,
                value=_as_float(st.session_state.get("maint_rate_per_m2_y"), band["intensity_per_year"]["maint_gbp_per_m2"]),
                key="maint_rate_per_m2_y"
            )
        elif st.session_state["maint_method"] == "Set a fixed monthly amount":
            st.session_state["maint_monthly"] = st.number_input(
                "Maintenance (monthly £)",
                min_value=0.0,
                step=25.0,
                value=_as_float(st.session_state.get("maint_monthly"), 0.0),
                key="maint_monthly"
            )
        else:  # % of reinstatement value
            st.session_state["reinstate_val"] = st.number_input(
                "Reinstatement value (£)",
                min_value=0.0,
                step=10_000.0,
                value=_as_float(st.session_state.get("reinstate_val"), 0.0),
                key="reinstate_val"
            )
            st.session_state["reinstate_pct"] = st.number_input(
                "Annual % of reinstatement value",
                min_value=0.0,
                step=0.25,
                format="%.2f",
                value=_as_float(st.session_state.get("reinstate_pct"), 2.0),
                key="reinstate_pct"
            )

        # --------------- Administration ---------------
        st.markdown("**Administration**")
        st.session_state["admin_monthly"] = st.number_input(
            "Admin (monthly £)",
            min_value=0.0,
            step=25.0,
            value=_as_float(st.session_state.get("admin_monthly"), band["rates"]["admin_monthly"]),
            key="admin_monthly"
        )

        # Small debug hint (toggle on if needed)
        # with st.expander("Debug (sidebar state)"):
        #     st.write({k: st.session_state.get(k) for k in [
        #         "electricity_rate","elec_daily","gas_rate","gas_daily","water_rate",
        #         "maint_method","maint_rate_per_m2_y","maint_monthly","reinstate_val","reinstate_pct",
        #         "admin_monthly","last_applied_band"
        #     ]})

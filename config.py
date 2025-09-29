# config.py
# Central configuration and small helpers used across the app.

from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    # --- Units & geometry
    FT2_TO_M2: float = 0.092903

    # --- Calendar
    DAYS_PER_MONTH: float = 365.0 / 12.0  # ≈30.42

    # --- Utilisation model
    # A 'fully utilised' week used for apportioning variable energy and maintenance by hours.
    # Change this in the UI (sidebar) if needed.
    FULL_UTILISATION_WEEK: float = 37.5   # 7.5h x 5 days

    # --- Apportionment switches (per your requirements)
    # Standing (daily) energy charges are NOT apportioned by hours.
    APPORTION_FIXED_ENERGY: bool = False
    # Maintenance IS apportioned by hours.
    APPORTION_MAINTENANCE: bool = True

    # --- Admin defaults
    DEFAULT_ADMIN_MONTHLY: float = 150.0

    # --- UI defaults
    GLOBAL_OUTPUT_DEFAULT: int = 100  # % Output utilisation (applies to Contractual + Ad‑hoc)


CFG = AppConfig()


def hours_scale(hours_open_per_week: float, full_week: float | None = None) -> float:
    """
    Returns a proportional scale based on hours open per week.
      scale = hours_open_per_week / FULL_UTILISATION_WEEK

    We do not clamp to 1.0 so extended opening (> full-week) can scale allocations up if desired.
    """
    try:
        h = float(hours_open_per_week)
        f = float(full_week if full_week is not None else CFG.FULL_UTILISATION_WEEK)
        if f <= 0:
            return 1.0
        return max(0.0, h / f)
    except Exception:
        return 1.0

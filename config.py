# config.py
# Central configuration and small helpers used across the app.

from dataclasses import dataclass
from typing import Optional  # <-- 3.9-safe alternative to `float | None`

@dataclass(frozen=True)
class AppConfig:
    # --- Units & geometry
    FT2_TO_M2: float = 0.092903

    # --- Calendar
    DAYS_PER_MONTH: float = 365.0 / 12.0  # ≈30.42

    # --- Utilisation model
    # 'Fully utilised' week used to apportion variable energy and maintenance by hours.
    FULL_UTILISATION_WEEK: float = 37.5   # 7.5h x 5 days by default

    # --- Apportionment switches (per your requirements)
    APPORTION_FIXED_ENERGY: bool = False  # Standing (daily) energy charges NOT apportioned by hours
    APPORTION_MAINTENANCE: bool = True    # Maintenance IS apportioned by hours

    # --- Admin defaults
    DEFAULT_ADMIN_MONTHLY: float = 150.0

    # --- UI defaults
    GLOBAL_OUTPUT_DEFAULT: int = 100  # % Output utilisation (applies to Contractual + Ad‑hoc)

CFG = AppConfig()

def hours_scale(hours_open_per_week: float, full_week: Optional[float] = None) -> float:
    """
    Returns scale = hours_open_per_week / FULL_UTILISATION_WEEK.
    Not clamped to 1.0 so extended hours can scale allocations up if desired.
    """
    try:
        h = float(hours_open_per_week)
        f = float(full_week if full_week is not None else CFG.FULL_UTILISATION_WEEK)
        if f <= 0:
            return 1.0
        return max(0.0, h / f)
    except Exception:
        return 1.0

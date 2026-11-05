"""
tools/cost_calculator.py
─────────────────────────
Standalone cost calculation utilities used by the agent tools.
"""

from __future__ import annotations

import os
from typing import List, Tuple


class CostCalculator:
    """Utility class for time-of-use electricity cost calculations."""

    def __init__(self):
        self.base_rate    = float(os.getenv("ENERGY_RATE_PER_KWH",    "0.12"))
        self.peak_mult    = float(os.getenv("PEAK_RATE_MULTIPLIER",   "1.5"))
        self.offpeak_mult = float(os.getenv("OFF_PEAK_RATE_MULTIPLIER", "0.7"))
        self.peak_start   = int(os.getenv("PEAK_HOURS_START", "17"))
        self.peak_end     = int(os.getenv("PEAK_HOURS_END",   "21"))

    def rate_at_hour(self, hour: int) -> float:
        if self.peak_start <= hour < self.peak_end:
            return round(self.base_rate * self.peak_mult, 4)
        if hour >= 22 or hour < 6:
            return round(self.base_rate * self.offpeak_mult, 4)
        return round(self.base_rate, 4)

    def daily_cost(self, kwh_per_hour: float, run_hour: int) -> float:
        return round(kwh_per_hour * self.rate_at_hour(run_hour), 4)

    def best_hours_for_load(self, n: int = 3) -> List[Tuple[int, float]]:
        """Returns the n cheapest hours of the day (hour, rate)."""
        hours = [(h, self.rate_at_hour(h)) for h in range(24)]
        hours.sort(key=lambda x: x[1])
        return hours[:n]

    def monthly_saving_by_shift(self, daily_kwh: float) -> float:
        """Saving per month if load is moved from peak to off-peak."""
        peak_cost    = daily_kwh * self.base_rate * self.peak_mult
        offpeak_cost = daily_kwh * self.base_rate * self.offpeak_mult
        return round((peak_cost - offpeak_cost) * 30, 2)

    def annual_saving(self, daily_kwh: float) -> float:
        return round(self.monthly_saving_by_shift(daily_kwh) * 12, 2)

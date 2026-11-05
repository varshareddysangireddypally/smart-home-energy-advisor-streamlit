"""
data/smart_meter.py
───────────────────
Simulates a smart meter and home appliance data source.
In a real deployment this would connect to a utility API or
an MQTT/REST smart-meter endpoint.
"""

from __future__ import annotations

import random
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict


# ─────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────

@dataclass
class ApplianceReading:
    name: str
    watts: float          # current draw in Watts
    daily_kwh: float      # estimated daily consumption
    category: str         # hvac | kitchen | laundry | entertainment | lighting | other
    is_on: bool = True
    smart_controllable: bool = False


@dataclass
class HourlyReading:
    timestamp: datetime
    kwh: float            # energy consumed in that hour
    cost: float           # cost in configured currency
    is_peak: bool


@dataclass
class DailyUsageSummary:
    date: str
    total_kwh: float
    total_cost: float
    peak_kwh: float
    off_peak_kwh: float
    hourly: List[HourlyReading] = field(default_factory=list)


@dataclass
class SmartMeterSnapshot:
    meter_id: str
    timestamp: datetime
    current_draw_watts: float
    today_kwh: float
    month_kwh: float
    month_cost: float
    appliances: List[ApplianceReading]
    daily_history: List[DailyUsageSummary]


# ─────────────────────────────────────────────────────────────
# Simulator
# ─────────────────────────────────────────────────────────────

class SmartMeterSimulator:
    """
    Generates realistic synthetic smart-meter data for a typical
    4-person household.  Patterns vary by time-of-day and day-of-week
    so the AI advisor has meaningful variation to analyse.
    """

    APPLIANCES: List[Dict] = [
        {"name": "HVAC System",            "watts": 3500, "daily_kwh": 12.0, "category": "hvac",          "smart": True},
        {"name": "Electric Water Heater",  "watts": 4000, "daily_kwh": 4.5,  "category": "hvac",          "smart": True},
        {"name": "Refrigerator",           "watts": 150,  "daily_kwh": 1.5,  "category": "kitchen",       "smart": False},
        {"name": "Dishwasher",             "watts": 1800, "daily_kwh": 1.2,  "category": "kitchen",       "smart": True},
        {"name": "Electric Oven / Stove",  "watts": 2400, "daily_kwh": 1.0,  "category": "kitchen",       "smart": False},
        {"name": "Washing Machine",        "watts": 500,  "daily_kwh": 0.5,  "category": "laundry",       "smart": True},
        {"name": "Clothes Dryer",          "watts": 5000, "daily_kwh": 3.5,  "category": "laundry",       "smart": True},
        {"name": "Television (65\")",      "watts": 120,  "daily_kwh": 0.5,  "category": "entertainment", "smart": False},
        {"name": "Gaming Console",         "watts": 200,  "daily_kwh": 0.4,  "category": "entertainment", "smart": False},
        {"name": "Home Office PC",         "watts": 300,  "daily_kwh": 2.4,  "category": "other",         "smart": False},
        {"name": "LED Lighting",           "watts": 200,  "daily_kwh": 1.0,  "category": "lighting",      "smart": True},
        {"name": "EV Charger",             "watts": 7200, "daily_kwh": 10.0, "category": "other",         "smart": True},
        {"name": "Pool Pump",              "watts": 750,  "daily_kwh": 3.0,  "category": "other",         "smart": True},
    ]

    def __init__(self, meter_id: str = "SM-HOME-001",
                 rate: float = 0.12,
                 peak_multiplier: float = 1.5,
                 off_peak_multiplier: float = 0.7,
                 peak_start: int = 17,
                 peak_end: int = 21,
                 history_days: int = 30):
        self.meter_id = meter_id
        self.rate = rate
        self.peak_multiplier = peak_multiplier
        self.off_peak_multiplier = off_peak_multiplier
        self.peak_start = peak_start
        self.peak_end = peak_end
        self.history_days = history_days
        random.seed(42)   # reproducible simulation

    # ── helpers ──────────────────────────────────────────────

    def _effective_rate(self, hour: int) -> float:
        if self.peak_start <= hour < self.peak_end:
            return self.rate * self.peak_multiplier
        if hour >= 22 or hour < 6:
            return self.rate * self.off_peak_multiplier
        return self.rate

    def _is_peak(self, hour: int) -> bool:
        return self.peak_start <= hour < self.peak_end

    def _hourly_base_kwh(self, hour: int, day_of_week: int) -> float:
        """
        Simulate realistic load curve:
        - Morning spike (6-9), lunch dip, afternoon steady,
          evening peak (17-21), night drop.
        - Weekends have a different profile.
        """
        weekend = day_of_week >= 5
        base = 0.5
        # morning rise
        if 6 <= hour < 9:
            base = 1.8 + math.sin((hour - 6) * math.pi / 3) * 0.8
        # midday
        elif 9 <= hour < 12:
            base = 1.2 + (0.4 if weekend else 0.0)
        # afternoon
        elif 12 <= hour < 17:
            base = 1.0 + math.sin((hour - 12) * math.pi / 5) * 0.3
        # evening peak
        elif 17 <= hour < 21:
            base = 2.5 + math.sin((hour - 17) * math.pi / 4) * 1.0
        # late evening
        elif 21 <= hour < 23:
            base = 1.5
        # night
        else:
            base = 0.4
        # add ±15 % random noise
        base *= 1.0 + random.uniform(-0.15, 0.15)
        # weekend boost (people home)
        if weekend:
            base *= 1.1
        return round(max(0.1, base), 3)

    # ── public API ────────────────────────────────────────────

    def get_appliances(self) -> List[ApplianceReading]:
        appliances = []
        for a in self.APPLIANCES:
            # Randomly determine if appliance is currently on
            is_on = random.random() > 0.3
            # Add ±10 % variance to watts
            watts = a["watts"] * (1.0 + random.uniform(-0.1, 0.1))
            appliances.append(ApplianceReading(
                name=a["name"],
                watts=round(watts if is_on else 0.0, 1),
                daily_kwh=a["daily_kwh"],
                category=a["category"],
                is_on=is_on,
                smart_controllable=a["smart"],
            ))
        return appliances

    def get_daily_history(self) -> List[DailyUsageSummary]:
        summaries = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for d in range(self.history_days, 0, -1):
            day = today - timedelta(days=d)
            dow = day.weekday()
            hourly_readings: List[HourlyReading] = []
            day_kwh = 0.0
            day_cost = 0.0
            peak_kwh = 0.0
            off_peak_kwh = 0.0

            for h in range(24):
                ts = day + timedelta(hours=h)
                kwh = self._hourly_base_kwh(h, dow)
                rate = self._effective_rate(h)
                cost = round(kwh * rate, 4)
                is_pk = self._is_peak(h)
                hourly_readings.append(HourlyReading(
                    timestamp=ts,
                    kwh=kwh,
                    cost=cost,
                    is_peak=is_pk,
                ))
                day_kwh += kwh
                day_cost += cost
                if is_pk:
                    peak_kwh += kwh
                elif h >= 22 or h < 6:
                    off_peak_kwh += kwh

            summaries.append(DailyUsageSummary(
                date=day.strftime("%Y-%m-%d"),
                total_kwh=round(day_kwh, 2),
                total_cost=round(day_cost, 4),
                peak_kwh=round(peak_kwh, 2),
                off_peak_kwh=round(off_peak_kwh, 2),
                hourly=hourly_readings,
            ))
        return summaries

    def get_snapshot(self) -> SmartMeterSnapshot:
        now = datetime.now()
        appliances = self.get_appliances()
        history = self.get_daily_history()

        current_draw = sum(a.watts for a in appliances if a.is_on)
        today_kwh = self._hourly_base_kwh(now.hour, now.weekday()) * now.hour
        month_kwh = sum(d.total_kwh for d in history)
        month_cost = sum(d.total_cost for d in history)

        return SmartMeterSnapshot(
            meter_id=self.meter_id,
            timestamp=now,
            current_draw_watts=round(current_draw, 1),
            today_kwh=round(today_kwh, 2),
            month_kwh=round(month_kwh, 2),
            month_cost=round(month_cost, 2),
            appliances=appliances,
            daily_history=history,
        )

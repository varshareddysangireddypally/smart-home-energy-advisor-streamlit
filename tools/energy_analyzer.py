"""
tools/energy_analyzer.py
─────────────────────────
Analytical tools the agent uses to inspect smart meter data.
Each tool returns a structured dict that the agent can include
in the Granite prompt as context.
"""

from __future__ import annotations

import os
from statistics import mean, stdev
from typing import Dict, List, Any

from data.smart_meter import SmartMeterSnapshot, DailyUsageSummary, HourlyReading


class EnergyAnalyzer:
    """
    A collection of deterministic analysis functions.
    The agent calls these tools to gather facts before asking
    Granite to reason over them.
    """

    def __init__(self, snapshot: SmartMeterSnapshot):
        self.snap = snapshot
        self.rate = float(os.getenv("ENERGY_RATE_PER_KWH", "0.12"))
        self.peak_start = int(os.getenv("PEAK_HOURS_START", "17"))
        self.peak_end = int(os.getenv("PEAK_HOURS_END", "21"))
        self.currency = os.getenv("ENERGY_CURRENCY", "USD")

    # ── Tool 1: Current Status ────────────────────────────────

    def get_current_status(self) -> Dict[str, Any]:
        """Returns a snapshot of what the home is doing RIGHT NOW."""
        on_appliances = [a for a in self.snap.appliances if a.is_on]
        top_consumers = sorted(on_appliances, key=lambda a: a.watts, reverse=True)[:5]
        return {
            "tool": "current_status",
            "meter_id": self.snap.meter_id,
            "timestamp": self.snap.timestamp.strftime("%Y-%m-%d %H:%M"),
            "current_draw_watts": self.snap.current_draw_watts,
            "current_draw_kw": round(self.snap.current_draw_watts / 1000, 2),
            "today_kwh": self.snap.today_kwh,
            "today_estimated_cost": round(self.snap.today_kwh * self.rate, 2),
            "is_peak_hour": self.peak_start <= self.snap.timestamp.hour < self.peak_end,
            "active_appliances": len(on_appliances),
            "top_consumers": [
                {"name": a.name, "watts": a.watts, "category": a.category}
                for a in top_consumers
            ],
        }

    # ── Tool 2: Monthly Bill Analysis ─────────────────────────

    def analyze_monthly_bill(self) -> Dict[str, Any]:
        """Breaks down the current month's energy spend by category and time-of-use."""
        history = self.snap.daily_history

        # Aggregate all hourly readings
        all_hourly: List[HourlyReading] = []
        for day in history:
            all_hourly.extend(day.hourly)

        peak_kwh    = sum(r.kwh for r in all_hourly if r.is_peak)
        off_peak_kwh = sum(r.kwh for r in all_hourly if not r.is_peak)
        total_kwh   = sum(r.kwh for r in all_hourly)
        total_cost  = sum(r.cost for r in all_hourly)

        # Category split from appliance data
        cat_daily: Dict[str, float] = {}
        for a in self.snap.appliances:
            cat_daily[a.category] = cat_daily.get(a.category, 0) + a.daily_kwh
        total_daily = sum(cat_daily.values()) or 1
        category_pct = {
            cat: round((kwh / total_daily) * 100, 1)
            for cat, kwh in cat_daily.items()
        }

        # Daily average and trend
        daily_totals = [d.total_kwh for d in history]
        avg_daily = mean(daily_totals) if daily_totals else 0
        std_daily = stdev(daily_totals) if len(daily_totals) > 1 else 0

        # Compare last 7 days vs previous 7 days
        if len(history) >= 14:
            recent_7  = mean([d.total_kwh for d in history[-7:]])
            prev_7    = mean([d.total_kwh for d in history[-14:-7]])
            trend_pct = round(((recent_7 - prev_7) / prev_7) * 100, 1) if prev_7 else 0
        else:
            trend_pct = 0.0

        return {
            "tool": "monthly_bill_analysis",
            "period_days": len(history),
            "total_kwh": round(total_kwh, 2),
            "total_cost": round(total_cost, 2),
            "currency": self.currency,
            "peak_kwh": round(peak_kwh, 2),
            "off_peak_kwh": round(off_peak_kwh, 2),
            "peak_cost_share_pct": round((peak_kwh / total_kwh * 100), 1) if total_kwh else 0,
            "avg_daily_kwh": round(avg_daily, 2),
            "daily_std_kwh": round(std_daily, 2),
            "category_breakdown_pct": category_pct,
            "trend_7day_pct": trend_pct,
            "high_bill_flags": self._flag_high_bill(history, avg_daily, std_daily),
        }

    def _flag_high_bill_days(
        self, history: List[DailyUsageSummary], avg: float, std: float
    ) -> List[str]:
        return [
            d.date for d in history
            if d.total_kwh > avg + std
        ]

    def _flag_high_bill(
        self, history: List[DailyUsageSummary], avg: float, std: float
    ) -> List[str]:
        return self._flag_high_bill_days(history, avg, std)

    # ── Tool 3: Appliance-Level Audit ─────────────────────────

    def audit_appliances(self) -> Dict[str, Any]:
        """Ranks appliances by estimated monthly cost and identifies optimisation targets."""
        days = len(self.snap.daily_history) or 30
        appliance_costs = []
        for a in self.snap.appliances:
            monthly_kwh  = a.daily_kwh * days
            monthly_cost = round(monthly_kwh * self.rate, 2)
            appliance_costs.append({
                "name": a.name,
                "category": a.category,
                "daily_kwh": a.daily_kwh,
                "monthly_kwh": round(monthly_kwh, 1),
                "monthly_cost": monthly_cost,
                "smart_controllable": a.smart_controllable,
                "optimizable": a.smart_controllable and monthly_cost > 5.0,
            })
        appliance_costs.sort(key=lambda x: x["monthly_cost"], reverse=True)
        total_monthly = sum(a["monthly_cost"] for a in appliance_costs)
        potential_saving = sum(
            a["monthly_cost"] * 0.30
            for a in appliance_costs
            if a["optimizable"]
        )
        return {
            "tool": "appliance_audit",
            "appliances": appliance_costs,
            "total_monthly_cost": round(total_monthly, 2),
            "potential_monthly_saving": round(potential_saving, 2),
            "top_3_consumers": [a["name"] for a in appliance_costs[:3]],
        }

    # ── Tool 4: Time-of-Use Optimisation ──────────────────────

    def get_optimal_schedule(self) -> Dict[str, Any]:
        """
        Returns the best time windows to run shiftable loads,
        based on the time-of-use tariff structure.
        """
        rate = float(os.getenv("ENERGY_RATE_PER_KWH", "0.12"))
        peak_mult    = float(os.getenv("PEAK_RATE_MULTIPLIER", "1.5"))
        offpeak_mult = float(os.getenv("OFF_PEAK_RATE_MULTIPLIER", "0.7"))

        shiftable = [
            a for a in self.snap.appliances
            if a.smart_controllable and a.daily_kwh > 0.3
        ]
        schedule = []
        for a in shiftable:
            peak_cost    = round(a.daily_kwh * rate * peak_mult, 3)
            offpeak_cost = round(a.daily_kwh * rate * offpeak_mult, 3)
            saving       = round(peak_cost - offpeak_cost, 3)
            schedule.append({
                "appliance": a.name,
                "category": a.category,
                "daily_kwh": a.daily_kwh,
                "cost_if_peak": peak_cost,
                "cost_if_offpeak": offpeak_cost,
                "daily_saving": saving,
                "monthly_saving": round(saving * 30, 2),
                "recommended_window": "10 PM – 6 AM (off-peak)",
            })
        schedule.sort(key=lambda x: x["monthly_saving"], reverse=True)
        return {
            "tool": "optimal_schedule",
            "off_peak_window": "10:00 PM – 6:00 AM",
            "off_peak_rate": round(rate * offpeak_mult, 4),
            "peak_rate": round(rate * peak_mult, 4),
            "shiftable_appliances": schedule,
            "total_monthly_saving_potential": round(
                sum(s["monthly_saving"] for s in schedule), 2
            ),
        }

    # ── Tool 5: Usage Pattern Detection ───────────────────────

    def detect_patterns(self) -> Dict[str, Any]:
        """Identifies usage anomalies and consumption patterns over the history window."""
        history = self.snap.daily_history
        if not history:
            return {"tool": "pattern_detection", "patterns": []}

        daily_kwh = [d.total_kwh for d in history]
        avg = mean(daily_kwh)
        sd  = stdev(daily_kwh) if len(daily_kwh) > 1 else 0

        # Weekend vs weekday
        weekday_kwh = [d.total_kwh for d in history
                       if not self._is_weekend(d.date)]
        weekend_kwh = [d.total_kwh for d in history
                       if self._is_weekend(d.date)]
        wd_avg = mean(weekday_kwh) if weekday_kwh else 0
        we_avg = mean(weekend_kwh) if weekend_kwh else 0

        # Hourly averages across the month
        hourly_avgs: Dict[int, List[float]] = {h: [] for h in range(24)}
        for day in history:
            for reading in day.hourly:
                hourly_avgs[reading.timestamp.hour].append(reading.kwh)
        hourly_profile = {
            h: round(mean(vals), 3)
            for h, vals in hourly_avgs.items() if vals
        }
        peak_hour = max(hourly_profile, key=hourly_profile.get)

        # Anomaly days
        anomalies = [
            {"date": d.date, "kwh": d.total_kwh,
             "deviation": round((d.total_kwh - avg) / sd, 1) if sd else 0}
            for d in history if sd and abs(d.total_kwh - avg) > 1.5 * sd
        ]

        return {
            "tool": "pattern_detection",
            "avg_daily_kwh": round(avg, 2),
            "std_daily_kwh": round(sd, 2),
            "weekday_avg_kwh": round(wd_avg, 2),
            "weekend_avg_kwh": round(we_avg, 2),
            "weekend_premium_pct": round(((we_avg - wd_avg) / wd_avg * 100), 1) if wd_avg else 0,
            "peak_consumption_hour": peak_hour,
            "hourly_profile": hourly_profile,
            "anomaly_days": anomalies[:5],  # top 5
            "total_anomaly_days": len(anomalies),
        }

    @staticmethod
    def _is_weekend(date_str: str) -> bool:
        from datetime import datetime
        return datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5

    # ── Tool 6: Carbon Footprint ──────────────────────────────

    def estimate_carbon(self) -> Dict[str, Any]:
        """Estimates CO2 emissions based on average grid intensity."""
        # US average grid emission factor: ~0.386 kg CO2e per kWh
        EMISSION_FACTOR = 0.386
        total_kwh = self.snap.month_kwh
        monthly_kg_co2 = round(total_kwh * EMISSION_FACTOR, 2)
        # Equivalent trees needed to offset (1 tree absorbs ~22 kg CO2/year)
        trees_needed = round(monthly_kg_co2 * 12 / 22, 1)
        return {
            "tool": "carbon_estimate",
            "monthly_kwh": total_kwh,
            "monthly_kg_co2": monthly_kg_co2,
            "monthly_tons_co2": round(monthly_kg_co2 / 1000, 3),
            "trees_to_offset_annually": trees_needed,
            "emission_factor_kg_per_kwh": EMISSION_FACTOR,
            "note": "Based on US average grid emission factor (0.386 kg CO2e/kWh)",
        }

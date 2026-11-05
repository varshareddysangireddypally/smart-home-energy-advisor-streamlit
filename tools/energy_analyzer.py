
"""
tools/energy_analyzer.py

Deterministic analysis tools for the Smart Home Energy Advisor.
Returns structured data for the IBM Granite advisor.
"""

from __future__ import annotations

import os
from statistics import mean, stdev
from typing import Dict, List, Any

from data.smart_meter import (
    SmartMeterSnapshot,
    DailyUsageSummary,
    HourlyReading,
)


class EnergyAnalyzer:
    """
    Deterministic analysis functions for simulated smart-meter data.
    """

    def __init__(self, snapshot: SmartMeterSnapshot):
        self.snap = snapshot
        self.rate = float(os.getenv("ENERGY_RATE_PER_KWH", "0.12"))
        self.peak_start = int(os.getenv("PEAK_HOURS_START", "17"))
        self.peak_end = int(os.getenv("PEAK_HOURS_END", "21"))
        self.currency = os.getenv("ENERGY_CURRENCY", "USD")

    # ---------------------------------------------------------
    # Helper functions
    # ---------------------------------------------------------

    @staticmethod
    def _is_off_peak_hour(hour: int) -> bool:
        return hour >= 22 or hour < 6

    def _is_peak_hour(self, hour: int) -> bool:
        return self.peak_start <= hour < self.peak_end

    # ---------------------------------------------------------
    # Tool 1: Current Status
    # ---------------------------------------------------------

    def get_current_status(self) -> Dict[str, Any]:

        on_appliances = [
            a for a in self.snap.appliances if a.is_on
        ]

        top_consumers = sorted(
            on_appliances,
            key=lambda a: a.watts,
            reverse=True
        )[:5]

        return {
            "tool": "current_status",
            "meter_id": self.snap.meter_id,
            "timestamp": self.snap.timestamp.strftime(
                "%Y-%m-%d %H:%M"
            ),
            "current_draw_watts": self.snap.current_draw_watts,
            "current_draw_kw": round(
                self.snap.current_draw_watts / 1000, 2
            ),
            "today_kwh": self.snap.today_kwh,
            "today_estimated_cost": round(
                self.snap.today_kwh * self.rate, 2
            ),
            "currency": self.currency,
            "is_peak_hour": self._is_peak_hour(
                self.snap.timestamp.hour
            ),
            "active_appliances": len(on_appliances),
            "top_consumers": [
                {
                    "name": a.name,
                    "watts": a.watts,
                    "category": a.category,
                }
                for a in top_consumers
            ],
            "data_note": (
                "Current status and daily cost are simulated estimates."
            ),
        }

    # ---------------------------------------------------------
    # Tool 2: Monthly Bill Analysis
    # ---------------------------------------------------------

    def analyze_monthly_bill(self) -> Dict[str, Any]:

        history = self.snap.daily_history

        all_hourly: List[HourlyReading] = []

        for day in history:
            all_hourly.extend(day.hourly)

        peak_readings = [
            r for r in all_hourly if r.is_peak
        ]

        peak_kwh = sum(r.kwh for r in peak_readings)
        peak_cost = sum(r.cost for r in peak_readings)

        off_peak_readings = [
            r for r in all_hourly
            if self._is_off_peak_hour(r.timestamp.hour)
        ]

        off_peak_kwh = sum(
            r.kwh for r in off_peak_readings
        )

        total_kwh = sum(r.kwh for r in all_hourly)
        total_cost = sum(r.cost for r in all_hourly)

        peak_cost_share_pct = (
            round(peak_cost / total_cost * 100, 1)
            if total_cost > 0 else 0
        )

        peak_usage_share_pct = (
            round(peak_kwh / total_kwh * 100, 1)
            if total_kwh > 0 else 0
        )

        # Appliance category percentages use all appliance estimates.
        cat_daily: Dict[str, float] = {}

        for appliance in self.snap.appliances:
            cat_daily[appliance.category] = (
                cat_daily.get(appliance.category, 0)
                + appliance.daily_kwh
            )

        total_appliance_daily = sum(cat_daily.values())

        category_pct = {
            category: round(
                kwh / total_appliance_daily * 100, 1
            )
            for category, kwh in cat_daily.items()
        } if total_appliance_daily > 0 else {}

        daily_totals = [
            day.total_kwh for day in history
        ]

        avg_daily = (
            mean(daily_totals) if daily_totals else 0
        )

        std_daily = (
            stdev(daily_totals)
            if len(daily_totals) > 1 else 0
        )

        if len(history) >= 14:

            recent_7 = mean([
                d.total_kwh for d in history[-7:]
            ])

            prev_7 = mean([
                d.total_kwh for d in history[-14:-7]
            ])

            trend_pct = (
                round(
                    ((recent_7 - prev_7) / prev_7) * 100,
                    1
                )
                if prev_7 > 0 else 0
            )

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

            "peak_cost": round(peak_cost, 2),
            "peak_cost_share_pct": peak_cost_share_pct,
            "peak_usage_share_pct": peak_usage_share_pct,

            "avg_daily_kwh": round(avg_daily, 2),
            "daily_std_kwh": round(std_daily, 2),

            "category_breakdown_pct": category_pct,
            "category_breakdown_basis": (
                "Estimated appliance daily consumption. "
                "Not a breakdown of measured meter consumption."
            ),

            "trend_7day_pct": trend_pct,

            "high_bill_flags": self._flag_high_bill(
                history, avg_daily, std_daily
            ),

            "data_note": (
                "Monthly usage and cost are calculated from "
                "simulated hourly meter readings."
            ),
        }

    def _flag_high_bill_days(
        self,
        history: List[DailyUsageSummary],
        avg: float,
        std: float,
    ) -> List[str]:

        return [
            day.date
            for day in history
            if day.total_kwh > avg + std
        ]

    def _flag_high_bill(
        self,
        history: List[DailyUsageSummary],
        avg: float,
        std: float,
    ) -> List[str]:

        return self._flag_high_bill_days(
            history, avg, std
        )

    # ---------------------------------------------------------
    # Tool 3: Appliance-Level Audit
    # ---------------------------------------------------------

    def audit_appliances(self) -> Dict[str, Any]:
        """
        Estimates appliance consumption, cost, and percentage
        contribution using all appliance estimates.
        """

        days = len(self.snap.daily_history) or 30

        # Total daily consumption across ALL appliances.
        total_daily_kwh = sum(
            appliance.daily_kwh
            for appliance in self.snap.appliances
        )

        appliance_costs = []

        for appliance in self.snap.appliances:

            daily_kwh = appliance.daily_kwh
            monthly_kwh = daily_kwh * days

            contribution_pct = (
                round(daily_kwh / total_daily_kwh * 100, 1)
                if total_daily_kwh > 0 else 0
            )

            monthly_cost = round(
                monthly_kwh * self.rate, 2
            )

            appliance_costs.append({
                "name": appliance.name,
                "category": appliance.category,

                "daily_kwh": round(daily_kwh, 2),
                "monthly_kwh": round(monthly_kwh, 2),

                "contribution_pct": contribution_pct,

                "monthly_cost": monthly_cost,
                "currency": self.currency,

                "smart_controllable": appliance.smart_controllable,

                "optimizable": (
                    appliance.smart_controllable
                    and monthly_cost > 5.0
                ),

                "estimate_basis": (
                    "Configured daily appliance consumption. "
                    "Percentage is calculated against the total "
                    "daily estimates of all appliances."
                ),
            })

        # Rank by daily energy consumption.
        appliance_costs.sort(
            key=lambda x: x["daily_kwh"],
            reverse=True
        )

        total_monthly = round(
            sum(a["monthly_cost"] for a in appliance_costs),
            2
        )

        return {
            "tool": "appliance_audit",

            "total_daily_appliance_estimate_kwh": round(
                total_daily_kwh, 2
            ),

            "total_monthly_appliance_estimate_kwh": round(
                total_daily_kwh * days, 2
            ),

            "appliances": appliance_costs,

            "total_monthly_cost": total_monthly,

            "potential_monthly_saving": 0.0,
            "potential_monthly_saving_available": False,

            "saving_estimate_note": (
                "A reliable appliance savings amount cannot "
                "be calculated from the available data. "
                "No arbitrary savings percentage is assumed."
            ),

            "top_3_consumers": [
                a["name"] for a in appliance_costs[:3]
            ],

            "currency": self.currency,

            "data_note": (
                "Appliance costs and consumption are estimates "
                "based on configured daily appliance values. "
                "They are not the actual smart-meter bill."
            ),
        }

    # ---------------------------------------------------------
    # Tool 4: Time-of-Use Optimisation
    # ---------------------------------------------------------

    def get_optimal_schedule(self) -> Dict[str, Any]:

        rate = float(
            os.getenv("ENERGY_RATE_PER_KWH", "0.12")
        )

        peak_mult = float(
            os.getenv("PEAK_RATE_MULTIPLIER", "1.5")
        )

        offpeak_mult = float(
            os.getenv("OFF_PEAK_RATE_MULTIPLIER", "0.7")
        )

        shiftable = [
            a for a in self.snap.appliances
            if a.smart_controllable and a.daily_kwh > 0.3
        ]

        schedule = []

        for appliance in shiftable:

            peak_cost = (
                appliance.daily_kwh * rate * peak_mult
            )

            offpeak_cost = (
                appliance.daily_kwh * rate * offpeak_mult
            )

            daily_saving = peak_cost - offpeak_cost

            schedule.append({
                "appliance": appliance.name,
                "category": appliance.category,

                "daily_kwh": appliance.daily_kwh,

                "cost_if_peak": round(peak_cost, 3),
                "cost_if_offpeak": round(offpeak_cost, 3),

                "daily_saving": round(daily_saving, 3),

                "monthly_saving": round(
                    daily_saving * 30, 2
                ),

                "recommended_window": (
                    "10 PM - 6 AM (off-peak)"
                ),

                "assumption": (
                    "Assumes the full configured daily "
                    "consumption can be shifted from peak "
                    "to off-peak hours."
                ),
            })

        schedule.sort(
            key=lambda x: x["monthly_saving"],
            reverse=True
        )

        total_saving = round(
            sum(
                item["monthly_saving"]
                for item in schedule
            ),
            2
        )

        return {
            "tool": "optimal_schedule",

            "off_peak_window": "10:00 PM - 6:00 AM",

            "off_peak_rate": round(
                rate * offpeak_mult, 4
            ),

            "peak_rate": round(
                rate * peak_mult, 4
            ),

            "currency": self.currency,

            "shiftable_appliances": schedule,

            "total_monthly_saving_potential": total_saving,

            "saving_type": "theoretical_estimate",

            "saving_note": (
                "Theoretical maximum under the assumption "
                "that all listed shiftable consumption "
                "moves from peak to off-peak hours. "
                "Actual savings may be lower."
            ),
        }

    # ---------------------------------------------------------
    # Tool 5: Usage Pattern Detection
    # ---------------------------------------------------------

    def detect_patterns(self) -> Dict[str, Any]:

        history = self.snap.daily_history

        if not history:
            return {
                "tool": "pattern_detection",
                "patterns": [],
                "total_anomaly_days": 0,
            }

        daily_kwh = [
            day.total_kwh for day in history
        ]

        avg = mean(daily_kwh)

        sd = (
            stdev(daily_kwh)
            if len(daily_kwh) > 1 else 0
        )

        weekday_kwh = [
            day.total_kwh
            for day in history
            if not self._is_weekend(day.date)
        ]

        weekend_kwh = [
            day.total_kwh
            for day in history
            if self._is_weekend(day.date)
        ]

        wd_avg = (
            mean(weekday_kwh) if weekday_kwh else 0
        )

        we_avg = (
            mean(weekend_kwh) if weekend_kwh else 0
        )

        hourly_avgs: Dict[int, List[float]] = {
            hour: [] for hour in range(24)
        }

        for day in history:
            for reading in day.hourly:
                hourly_avgs[
                    reading.timestamp.hour
                ].append(reading.kwh)

        hourly_profile = {
            hour: round(mean(values), 3)
            for hour, values in hourly_avgs.items()
            if values
        }

        peak_hour = (
            max(hourly_profile, key=hourly_profile.get)
            if hourly_profile else None
        )

        anomalies = []

        for day in history:

            if sd > 0:

                deviation = (
                    day.total_kwh - avg
                ) / sd

                if abs(deviation) > 1.5:

                    anomalies.append({
                        "date": day.date,
                        "kwh": day.total_kwh,
                        "deviation": round(deviation, 1),
                    })

        return {
            "tool": "pattern_detection",

            "avg_daily_kwh": round(avg, 2),
            "std_daily_kwh": round(sd, 2),

            "weekday_avg_kwh": round(wd_avg, 2),
            "weekend_avg_kwh": round(we_avg, 2),

            "weekend_premium_pct": (
                round(
                    ((we_avg - wd_avg) / wd_avg) * 100,
                    1
                )
                if wd_avg > 0 else 0
            ),

            "peak_consumption_hour": peak_hour,

            "hourly_profile": hourly_profile,

            "anomaly_days": anomalies[:5],

            "total_anomaly_days": len(anomalies),

            "data_note": (
                "Patterns and anomalies are calculated "
                "from simulated daily meter readings."
            ),
        }

    @staticmethod
    def _is_weekend(date_str: str) -> bool:
        from datetime import datetime

        return (
            datetime.strptime(
                date_str, "%Y-%m-%d"
            ).weekday() >= 5
        )

    # ---------------------------------------------------------
    # Tool 6: Carbon Footprint
    # ---------------------------------------------------------

    def estimate_carbon(self) -> Dict[str, Any]:
        """
        Estimates emissions using an illustrative US grid factor.
        """

        emission_factor = 0.386

        total_kwh = self.snap.month_kwh

        monthly_kg_co2 = round(
            total_kwh * emission_factor, 2
        )

        trees_needed = round(
            monthly_kg_co2 * 12 / 22, 1
        )

        return {
            "tool": "carbon_estimate",

            "monthly_kwh": total_kwh,

            "monthly_kg_co2": monthly_kg_co2,

            "monthly_tons_co2": round(
                monthly_kg_co2 / 1000, 3
            ),

            "trees_to_offset_annually": trees_needed,

            "emission_factor_kg_per_kwh": (
                emission_factor
            ),

            "note": (
                "Uses a US average grid emission factor "
                "of 0.386 kg CO2e/kWh. This is an illustrative "
                "estimate, not a verified India-specific "
                "emission calculation."
            ),
        }

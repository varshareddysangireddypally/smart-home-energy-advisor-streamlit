"""
tools/report_generator.py
──────────────────────────
Generates formatted console reports and text exports.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


class ReportGenerator:
    """Formats analysis results into human-readable reports."""

    def print_bill_analysis(self, data: Dict[str, Any]) -> None:
        console.print(Panel(
            f"[bold]Period:[/bold] Last {data['period_days']} days\n"
            f"[bold]Total Usage:[/bold] {data['total_kwh']} kWh\n"
            f"[bold]Total Cost:[/bold] ${data['total_cost']:.2f} {data['currency']}\n"
            f"[bold]Peak Usage:[/bold] {data['peak_kwh']} kWh ({data['peak_cost_share_pct']}% of usage)\n"
            f"[bold]Off-Peak Usage:[/bold] {data['off_peak_kwh']} kWh\n"
            f"[bold]Average Daily:[/bold] {data['avg_daily_kwh']} kWh\n"
            f"[bold]7-Day Trend:[/bold] {data['trend_7day_pct']:+.1f}%\n"
            f"[bold]High Usage Days:[/bold] {len(data.get('high_bill_flags', []))}",
            title="📋 Monthly Bill Analysis",
            border_style="yellow",
        ))

        # Category breakdown
        if data.get("category_breakdown_pct"):
            table = Table(title="Category Breakdown", box=box.SIMPLE)
            table.add_column("Category")
            table.add_column("Share %", justify="right")
            for cat, pct in sorted(
                data["category_breakdown_pct"].items(), key=lambda x: -x[1]
            ):
                bar = "█" * int(pct / 5)
                table.add_row(cat.title(), f"{pct}%  {bar}")
            console.print(table)

    def print_schedule_recommendations(self, data: Dict[str, Any]) -> None:
        console.print(
            f"\n[bold]Off-Peak Window:[/bold] {data['off_peak_window']}  "
            f"Rate: ${data['off_peak_rate']}/kWh  (vs ${data['peak_rate']}/kWh peak)\n"
        )
        table = Table(
            title="⏰ Recommended Shift Schedule",
            box=box.ROUNDED,
            border_style="cyan",
        )
        table.add_column("Appliance",        style="bold")
        table.add_column("Daily kWh",        justify="right")
        table.add_column("Peak Cost",        justify="right")
        table.add_column("Off-Peak Cost",    justify="right")
        table.add_column("Monthly Saving",   justify="right", style="green")

        for a in data["shiftable_appliances"]:
            table.add_row(
                a["appliance"],
                str(a["daily_kwh"]),
                f"${a['cost_if_peak']}",
                f"${a['cost_if_offpeak']}",
                f"${a['monthly_saving']}",
            )
        console.print(table)
        console.print(
            f"[bold green]Total potential monthly saving: "
            f"${data['total_monthly_saving_potential']:.2f}[/bold green]\n"
        )

    def export_text_report(self, analyses: Dict[str, Any], filename: str | None = None) -> str:
        """Exports a plain-text report suitable for saving or emailing."""
        lines = [
            "=" * 60,
            "  SMART HOME ENERGY ADVISOR — MONTHLY REPORT",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ]
        for key, data in analyses.items():
            lines.append(f"\n[{key.upper()}]")
            for k, v in data.items():
                if k != "tool":
                    lines.append(f"  {k}: {v}")
        report = "\n".join(lines)

        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            console.print(f"[dim]Report saved to {filename}[/dim]")

        return report

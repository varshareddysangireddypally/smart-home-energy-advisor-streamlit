
"""
agent/advisor_agent.py

Main Agentic AI loop for the Smart Home Energy Advisor.

Architecture:
1. Receive user question
2. Classify intent
3. Execute relevant analysis tools
4. Build a data-rich prompt
5. Generate response using IBM Granite
6. Return response
"""

from __future__ import annotations

import os
import logging
from typing import List, Dict, Any

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

from data.smart_meter import SmartMeterSimulator, SmartMeterSnapshot
from agent.granite_client import GraniteClient
from agent.prompt_builder import PromptBuilder
from tools.energy_analyzer import EnergyAnalyzer

load_dotenv()
logger = logging.getLogger(__name__)
console = Console()


# -------------------------------------------------------------
# Intent to tool mapping
# -------------------------------------------------------------

INTENT_TOOL_MAP: Dict[str, List[str]] = {
    "BILL_ANALYSIS": [
        "current_status",
        "monthly_bill_analysis",
        "appliance_audit",
        "optimal_schedule",
    ],
    "APPLIANCE_SCHEDULE": [
        "current_status",
        "optimal_schedule",
        "monthly_bill_analysis",
    ],
    "APPLIANCE_AUDIT": [
        "appliance_audit",
        "current_status",
    ],
    "USAGE_PATTERN": [
        "pattern_detection",
    ],
    "CARBON_FOOTPRINT": [
        "carbon_estimate",
        "appliance_audit",
    ],
    "GENERAL_ADVICE": [
        "current_status",
        "appliance_audit",
        "optimal_schedule",
        "pattern_detection",
    ],
    "CURRENT_STATUS": [
        "current_status",
        "appliance_audit",
    ],
}


# -------------------------------------------------------------
# Keyword-based intent classification
# -------------------------------------------------------------

KEYWORD_INTENT_MAP = [
    (
        [
            "pattern",
            "trend",
            "anomal",
            "spike",
            "unusual",
            "weekend",
            "weekday",
            "hourly consumption",
            "hourly usage",
            "hourly pattern",
            "peak consumption",
            "peak usage",
            "peak hour",
            "consumption peak",
            "usage peak",
            "highest consumption",
            "highest usage",
            "highest at",
            "maximum consumption",
            "maximum usage",
            "maximum at",
            "lowest consumption",
            "lowest usage",
            "lowest at",
            "consumption highest",
            "usage highest",
            "consumption lowest",
            "usage lowest",
        ],
        "USAGE_PATTERN",
    ),
    (
        [
            "washing",
            "washer",
            "dryer",
            "dishwasher",
            "schedule",
            "when",
            "time to run",
        ],
        "APPLIANCE_SCHEDULE",
    ),
    (
        [
            "appliance",
            "device",
            "which",
            "most",
            "top",
            "biggest",
        ],
        "APPLIANCE_AUDIT",
    ),
    (
        [
            "bill",
            "expensive",
            "high bill",
            "electricity bill",
            "monthly bill",
            "charge",
        ],
        "BILL_ANALYSIS",
    ),
    (
        [
            "carbon",
            "co2",
            "emission",
            "environment",
            "green",
        ],
        "CARBON_FOOTPRINT",
    ),
    (
        [
            "now",
            "current",
            "right now",
            "at the moment",
            "live",
        ],
        "CURRENT_STATUS",
    ),
    (
        [
            "save",
            "tip",
            "recommend",
            "advice",
            "help",
            "reduce",
        ],
        "GENERAL_ADVICE",
    ),
]


class SmartHomeEnergyAdvisor:
    """
    Top-level agent orchestrator.
    Manages the data layer, AI client, and CLI interface.
    """

    def __init__(self):
        self.meter = SmartMeterSimulator(
            meter_id=os.getenv(
                "SMART_METER_ID",
                "SM-HOME-001"
            ),
            rate=float(
                os.getenv("ENERGY_RATE_PER_KWH", "0.12")
            ),
            peak_multiplier=float(
                os.getenv("PEAK_RATE_MULTIPLIER", "1.5")
            ),
            off_peak_multiplier=float(
                os.getenv("OFF_PEAK_RATE_MULTIPLIER", "0.7")
            ),
            peak_start=int(
                os.getenv("PEAK_HOURS_START", "17")
            ),
            peak_end=int(
                os.getenv("PEAK_HOURS_END", "21")
            ),
            history_days=int(
                os.getenv("MAX_HISTORY_DAYS", "30")
            ),
        )

        self.granite = GraniteClient()
        self.prompt_builder = PromptBuilder()
        self.conversation_history: List[Dict[str, str]] = []

        self.max_iterations = int(
            os.getenv("AGENT_MAX_ITERATIONS", "10")
        )

        self._snapshot: SmartMeterSnapshot | None = None

    # ---------------------------------------------------------
    # Data layer
    # ---------------------------------------------------------

    def _get_snapshot(self) -> SmartMeterSnapshot:
        """Returns cached snapshot or refreshes from the meter."""

        if self._snapshot is None:
            self._snapshot = self.meter.get_snapshot()

        return self._snapshot

    def _refresh_snapshot(self) -> SmartMeterSnapshot:
        """Refreshes the smart-meter snapshot."""

        self._snapshot = self.meter.get_snapshot()
        return self._snapshot

    # ---------------------------------------------------------
    # Intent classification
    # ---------------------------------------------------------

    def _classify_intent(self, question: str) -> str:
        """
        Classifies questions using keyword matching first.
        Granite classification is used only for ambiguous questions.
        """

        q_lower = question.lower()

        for keywords, intent in KEYWORD_INTENT_MAP:
            if any(keyword in q_lower for keyword in keywords):
                logger.info(
                    "Keyword intent detected: %s",
                    intent,
                )
                return intent

        intent_prompt = (
            self.prompt_builder
            .build_intent_classification_prompt(question)
        )

        raw = self.granite.generate(
            intent_prompt,
            max_tokens=20,
        ).strip().upper()

        known = set(INTENT_TOOL_MAP.keys())

        for word in raw.split():
            if word in known:
                return word

        return "GENERAL_ADVICE"

    # ---------------------------------------------------------
    # Tool execution
    # ---------------------------------------------------------

    def _run_tools(
        self,
        intent: str,
        snapshot: SmartMeterSnapshot,
    ) -> List[Dict[str, Any]]:
        """Executes only the tools associated with the intent."""

        analyzer = EnergyAnalyzer(snapshot)

        tool_names = INTENT_TOOL_MAP.get(
            intent,
            ["current_status"],
        )

        results = []

        tool_fn_map = {
            "current_status": analyzer.get_current_status,
            "monthly_bill_analysis": analyzer.analyze_monthly_bill,
            "appliance_audit": analyzer.audit_appliances,
            "optimal_schedule": analyzer.get_optimal_schedule,
            "pattern_detection": analyzer.detect_patterns,
            "carbon_estimate": analyzer.estimate_carbon,
        }

        for name in tool_names:
            fn = tool_fn_map.get(name)

            if fn:
                try:
                    result = fn()
                    results.append(result)

                    logger.debug(
                        "Tool '%s' succeeded",
                        name,
                    )

                except Exception as exc:
                    logger.warning(
                        "Tool '%s' failed: %s",
                        name,
                        exc,
                    )

        return results

    # ---------------------------------------------------------
    # Deterministic bill reduction response
    # ---------------------------------------------------------

    def _build_bill_reduction_response(
        self,
        tool_results: List[Dict[str, Any]],
    ) -> str | None:
        """Builds a factual bill-reduction response."""

        schedule_result = next(
            (
                result
                for result in tool_results
                if result.get("tool") == "optimal_schedule"
            ),
            None,
        )

        if not schedule_result:
            return None

        appliances = schedule_result.get(
            "shiftable_appliances",
            [],
        )

        if not appliances:
            return None

        currency = schedule_result.get("currency", "USD")

        total_saving = schedule_result.get(
            "total_monthly_saving_potential"
        )

        if total_saving is None:
            return None

        off_peak_window = schedule_result.get(
            "off_peak_window",
            "Not available",
        )

        peak_rate = schedule_result.get(
            "peak_rate",
            "Not available",
        )

        off_peak_rate = schedule_result.get(
            "off_peak_rate",
            "Not available",
        )

        response = (
            "## Electricity Bill Reduction Recommendations\n\n"
            "Based on the available appliance scheduling "
            "and tariff data:\n\n"
            "### 1. Use the off-peak window\n\n"
            f"- **Off-peak window:** {off_peak_window}\n"
            f"- **Peak rate:** {currency} {peak_rate}/kWh\n"
            f"- **Off-peak rate:** {currency} {off_peak_rate}/kWh\n\n"
            "### 2. Prioritise these shiftable appliances\n\n"
            "| Appliance | Daily Usage | Theoretical Monthly Saving |\n"
            "|---|---:|---:|\n"
        )

        for appliance in appliances:
            name = appliance.get("appliance", "Unknown")
            daily_kwh = appliance.get("daily_kwh", "N/A")
            monthly_saving = appliance.get("monthly_saving", "N/A")

            response += (
                f"| {name} | {daily_kwh} kWh | "
                f"{currency} {monthly_saving} |\n"
            )

        response += (
            "\n### 3. Estimated savings potential\n\n"
            f"The combined theoretical maximum is "
            f"**{currency} {total_saving} per month**.\n\n"
            "**Important:** This estimate assumes the full "
            "configured daily consumption of every listed "
            "shiftable appliance can be moved from peak to "
            "off-peak hours. Actual savings may be lower. "
            "This is a theoretical estimate, not a guaranteed "
            "reduction in your electricity bill.\n\n"
            "The appliance schedule estimates and smart-meter "
            "bill measurements are separate data sources."
        )

        return response

    # ---------------------------------------------------------
    # Deterministic appliance scheduling response
    # ---------------------------------------------------------

    def _build_appliance_schedule_response(
        self,
        tool_results: List[Dict[str, Any]],
    ) -> str | None:
        """Builds a factual appliance scheduling response."""

        schedule_result = next(
            (
                result
                for result in tool_results
                if result.get("tool") == "optimal_schedule"
            ),
            None,
        )

        if not schedule_result:
            return None

        appliances = schedule_result.get(
            "shiftable_appliances",
            [],
        )

        if not appliances:
            return None

        currency = schedule_result.get("currency", "USD")

        off_peak_window = schedule_result.get(
            "off_peak_window",
            "Not available",
        )

        off_peak_rate = schedule_result.get(
            "off_peak_rate",
            "Not available",
        )

        peak_rate = schedule_result.get(
            "peak_rate",
            "Not available",
        )

        total_saving = schedule_result.get(
            "total_monthly_saving_potential"
        )

        if total_saving is None:
            return None

        response = (
            "## Recommended Appliance Schedule\n\n"
            "### Best available off-peak window\n\n"
            f"- **Off-peak hours:** {off_peak_window}\n"
            f"- **Off-peak rate:** {currency} "
            f"{off_peak_rate}/kWh\n"
            f"- **Peak rate:** {currency} "
            f"{peak_rate}/kWh\n\n"
            "### Appliances identified by the schedule tool\n\n"
            "| Appliance | Configured Daily Usage |\n"
            "|---|---:|\n"
        )

        for appliance in appliances:
            name = appliance.get("appliance", "Unknown")
            daily_kwh = appliance.get("daily_kwh", "N/A")

            response += (
                f"| {name} | {daily_kwh} kWh/day |\n"
            )

        response += (
            "\n### Estimated savings\n\n"
            f"Shifting the configured consumption of all "
            f"listed appliances from peak to off-peak hours "
            f"has a theoretical maximum saving of "
            f"**{currency} {total_saving} per month**.\n\n"
            "### Practical guidance\n\n"
            f"Where practical, schedule flexible appliances "
            f"during the {off_peak_window} off-peak window. "
            "Consider appliance operating requirements, "
            "comfort, safety, and manufacturer instructions "
            "before changing schedules.\n\n"
            "**Important:** The savings figure is theoretical. "
            "It assumes the full configured daily consumption "
            "of every listed appliance can be shifted from "
            "peak to off-peak hours. Actual savings may be "
            "lower and are not guaranteed. The available data "
            "does not confirm each appliance's actual operating "
            "time."
        )

        return response

    # ---------------------------------------------------------
    # Deterministic appliance audit response
    # ---------------------------------------------------------

    def _build_appliance_audit_response(
        self,
        tool_results: List[Dict[str, Any]],
    ) -> str | None:
        """
        Builds an accurate appliance consumption report
        using verified appliance audit data.
        """

        audit = next(
            (
                result
                for result in tool_results
                if result.get("tool") == "appliance_audit"
            ),
            None,
        )

        if not audit:
            return None

        appliances = audit.get("appliances", [])

        if not appliances:
            return None

        total_daily = audit.get(
            "total_daily_appliance_estimate_kwh",
            0,
        )

        if not total_daily:
            return None

        currency = audit.get("currency", "USD")

        sorted_appliances = sorted(
            appliances,
            key=lambda item: float(item.get("daily_kwh", 0)),
            reverse=True,
        )

        response = (
            "## Appliance Consumption Analysis\n\n"
            "**Daily and monthly appliance consumption estimates:**\n\n"
            "| Appliance | Daily Usage | Monthly Usage | Contribution |\n"
            "|---|---:|---:|---:|\n"
        )

        for appliance in sorted_appliances:
            response += (
                f"| {appliance.get('name', 'Unknown')} "
                f"| {appliance.get('daily_kwh', 0)} kWh "
                f"| {appliance.get('monthly_kwh', 0)} kWh "
                f"| {appliance.get('contribution_pct', 0)}% |\n"
            )

        top_three = sorted_appliances[:3]

        top_three_daily = sum(
            float(item.get("daily_kwh", 0))
            for item in top_three
        )

        top_three_percentage = (
            top_three_daily / float(total_daily)
        ) * 100

        response += (
            "\n### Key Findings\n\n"
            "**Top 3 electricity consumers:**\n\n"
        )

        for index, appliance in enumerate(top_three, start=1):
            response += (
                f"{index}. **{appliance.get('name')}** — "
                f"{appliance.get('daily_kwh')} kWh/day "
                f"({appliance.get('contribution_pct')}%).\n"
            )

        response += (
            f"\nTogether, these three appliances account for "
            f"**{top_three_percentage:.1f}%** of total estimated "
            f"daily appliance consumption "
            f"({top_three_daily:.1f} kWh out of "
            f"{total_daily} kWh).\n\n"
            f"**Total estimated daily consumption:** "
            f"{total_daily} kWh.\n\n"
            f"**Estimated monthly appliance cost:** "
            f"{currency} {audit.get('total_monthly_cost', 'N/A')}.\n\n"
            "**Important:** These figures are based on configured "
            "daily appliance estimates. They are not actual "
            "smart-meter readings or the actual electricity bill."
        )

        return response

    # ---------------------------------------------------------
    # Agent reasoning loop
    # ---------------------------------------------------------

    def answer(self, question: str) -> str:
        """
        Full agent cycle:
        Classify -> Execute tools -> Build prompt -> Generate response.
        """

        snapshot = self._refresh_snapshot()

        intent = self._classify_intent(question)

        logger.info("Intent: %s", intent)

        tool_results = self._run_tools(
            intent,
            snapshot,
        )

        question_lower = question.lower()

        reduction_keywords = (
            "reduce",
            "lower",
            "save",
            "saving",
            "cut",
            "decrease",
        )

        is_bill_reduction_question = (
            intent == "BILL_ANALYSIS"
            and any(
                word in question_lower
                for word in reduction_keywords
            )
        )

        if is_bill_reduction_question:
            response = self._build_bill_reduction_response(
                tool_results
            )

            if response is None:
                prompt = self.prompt_builder.build_analysis_prompt(
                    user_question=question,
                    tool_results=tool_results,
                    conversation_history=self.conversation_history,
                )

                response = self.granite.generate(prompt)

        elif intent == "APPLIANCE_SCHEDULE":
            response = self._build_appliance_schedule_response(
                tool_results
            )

            if response is None:
                prompt = self.prompt_builder.build_analysis_prompt(
                    user_question=question,
                    tool_results=tool_results,
                    conversation_history=self.conversation_history,
                )

                response = self.granite.generate(prompt)

        elif intent == "APPLIANCE_AUDIT":
            response = self._build_appliance_audit_response(
                tool_results
            )

            if response is None:
                prompt = self.prompt_builder.build_analysis_prompt(
                    user_question=question,
                    tool_results=tool_results,
                    conversation_history=self.conversation_history,
                )

                response = self.granite.generate(prompt)

        else:
            prompt = self.prompt_builder.build_analysis_prompt(
                user_question=question,
                tool_results=tool_results,
                conversation_history=self.conversation_history,
            )

            response = self.granite.generate(prompt)

        self.conversation_history.append({
            "role": "user",
            "content": question,
        })

        self.conversation_history.append({
            "role": "assistant",
            "content": response,
        })

        if len(self.conversation_history) > 20:
            self.conversation_history = (
                self.conversation_history[-20:]
            )

        return response

    # ---------------------------------------------------------
    # Monthly summary
    # ---------------------------------------------------------

    def get_monthly_summary(self) -> str:
        """Generates a monthly energy summary."""

        snapshot = self._get_snapshot()

        analyzer = EnergyAnalyzer(snapshot)

        bill_data = analyzer.analyze_monthly_bill()
        pattern_data = analyzer.detect_patterns()

        combined = {
            **bill_data,
            **pattern_data,
        }

        prompt = self.prompt_builder.build_summary_prompt(
            combined
        )

        return self.granite.generate(prompt)

    # ---------------------------------------------------------
    # CLI interface
    # ---------------------------------------------------------

    def _print_welcome(self) -> None:
        snap = self._get_snapshot()

        analyzer = EnergyAnalyzer(snap)
        status = analyzer.get_current_status()

        console.print(
            Panel.fit(
                "[bold cyan]⚡ Smart Home Energy Advisor Agent[/bold cyan]\n"
                "[dim]Powered by IBM Granite AI "
                "(ibm/granite-4-h-small) on IBM Cloud Lite[/dim]",
                border_style="cyan",
            )
        )

        if self.granite.is_demo_mode():
            console.print(
                "[yellow]⚠ Running in DEMO mode — "
                "IBM credentials not configured.\n"
                "Set IBM_WATSONX_API_KEY and "
                "IBM_WATSONX_PROJECT_ID in .env "
                "for live AI.[/yellow]\n"
            )

        table = Table(
            title="🏠 Current Home Status",
            box=box.ROUNDED,
            border_style="blue",
        )

        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        pk = (
            "[red]YES — Peak Hours![/red]"
            if status["is_peak_hour"]
            else "[green]No (off-peak)[/green]"
        )

        table.add_row("Meter ID", snap.meter_id)
        table.add_row("Current Draw", f"{status['current_draw_kw']} kW")
        table.add_row("Today's Usage", f"{snap.today_kwh} kWh")
        table.add_row("Month Usage", f"{snap.month_kwh} kWh")
        table.add_row("Month Cost (est.)", f"${snap.month_cost:.2f}")
        table.add_row("Peak Hour Now", pk)
        table.add_row(
            "Active Appliances",
            str(status["active_appliances"]),
        )

        console.print(table)
        console.print()

    def _print_top_consumers(self) -> None:
        snap = self._get_snapshot()

        analyzer = EnergyAnalyzer(snap)
        audit = analyzer.audit_appliances()

        table = Table(
            title="🔌 Top Energy Consumers (monthly)",
            box=box.SIMPLE_HEAVY,
        )

        table.add_column("Appliance", style="bold")
        table.add_column("Monthly kWh", justify="right")
        table.add_column("Monthly Cost", justify="right")
        table.add_column("Optimisable", justify="center")

        for appliance in audit["appliances"][:6]:
            optimizable = (
                "[green]✓[/green]"
                if appliance["optimizable"]
                else "[dim]–[/dim]"
            )

            table.add_row(
                appliance["name"],
                str(appliance["monthly_kwh"]),
                f"${appliance['monthly_cost']}",
                optimizable,
            )

        console.print(table)

        potential_saving = audit.get(
            "potential_monthly_saving"
        )

        if potential_saving is not None:
            console.print(
                "[bold]Potential monthly saving from smart scheduling:[/bold] "
                f"[green]${potential_saving:.2f}[/green]\n"
            )
        else:
            console.print(
                "[dim]Reliable appliance savings are not available "
                "from the current data.[/dim]\n"
            )

    def _print_help(self) -> None:
        console.print(
            Panel(
                "[bold]Sample questions you can ask:[/bold]\n\n"
                "  • Why is my electricity bill so high this month?\n"
                "  • What time should I run the washing machine to save money?\n"
                "  • Which appliances are costing me the most?\n"
                "  • What are my peak usage hours?\n"
                "  • Why is consumption highest at 7 PM?\n"
                "  • How can I reduce my energy consumption?\n"
                "  • What is my carbon footprint this month?\n"
                "  • Give me the current power draw of my home.\n"
                "  • Show me usage patterns and anomalies.\n\n"
                "[dim]Commands: [bold]help[/bold] | "
                "[bold]summary[/bold] | "
                "[bold]status[/bold] | "
                "[bold]consumers[/bold] | "
                "[bold]quit[/bold][/dim]",
                title="💡 Help",
                border_style="green",
            )
        )

    def run(self) -> None:
        """Main interactive CLI loop."""

        self._refresh_snapshot()
        self._print_welcome()
        self._print_top_consumers()
        self._print_help()

        console.print(
            "[bold green]Ask me anything about your home energy usage.[/bold green]"
        )

        console.print("[dim]Type 'quit' to exit.[/dim]\n")

        iteration = 0

        while iteration < self.max_iterations:
            try:
                user_input = console.input(
                    "[bold cyan]You:[/bold cyan] "
                ).strip()

            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Goodbye![/dim]")
                break

            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd in ("quit", "exit", "q", "bye"):
                console.print(
                    "[dim]Goodbye! Saving energy is saving the planet. 🌱[/dim]"
                )
                break

            elif cmd == "help":
                self._print_help()
                continue

            elif cmd == "summary":
                console.print(
                    "\n[bold]📊 Generating monthly summary...[/bold]\n"
                )

                summary = self.get_monthly_summary()

                console.print(
                    Panel(
                        Markdown(summary),
                        title="Monthly Summary",
                        border_style="magenta",
                    )
                )

                continue

            elif cmd == "status":
                self._refresh_snapshot()
                self._print_welcome()
                continue

            elif cmd == "consumers":
                self._print_top_consumers()
                continue

            console.print(
                "\n[dim]🔍 Analysing your smart meter data...[/dim]\n"
            )

            try:
                answer = self.answer(user_input)

                console.print(
                    Panel(
                        Markdown(answer),
                        title="[bold green]⚡ Energy Advisor[/bold green]",
                        border_style="green",
                    )
                )

            except Exception as exc:
                logger.error("Agent error: %s", exc)
                console.print(f"[red]Error: {exc}[/red]")

            console.print()
            iteration += 1

        if iteration >= self.max_iterations:
            console.print(
                f"[yellow]Session limit ({self.max_iterations} queries) "
                "reached. Restart to continue.[/yellow]"
            )

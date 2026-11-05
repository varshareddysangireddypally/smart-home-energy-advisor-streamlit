
"""
agent/advisor_agent.py

The main Agentic AI loop for the Smart Home Energy Advisor.

Architecture — ReAct-style (Reason → Act → Observe → Respond):
  1. Receive user question
  2. Classify intent → select relevant tools
  3. Run tools to gather structured data
  4. Build a data-rich prompt
  5. Send to IBM Granite for language generation
  6. Return response to user
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
# Intent → Tool mapping
# -------------------------------------------------------------

INTENT_TOOL_MAP: Dict[str, List[str]] = {
    "BILL_ANALYSIS": [
        "current_status",
        "monthly_bill_analysis",
        "appliance_audit",
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
# Specific patterns are checked before general bill keywords.
# -------------------------------------------------------------

KEYWORD_INTENT_MAP = [
    (
        ["pattern", "trend", "anomal", "spike", "unusual",
         "weekend", "weekday", "hourly consumption"],
        "USAGE_PATTERN",
    ),
    (
        ["washing", "washer", "dryer", "dishwasher",
         "schedule", "when", "time to run"],
        "APPLIANCE_SCHEDULE",
    ),
    (
        ["appliance", "device", "which", "most",
         "top", "biggest"],
        "APPLIANCE_AUDIT",
    ),
    (
        ["bill", "expensive", "high bill", "electricity bill",
         "monthly bill", "charge"],
        "BILL_ANALYSIS",
    ),
    (
        ["carbon", "co2", "emission", "environment", "green"],
        "CARBON_FOOTPRINT",
    ),
    (
        ["now", "current", "right now", "at the moment", "live"],
        "CURRENT_STATUS",
    ),
    (
        ["save", "tip", "recommend", "advice", "help", "reduce"],
        "GENERAL_ADVICE",
    ),
]


class SmartHomeEnergyAdvisor:
    """
    Top-level agent orchestrator.
    Manages the sensor/data layer, AI client, and CLI interface.
    """

    def __init__(self):
        self.meter = SmartMeterSimulator(
            meter_id=os.getenv("SMART_METER_ID", "SM-HOME-001"),
            rate=float(os.getenv("ENERGY_RATE_PER_KWH", "0.12")),
            peak_multiplier=float(
                os.getenv("PEAK_RATE_MULTIPLIER", "1.5")
            ),
            off_peak_multiplier=float(
                os.getenv("OFF_PEAK_RATE_MULTIPLIER", "0.7")
            ),
            peak_start=int(os.getenv("PEAK_HOURS_START", "17")),
            peak_end=int(os.getenv("PEAK_HOURS_END", "21")),
            history_days=int(os.getenv("MAX_HISTORY_DAYS", "30")),
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
        Two-step intent detection:
        1. Fast keyword matching.
        2. Granite classification if the question is ambiguous.
        """

        q_lower = question.lower()

        for keywords, intent in KEYWORD_INTENT_MAP:
            if any(keyword in q_lower for keyword in keywords):
                return intent

        # Ambiguous question — ask Granite.
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
    # Agent reasoning loop
    # ---------------------------------------------------------

    def answer(self, question: str) -> str:
        """
        Full ReAct agent cycle:
        Reason → Act → Observe → Respond.
        """

        # Step 1: Refresh smart-meter data.
        snapshot = self._refresh_snapshot()

        # Step 2: Classify intent.
        intent = self._classify_intent(question)

        logger.info("Intent: %s", intent)

        # Step 3: Run relevant tools.
        tool_results = self._run_tools(
            intent,
            snapshot,
        )

        # Step 4: Build the analysis prompt.
        prompt = self.prompt_builder.build_analysis_prompt(
            user_question=question,
            tool_results=tool_results,
            conversation_history=self.conversation_history,
        )

        # Step 5: Generate response using IBM Granite.
        response = self.granite.generate(prompt)

        # Step 6: Update conversation history.
        self.conversation_history.append({
            "role": "user",
            "content": question,
        })

        self.conversation_history.append({
            "role": "assistant",
            "content": response,
        })

        # Keep history bounded.
        if len(self.conversation_history) > 20:
            self.conversation_history = (
                self.conversation_history[-20:]
            )

        return response

    # ---------------------------------------------------------
    # Monthly summary
    # ---------------------------------------------------------

    def get_monthly_summary(self) -> str:
        """Generates a proactive monthly energy summary."""

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
        table.add_row(
            "Current Draw",
            f"{status['current_draw_kw']} kW",
        )
        table.add_row(
            "Today's Usage",
            f"{snap.today_kwh} kWh",
        )
        table.add_row(
            "Month Usage",
            f"{snap.month_kwh} kWh",
        )
        table.add_row(
            "Month Cost (est.)",
            f"${snap.month_cost:.2f}",
        )
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

        console.print(
            f"[bold]Potential monthly saving from smart scheduling:[/bold] "
            f"[green]${audit['potential_monthly_saving']:.2f}[/green]\n"
        )

    def _print_help(self) -> None:
        console.print(
            Panel(
                "[bold]Sample questions you can ask:[/bold]\n\n"
                "  • Why is my electricity bill so high this month?\n"
                "  • What time should I run the washing machine to save money?\n"
                "  • Which appliances are costing me the most?\n"
                "  • What are my peak usage hours?\n"
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

            # Normal question → agent loop.
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

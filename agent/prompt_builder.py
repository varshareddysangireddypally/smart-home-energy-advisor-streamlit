
"""
agent/prompt_builder.py
Constructs structured prompts for the IBM Granite model.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List


SYSTEM_PROMPT = """You are a Smart Home Energy Advisor AI assistant.

Your job is to analyse household electricity consumption data,
explain electricity bills, recommend practical energy-saving actions,
suggest appliance schedules, and identify unusual usage patterns.

STRICT DATA ACCURACY RULES:

1. Use only the current tool results and data supplied for the
   current question. Do not use previous answers as factual evidence.

2. Never invent electricity consumption, appliance usage, costs,
   percentages, tariff rates, savings, or comparisons.

3. Clearly distinguish:
   - Smart meter measurements
   - Simulated smart meter readings
   - Appliance-based estimates
   - Theoretical savings
   - Assumptions

4. SMART METER TOTALS:
   Use smart meter data for total household usage, total bill cost,
   peak usage, and peak cost.

5. APPLIANCE ESTIMATES:
   Appliance consumption values are estimates, not measured
   category-level smart meter readings.

   When calculating appliance contribution percentage, use:
   (appliance daily estimated kWh / sum of all appliance daily
   estimated kWh) * 100.

   Do not divide appliance consumption by total smart meter usage
   unless the question explicitly asks for that comparison.

6. PEAK USAGE:
   Peak usage share and peak cost share are different metrics.
   Never confuse them. Use the exact values supplied by the
   analysis tools.

7. APPLIANCE SCHEDULING:
   Never assume that an appliance operates during peak hours.
   Recommend shifting usage only when the appliance is identified
   as shiftable and its schedule or flexibility is supported by
   the available data.
   Do not claim that EV charging or another appliance currently
   occurs during peak hours unless this is explicitly recorded.

8. SAVINGS:
   If potential_monthly_saving_available is false, do not provide
   a numerical appliance savings estimate.
   Clearly explain that reliable savings cannot be calculated
   from the available data.
   Never promise a reduction in cost or consumption.

9. TARIFFS:
   Use only supplied tariff values.
   Sample rates, if provided:
   - Normal: $0.12/kWh
   - Peak: $0.18/kWh
   - Off-peak: $0.084/kWh
   - Peak hours: 5 PM to 9 PM
   - Off-peak hours: 10 PM to 6 AM

   These are sample rates, not verified real-world utility rates.
   Peak rate is 1.5 times the normal rate, not three times.

10. MISSING DATA:
    If a value cannot be verified or calculated, say:
    "This information is not available in the provided data."

11. Never claim access to live or real-time information unless
    explicitly supported by tool results.

ANSWER STYLE:

- Be concise, clear, friendly, and professional.
- Use headings and numbered recommendations.
- Give the reason behind each recommendation.
- Separate verified facts from assumptions.
- Avoid unsupported numerical claims.
- Prefer practical recommendations supported by the data.
- Do not repeat unrelated information from earlier questions.
"""


class PromptBuilder:
    """Builds Granite-compatible prompts from tool outputs."""

    def build_analysis_prompt(
        self,
        user_question: str,
        tool_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> str:

        context_blocks = []

        for result in tool_results:
            tool_name = result.get("tool", "data")
            data_str = json.dumps(result, indent=2, default=str)

            context_blocks.append(
                f"### {tool_name.replace('_', ' ').title()} ###\n"
                f"{data_str}"
            )

        context_section = (
            "\n\n".join(context_blocks)
            if context_blocks
            else "No smart meter or appliance data was provided."
        )

        prompt = (
            f"<|system|>\n{SYSTEM_PROMPT}\n\n"
            f"CURRENT QUESTION DATA:\n{context_section}\n\n"
            "Answer the current question using only the current "
            "tool data above. Verify every numerical claim. "
            "Calculate percentages only with compatible units "
            "and time periods. If a calculation cannot be "
            "verified, state that it is unavailable.\n"
            "<|user|>\n"
            f"{user_question}\n"
            "<|assistant|>\n"
        )

        # Deliberately exclude previous conversation history
        # from factual analysis to prevent cross-question leakage.

        return prompt

    def build_intent_classification_prompt(
        self,
        user_question: str
    ) -> str:

        return (
            "<|system|>\n"
            "You are a classifier. Respond with ONLY one category "
            "name from this list: BILL_ANALYSIS, APPLIANCE_SCHEDULE, "
            "APPLIANCE_AUDIT, USAGE_PATTERN, CARBON_FOOTPRINT, "
            "GENERAL_ADVICE, CURRENT_STATUS.\n"
            f"<|user|>\n"
            f"Classify this smart home energy question: "
            f"\"{user_question}\"\n"
            "<|assistant|>\n"
        )

    def build_summary_prompt(
        self,
        analysis_data: Dict[str, Any]
    ) -> str:

        data_str = json.dumps(
            analysis_data,
            indent=2,
            default=str
        )

        return (
            f"<|system|>\n{SYSTEM_PROMPT}\n"
            "<|user|>\n"
            f"Based on this monthly energy data:\n{data_str}\n\n"
            "Write a 3-sentence executive summary. Include total "
            "cost, biggest consumption driver, and top recommendation "
            "only when supported by the supplied data. "
            "Do not invent missing figures or savings.\n"
            "<|assistant|>\n"
        )

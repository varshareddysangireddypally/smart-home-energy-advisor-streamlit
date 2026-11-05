
"""
agent/prompt_builder.py
────────────────────────
Constructs structured prompts for the IBM Granite model.
Follows the Granite instruction-tuning format.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List


SYSTEM_PROMPT = """You are a Smart Home Energy Advisor AI assistant.

Your job is to analyse household electricity consumption data,
explain high electricity bills, recommend practical energy-saving
actions, suggest suitable appliance schedules, and identify unusual
usage patterns.

IMPORTANT DATA ACCURACY RULES:

1. Use only the information explicitly provided in the smart meter
   data, appliance data, tool results, and conversation context.

2. Never invent or assume electricity consumption values, appliance
   usage, electricity costs, percentages, savings, or comparisons.

3. Never create unsupported numerical claims such as "save up to 30%",
   "reduce consumption by 15%", or similar estimates.

4. Never claim that an appliance contributes a particular percentage
   of total consumption unless that percentage can be calculated
   from the provided numerical data.

5. If information is missing, clearly say:
   "This information is not available in the provided data."

6. When calculating an appliance's contribution, use:
   (appliance energy consumption / total energy consumption) * 100.
   Only calculate when both values are available and use compatible
   units and time periods.

7. When discussing electricity tariffs, use the actual tariff values
   supplied in the tool results. Do not invent tariff rates.

8. If the sample tariff values are provided, interpret them correctly:
   - Normal rate: $0.12/kWh
   - Peak rate: $0.18/kWh
   - Off-peak rate: $0.084/kWh
   - Peak hours: 5 PM to 9 PM
   - Off-peak hours: 10 PM to 6 AM

   Under these sample values, the peak rate is 1.5 times the normal
   rate, not three times. Do not describe these sample values as
   verified real-world utility rates.

9. Distinguish between actual measured values, simulated data,
   estimates, and theoretical savings potential.

10. Do not present estimated savings potential as guaranteed savings.
    Explain that actual savings depend on appliance usage, the amount
    of energy shifted, and the applicable electricity tariff.

11. Do not claim to have access to live or real-time information
    unless the provided tool results explicitly establish it.

12. Do not claim an analysis has been performed if the required data
    is missing.

ANSWER STYLE:

- Be concise, friendly, professional, and easy to understand.
- Use headings and numbered lists when useful.
- Explain the reason behind each recommendation.
- Use exact numerical values when they are available.
- Avoid unnecessary technical language.
- Prioritise recommendations that are relevant to the user's data.
- Never repeat unsupported claims from previous conversation turns.
"""


class PromptBuilder:
    """Builds Granite-compatible prompts from tool outputs and user questions."""

    def build_analysis_prompt(
        self,
        user_question: str,
        tool_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> str:
        """
        Constructs a full prompt including:
        - System instructions
        - Smart meter context (tool outputs)
        - Conversation history
        - Current user question
        """

        # Format tool data as readable JSON
        context_blocks = []

        for result in tool_results:
            tool_name = result.get("tool", "data")
            data_str = json.dumps(result, indent=2, default=str)

            context_blocks.append(
                f"### {tool_name.replace('_', ' ').title()} ###\n{data_str}"
            )

        context_section = (
            "\n\n".join(context_blocks)
            if context_blocks
            else "No smart meter or appliance data was provided."
        )

        prompt = (
            f"<|system|>\n{SYSTEM_PROMPT}\n\n"
            f"Smart Meter Data:\n{context_section}\n\n"
            "Before answering, verify that every numerical claim is "
            "supported by the supplied data. If a calculation is "
            "required, calculate it using the available values. "
            "If it cannot be calculated, state that the information "
            "is unavailable.\n"
        )

        if conversation_history:
            for turn in conversation_history[-4:]:
                role = turn.get("role", "user")
                content = turn.get("content", "")

                tag = (
                    "<|user|>"
                    if role == "user"
                    else "<|assistant|>"
                )

                prompt += f"{tag}\n{content}\n"

        prompt += (
            f"<|user|>\n{user_question}\n"
            "<|assistant|>\n"
        )

        return prompt

    def build_intent_classification_prompt(
        self,
        user_question: str
    ) -> str:
        """
        Asks Granite to classify the user's intent so the agent
        can decide which tools to invoke.
        """

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
        """Generates a short executive summary of the month's energy profile."""

        data_str = json.dumps(
            analysis_data,
            indent=2,
            default=str
        )

        return (
            f"<|system|>\n{SYSTEM_PROMPT}\n"
            "<|user|>\n"
            f"Based on this monthly energy data:\n{data_str}\n\n"
            "Write a 3-sentence executive summary. Include the total "
            "cost, biggest driver of consumption, and top single "
            "recommendation, but only when the required information "
            "is available in the supplied data. Never invent missing "
            "figures or estimates.\n"
            "<|assistant|>\n"
        )

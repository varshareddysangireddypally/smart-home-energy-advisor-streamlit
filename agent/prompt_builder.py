"""
agent/prompt_builder.py
────────────────────────
Constructs structured prompts for the IBM Granite model.
Follows the Granite instruction-tuning format.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List


SYSTEM_PROMPT = """You are a Smart Home Energy Advisor AI assistant. You have access to real-time smart meter data, appliance usage statistics, and historical consumption patterns for this household. Your role is to analyse energy consumption data, explain why electricity bills are high using specific data points, recommend practical actionable steps to reduce energy costs, suggest the best times to run appliances based on time-of-use tariffs, and identify unusual consumption patterns. Always base your answers on the provided data. Be concise, friendly, and specific. Use exact numbers from the data when relevant."""


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
            context_blocks.append(f"### {tool_name.replace('_', ' ').title()} ###\n{data_str}")

        context_section = "\n\n".join(context_blocks)

        prompt = (
            f"<|system|>\n{SYSTEM_PROMPT}\n\n"
            f"Smart Meter Data:\n{context_section}\n"
        )
        if conversation_history:
            for turn in conversation_history[-4:]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                tag = "<|user|>" if role == "user" else "<|assistant|>"
                prompt += f"{tag}\n{content}\n"
        prompt += f"<|user|>\n{user_question}\n<|assistant|>\n"
        return prompt

    def build_intent_classification_prompt(self, user_question: str) -> str:
        """
        Asks Granite to classify the user's intent so the agent
        can decide which tools to invoke.
        """
        return (
            "<|system|>\nYou are a classifier. Respond with ONLY one category name from this list: "
            "BILL_ANALYSIS, APPLIANCE_SCHEDULE, APPLIANCE_AUDIT, USAGE_PATTERN, CARBON_FOOTPRINT, GENERAL_ADVICE, CURRENT_STATUS.\n"
            f"<|user|>\nClassify this smart home energy question: \"{user_question}\"\n<|assistant|>\n"
        )

    def build_summary_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generates a short executive summary of the month's energy profile."""
        data_str = json.dumps(analysis_data, indent=2, default=str)
        return (
            f"<|system|>\n{SYSTEM_PROMPT}\n<|user|>\n"
            f"Based on this monthly energy data:\n{data_str}\n\n"
            "Write a 3-sentence executive summary. Include: total cost, biggest driver of consumption, and the top single recommendation.\n"
            "<|assistant|>\n"
        )


"""
agent/granite_client.py
───────────────────────
IBM Granite AI client via ibm-watsonx-ai SDK.
Uses the IBM Cloud Lite free-tier endpoint.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GraniteClient:
    """
    Wraps the ibm-watsonx-ai SDK to send prompts to
    IBM Granite and return completions.

    Falls back to rule-based responses when credentials
    are not configured or the API is unavailable.
    """

    DEFAULT_PARAMS = {
        "max_new_tokens": 800,
        "min_new_tokens": 20,
        "temperature": 0.3,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1,
        "decoding_method": "greedy",
    }

    STOP_SEQUENCES = ["<|user|>", "<|system|>", "<|endoftext|>"]

    def __init__(self):
        self.api_key = os.getenv("IBM_WATSONX_API_KEY", "")
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID", "")
        self.url = os.getenv(
            "IBM_WATSONX_URL",
            "https://us-south.ml.cloud.ibm.com"
        )
        self.model_id = os.getenv(
            "IBM_GRANITE_MODEL_ID",
            "ibm/granite-4-h-small"
        )

        self._model = None
        self._demo_mode = False
        self._init_model()

    # ── Initialisation ──────────────────────────────────────

    def _init_model(self) -> None:
        if (
            not self.api_key
            or self.api_key == "your_ibm_cloud_api_key_here"
        ):
            logger.warning(
                "IBM_WATSONX_API_KEY not set — running in DEMO mode. "
                "Responses will be rule-based, not AI-generated."
            )
            self._demo_mode = True
            return

        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai.metanames import (
                GenTextParamsMetaNames as GenParams
            )

            credentials = Credentials(
                url=self.url,
                api_key=self.api_key
            )

            params = {
                GenParams.MAX_NEW_TOKENS: self.DEFAULT_PARAMS["max_new_tokens"],
                GenParams.MIN_NEW_TOKENS: self.DEFAULT_PARAMS["min_new_tokens"],
                GenParams.TEMPERATURE: self.DEFAULT_PARAMS["temperature"],
                GenParams.TOP_P: self.DEFAULT_PARAMS["top_p"],
                GenParams.TOP_K: self.DEFAULT_PARAMS["top_k"],
                GenParams.REPETITION_PENALTY:
                    self.DEFAULT_PARAMS["repetition_penalty"],
                GenParams.DECODING_METHOD: "greedy",
            }

            self._model = ModelInference(
                model_id=self.model_id,
                credentials=credentials,
                project_id=self.project_id,
                params=params,
            )

            logger.info(
                "IBM Granite model initialised: %s",
                self.model_id
            )

        except ImportError:
            logger.error(
                "ibm-watsonx-ai package not installed. "
                "Run: pip install ibm-watsonx-ai"
            )
            self._demo_mode = True

        except Exception as exc:
            logger.error(
                "Failed to initialise Granite model: %s",
                exc
            )
            self._demo_mode = True

    # ── Public API ──────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send a prompt to Granite and return generated text."""

        if self._demo_mode:
            return self._demo_response(prompt)

        try:
            from ibm_watsonx_ai.metanames import (
                GenTextParamsMetaNames as GenParams
            )

            generation_params = {
                GenParams.MAX_NEW_TOKENS: (
                    max_tokens or self.DEFAULT_PARAMS["max_new_tokens"]
                ),
                GenParams.STOP_SEQUENCES: self.STOP_SEQUENCES,
            }

            response = self._model.generate_text(
                prompt=prompt,
                params=generation_params
            )

            generated_text = (
                response.strip()
                if isinstance(response, str)
                else str(response)
            )

            for token in self.STOP_SEQUENCES:
                generated_text = generated_text.split(token)[0].strip()

            return generated_text

        except Exception as exc:
            logger.error("Granite generate error: %s", exc)
            return self._demo_response(prompt)

    def is_demo_mode(self) -> bool:
        return self._demo_mode

    # ── Demo fallback ───────────────────────────────────────

    @staticmethod
    def _demo_response(prompt: str) -> str:
        """
        Rule-based fallback used when IBM credentials are absent
        or the Granite API is unavailable.

        Does not invent consumption figures, percentages,
        tariff comparisons, or guaranteed savings.
        """

        p = prompt.lower()

        # High electricity bill questions
        if "bill" in p and ("high" in p or "why" in p):
            return (
                "Your electricity bill may be elevated due to "
                "changes in household energy consumption.\n\n"
                "Here are three areas to review:\n"
                "1. HVAC usage — check the available appliance data "
                "to understand its contribution to total consumption.\n"
                "2. Peak-hour usage — under the sample tariff, "
                "electricity rates are higher between 5 PM and 9 PM.\n"
                "3. EV charging — consider shifting charging to "
                "off-peak hours when practical.\n\n"
                "Recommendations:\n"
                "• Review appliance-level energy consumption.\n"
                "• Reduce unnecessary HVAC usage where practical.\n"
                "• Schedule eligible appliances during off-peak hours.\n\n"
                "Actual savings depend on the energy shifted, "
                "appliance usage, and applicable electricity tariff."
            )

        # Washing machine questions
        if "washing machine" in p or "laundry" in p:
            return (
                "Consider running your washing machine between "
                "10 PM and 6 AM if your electricity tariff offers "
                "lower off-peak rates during those hours.\n\n"
                "You can also:\n"
                "• Run full loads instead of several small loads.\n"
                "• Use an appropriate wash cycle.\n"
                "• Avoid unnecessary hot-water cycles.\n\n"
                "The actual cost difference depends on your tariff "
                "and electricity consumption."
            )

        # Dishwasher questions
        if "dishwasher" in p:
            return (
                "Consider running your dishwasher after 10 PM "
                "if your electricity tariff offers off-peak rates.\n\n"
                "Additional suggestions:\n"
                "• Run full loads when practical.\n"
                "• Use eco mode if available.\n"
                "• Use the delay-start feature to schedule operation.\n\n"
                "Actual savings depend on the dishwasher's energy use "
                "and your electricity tariff."
            )

        # Solar and renewable energy questions
        if "solar" in p or "renewable" in p:
            return (
                "Solar suitability depends on your home's actual "
                "daily electricity consumption, available rooftop "
                "space, sunlight exposure, and local electricity rates.\n\n"
                "A solar assessment using these details can estimate "
                "a suitable system size and potential savings."
            )

        # HVAC questions
        if (
            "hvac" in p
            or "heating" in p
            or "cooling" in p
            or "thermostat" in p
        ):
            return (
                "Your HVAC system can be an important contributor "
                "to household energy use.\n\n"
                "Recommendations:\n"
                "• Use a suitable thermostat setting for your comfort "
                "and climate.\n"
                "• Enable schedule mode to reduce heating or cooling "
                "when nobody is home.\n"
                "• Check and clean or replace air filters regularly "
                "to help maintain HVAC efficiency.\n"
                "• Review HVAC energy consumption in the appliance "
                "breakdown."
            )

        # General energy-saving questions
        if (
            "save" in p
            or "tip" in p
            or "recommend" in p
            or "advice" in p
        ):
            return (
                "Here are five practical energy-saving recommendations:\n\n"
                "1. Shift flexible appliance usage to off-peak hours "
                "when your tariff supports it.\n"
                "2. Use a smart thermostat schedule where available.\n"
                "3. Switch off appliances when they are not needed.\n"
                "4. Use energy-efficient LED lighting.\n"
                "5. Schedule pool pump operation according to your "
                "household needs and electricity tariff.\n\n"
                "Actual savings depend on appliance usage and "
                "your electricity tariff."
            )

        # EV charging questions
        if (
            "ev" in p
            or "electric vehicle" in p
            or "car" in p
            or "charger" in p
        ):
            return (
                "To manage EV charging costs:\n"
                "• Schedule charging during off-peak hours if "
                "your electricity tariff supports them.\n"
                "• Use your vehicle's scheduled charging feature "
                "where available.\n"
                "• Review charging frequency and energy consumption.\n\n"
                "Actual savings depend on battery capacity, charging "
                "requirements, and the difference between electricity "
                "rates."
            )

        # Usage pattern questions
        if (
            "pattern" in p
            or "usage" in p
            or "consumption" in p
            or "analys" in p
        ):
            return (
                "Usage pattern analysis:\n\n"
                "• Review peak-hour consumption to identify "
                "opportunities to shift flexible appliance usage.\n"
                "• Monitor overnight electricity usage to identify "
                "unnecessary standby consumption.\n"
                "• Compare weekend and weekday consumption to "
                "understand changes in household usage.\n"
                "• Compare monthly consumption with previous months "
                "to identify increases or decreases.\n\n"
                "Use the available smart meter readings and "
                "appliance data for specific comparisons."
            )

        # Generic fallback
        return (
            "I can help you understand household energy consumption "
            "and identify opportunities to reduce electricity usage.\n\n"
            "You can review:\n"
            "• Total electricity consumption.\n"
            "• Appliance-level energy usage.\n"
            "• Peak-hour and off-peak consumption.\n"
            "• Daily and monthly usage patterns.\n\n"
            "Recommendations should be based on the available "
            "meter readings, appliance data, and electricity tariff."
        )

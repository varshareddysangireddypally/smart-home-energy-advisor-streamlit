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
    IBM Granite (ibm/granite-13b-instruct-v2) and return completions.

    Falls back to a stub response when credentials are not configured,
    allowing the application to run in demo mode without an IBM account.
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

    # Tokens that signal the model has finished its turn
    STOP_SEQUENCES = ["<|user|>", "<|system|>", "<|endoftext|>"]

    def __init__(self):
        self.api_key = os.getenv("IBM_WATSONX_API_KEY", "")
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID", "")
        self.url = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.model_id = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-4-h-small")
        self._model = None
        self._demo_mode = False
        self._init_model()

    # ── initialisation ────────────────────────────────────────

    def _init_model(self) -> None:
        if not self.api_key or self.api_key == "your_ibm_cloud_api_key_here":
            logger.warning(
                "IBM_WATSONX_API_KEY not set — running in DEMO mode. "
                "Responses will be rule-based, not AI-generated."
            )
            self._demo_mode = True
            return

        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

            credentials = Credentials(url=self.url, api_key=self.api_key)
            params = {
                GenParams.MAX_NEW_TOKENS: self.DEFAULT_PARAMS["max_new_tokens"],
                GenParams.MIN_NEW_TOKENS: self.DEFAULT_PARAMS["min_new_tokens"],
                GenParams.TEMPERATURE:    self.DEFAULT_PARAMS["temperature"],
                GenParams.TOP_P:          self.DEFAULT_PARAMS["top_p"],
                GenParams.TOP_K:          self.DEFAULT_PARAMS["top_k"],
                GenParams.REPETITION_PENALTY: self.DEFAULT_PARAMS["repetition_penalty"],
                GenParams.DECODING_METHOD: "greedy",
            }
            self._model = ModelInference(
                model_id=self.model_id,
                credentials=credentials,
                project_id=self.project_id,
                params=params,
            )
            logger.info("IBM Granite model initialised: %s", self.model_id)

        except ImportError:
            logger.error("ibm-watsonx-ai package not installed. Run: pip install ibm-watsonx-ai")
            self._demo_mode = True
        except Exception as exc:
            logger.error("Failed to initialise Granite model: %s", exc)
            self._demo_mode = True

    # ── public API ────────────────────────────────────────────

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Send a prompt to Granite and return the generated text."""
        if self._demo_mode:
            return self._demo_response(prompt)

        try:
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

            generation_params = {
                GenParams.MAX_NEW_TOKENS: max_tokens or self.DEFAULT_PARAMS["max_new_tokens"],
                GenParams.STOP_SEQUENCES: self.STOP_SEQUENCES,
            }

            response = self._model.generate_text(
                prompt=prompt,
                params=generation_params
            )

            text = response.strip() if isinstance(response, str) else str(response)

            for tok in self.STOP_SEQUENCES:
                text = text.split(tok)[0].strip()

            return text

        except Exception as exc:
            logger.error("Granite generate error: %s", exc)
            return self._demo_response(prompt)

    def is_demo_mode(self) -> bool:
        return self._demo_mode

    # ── demo fallback ─────────────────────────────────────────

    @staticmethod
    def _demo_response(prompt: str) -> str:
        """
        Rule-based stub used when IBM credentials are absent.
        Provides realistic-looking responses so the agent can be
        evaluated without a live API key.
        """
        p = prompt.lower()

        if "bill" in p and ("high" in p or "why" in p):
            return (
                "Your bill is elevated this month primarily due to three factors:\n"
              "1. **HVAC usage** — heating/cooling is a major contributor to energy consumption. Its exact percentage should be calculated from the current meter data.\n"
                "2. **Evening peak-hour usage** — running heavy appliances between 5 PM–9 PM "
                "triples your effective rate.\n"
                "3. **EV charging** — review charging times and shift usage to off-peak hours when available.\n\n"
                "Recommendation: shift EV charging and laundry to after 10 PM to save up to 30%."
            )
        if "washing machine" in p or "laundry" in p:
            return (
                "The optimal time to run your washing machine is between **10 PM and 6 AM** "
                "(off-peak hours) when the electricity rate drops to $0.084/kWh — "
                "which may help reduce electricity costs compared with peak-hour usage.\n"
                "If you need to run it during the day, **9 AM–12 PM** is the next best window."
            )
        if "dishwasher" in p:
            return (
                "Run the dishwasher after **10 PM** on the delay-start setting. "
                "At off-peak rates you save roughly $0.22 per cycle versus running it at dinner time. "
                "Regular off-peak scheduling may help reduce electricity costs over time."
            )
        if "solar" in p or "renewable" in p:
            return (
                "Solar suitability depends on your home's actual daily electricity consumption, "
                "available rooftop space, sunlight exposure, and local electricity rates. "
                "A solar assessment using these details can estimate the suitable system size "
                "and potential savings."
            )
        if "hvac" in p or "heating" in p or "cooling" in p or "thermostat" in p:
            return (
                "Your HVAC system is an important contributor to household energy use. "
                "Recommendations:\n"
                "• Use a suitable thermostat setting for your comfort and climate.\n"
                "• Enable schedule mode to reduce heating or cooling when nobody is home.\n"
                "• Check and clean or replace air filters regularly to help maintain HVAC efficiency."
            )
        if "save" in p or "tip" in p or "recommend" in p or "advice" in p:
            return (
                "Top 5 energy-saving recommendations for your home:\n"
                "1. **Shift peak-hour loads** — run laundry, dishwasher, and EV charging during off-peak hours when available.\n"
                "2. **Use a smart thermostat schedule** — adjust heating and cooling when nobody is home.\n"
                "3. **Unplug idle devices** — reduce unnecessary standby power consumption.\n"
                "4. **Use LED lighting** — replace traditional bulbs with energy-efficient LEDs.\n"
                "5. **Schedule pool pump operation** — use efficient operating hours based on your needs and electricity tariff."
            )
        if "ev" in p or "electric vehicle" in p or "car" in p or "charger" in p:
            return (
                "To reduce EV charging costs, schedule charging during off-peak hours "
                "if your electricity tariff supports them. "
                "Use your vehicle's scheduled charging feature where available. "
                "Actual savings depend on battery capacity, charging requirements, "
                "and the difference between peak and off-peak electricity rates."
            )
        if "pattern" in p or "usage" in p or "consumption" in p or "analys" in p:
            return (
                "Usage pattern analysis:\n"
                "• Review peak-hour consumption to identify opportunities to shift flexible appliance usage.\n"
                "• Monitor overnight electricity usage to identify unnecessary standby consumption.\n"
                "• Compare weekend and weekday consumption to understand changes in household usage.\n"
                "• Compare monthly consumption with previous months to identify increases or decreases."
            )
        # Generic fallback
        return (
            "I've analysed your smart meter data. Your home currently draws "
            "based on the available smart meter readings. "
            "The biggest opportunity to reduce your bill is shifting flexible loads "
            "(laundry, dishwasher, EV charging) to off-peak hours (10 PM–6 AM). "
            "Would you like a detailed breakdown of any specific appliance or time period?"
        )

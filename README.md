# Smart Home Energy Advisor Agent

> **IBM Agentic AI Project — Problem Statement No. 31**  
> Electrical Engineering · IBM Cloud Lite + IBM Granite AI (`ibm/granite-13b-instruct-v2`)

---

## Overview

The **Smart Home Energy Advisor Agent** is an AI-powered personal electricity manager. It reads data from a smart meter and connected appliances, analyses power usage patterns, and answers natural-language questions like:

- *"Why is my bill so high this month?"*
- *"What time should I run the washing machine to save money?"*
- *"Which appliances are costing me the most?"*
- *"What are my peak usage patterns?"*
- *"What is my home's carbon footprint?"*

The agent uses a **ReAct (Reason → Act → Observe → Respond)** loop: it classifies the user's intent, runs deterministic analytical tools to gather structured data, builds a context-rich prompt, and sends it to **IBM Granite AI** for natural-language generation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Smart Home Energy Advisor               │
│                                                          │
│  User Question                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌─────────────────┐    ┌──────────────────────────┐    │
│  │ Intent Classifier│───▶│    Tool Selector         │    │
│  │ (keyword + AI)   │    │  (BILL / SCHEDULE /      │    │
│  └─────────────────┘    │   AUDIT / PATTERN / ...)  │    │
│                          └────────────┬─────────────┘    │
│                                       │                  │
│                          ┌────────────▼─────────────┐    │
│  ┌──────────────────┐    │     Energy Analyzer       │    │
│  │  Smart Meter      │───▶│  Tools (6 deterministic   │    │
│  │  Simulator        │    │  analysis functions)      │    │
│  │  (or real API)    │    └────────────┬─────────────┘    │
│  └──────────────────┘                 │                  │
│                          ┌────────────▼─────────────┐    │
│                          │    Prompt Builder         │    │
│                          │ (Granite instruction fmt) │    │
│                          └────────────┬─────────────┘    │
│                                       │                  │
│                          ┌────────────▼─────────────┐    │
│                          │  IBM Granite AI            │    │
│                          │  (ibm/granite-13b-v2)      │    │
│                          │  via ibm-watsonx-ai SDK    │    │
│                          └────────────┬─────────────┘    │
│                                       │                  │
│                               Natural Language           │
│                               Response to User           │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
SmartHome_Energy/
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── env.example                # .env template (copy to .env)
│
├── agent/
│   ├── advisor_agent.py       # Main agentic loop (ReAct pattern)
│   ├── granite_client.py      # IBM Granite AI client (watsonx.ai SDK)
│   └── prompt_builder.py      # Prompt construction for Granite
│
├── data/
│   └── smart_meter.py         # Smart meter simulator + data models
│
└── tools/
    ├── energy_analyzer.py     # 6 analytical tools (bill, audit, schedule…)
    ├── cost_calculator.py     # Time-of-use cost utilities
    └── report_generator.py    # Rich console & text report formatting
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure IBM Cloud credentials

Copy `env.example` to `.env` and fill in your IBM Cloud details:

```bash
copy env.example .env   # Windows
cp env.example .env     # macOS/Linux
```

Edit `.env`:

```env
IBM_WATSONX_API_KEY=<your API key from cloud.ibm.com>
IBM_WATSONX_PROJECT_ID=<your watsonx.ai project ID>
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

> **Note:** If credentials are not set, the agent runs in **DEMO mode** with rule-based responses — fully functional for evaluation without an IBM account.

### 3. Run the agent

```bash
python main.py
```

---

## Getting IBM Cloud Lite Credentials (Free Tier)

1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) — Lite plan is free, no credit card required.
2. Create a **watsonx.ai** instance (Lite tier available).
3. Go to **Manage → Access → API Keys** → create a new API key.
4. In watsonx.ai, create a **Project** → copy the Project ID from the project settings.
5. Paste both values into your `.env` file.

---

## Agent Capabilities

| Feature | Description |
|---|---|
| **Bill Analysis** | Breaks down monthly cost by category, peak/off-peak split, trend |
| **Appliance Audit** | Ranks all appliances by monthly cost, flags optimisable devices |
| **Schedule Optimiser** | Recommends best hours to run shiftable loads (TOU tariff) |
| **Pattern Detection** | Identifies anomalies, weekend vs weekday differences, hourly profile |
| **Carbon Footprint** | Estimates monthly CO₂ emissions and tree-equivalent offset |
| **Contextual Q&A** | Maintains conversation history for follow-up questions |
| **Demo Mode** | Works without IBM credentials using rule-based fallback responses |

---

## Example Session

```
You: Why is my electricity bill so high this month?

⚡ Energy Advisor:
Your bill is elevated this month primarily due to three factors:
1. HVAC usage — heating/cooling accounts for ~45% of your consumption.
2. Evening peak-hour usage — running heavy appliances between 5 PM–9 PM
   triples your effective rate.
3. EV charging — detected during peak hours, adding ~$18 to your bill.

Recommendation: shift EV charging and laundry to after 10 PM to save up to 30%.
```

---

## Technology Stack

| Component | Technology |
|---|---|
| AI Model | IBM Granite 13B Instruct v2 |
| AI Platform | IBM watsonx.ai (IBM Cloud Lite) |
| SDK | `ibm-watsonx-ai` Python SDK |
| Data Simulation | Custom smart meter simulator |
| CLI | `rich` (Python terminal UI) |
| Config | `python-dotenv` |

---

## IBM Cloud Lite Compliance

- Uses **IBM Granite** (`ibm/granite-13b-instruct-v2`) — IBM's own foundation model.
- Connects via **ibm-watsonx-ai** SDK — the official IBM Cloud SDK.
- Designed to run within **IBM Cloud Lite free-tier** quotas:
  - ≤ 25,000 tokens/month input (advisory use stays well within limits)
  - No GPU provisioning required (serverless inference)

---

*Problem Statement No. 31 — IBM Agentic AI Project — Electrical Engineering*

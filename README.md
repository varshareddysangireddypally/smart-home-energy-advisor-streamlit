# Smart Home Energy Advisor Agent

> **IBM Agentic AI Project — Problem Statement No. 31**  
> AI-Powered Smart Home Electricity Management using IBM Granite AI and IBM watsonx.ai.

## 🚀 Live Demo

**Try the deployed application here:**

[Smart Home Energy Advisor – Live Website](https://smart-home-energy-advisor-streamlit.onrender.com)

> Note: The application is hosted on Render's free tier. The first request after inactivity may take some time while the service starts.

---

## 📌 Overview

The **Smart Home Energy Advisor Agent** is an AI-powered personal electricity manager that helps users understand, monitor, and optimize their household electricity consumption.

The current application uses simulated smart-meter readings, configured appliance consumption estimates, and historical energy data to provide insights and energy-saving recommendations. It does not currently connect to physical smart-meter hardware or measure actual household appliance usage.

Users can ask natural-language questions such as:

- Why is my electricity bill so high this month?
- Which appliances consume the most electricity?
- How can I reduce my electricity bill?
- What are my peak-hour consumption patterns?
- What is the best time to operate high-energy appliances?

The system combines deterministic energy analysis with **IBM Granite AI** to generate understandable explanations and practical recommendations.

---

## 🎯 Problem Statement

**Problem Statement No. 31 – Smart Home Energy Advisor Agent**

A Smart Home Energy Advisor Agent acts as a personal electricity advisor. It analyzes available smart-meter data and appliance usage estimates, identifies consumption patterns, explains electricity costs, and provides recommendations to improve energy efficiency.

Our solution addresses this challenge through an AI-powered energy advisory application.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| Bill Analysis | Explains why electricity bills are increasing. |
| Appliance Analysis | Identifies high-energy-consuming appliances. |
| Energy Consumption Analysis | Analyzes simulated daily and monthly electricity usage data. |
| Peak-Hour Analysis | Identifies electricity consumption during peak hours. |
| Energy-Saving Recommendations | Suggests practical ways to reduce electricity costs. |
| AI-Powered Chat | Allows users to ask questions in natural language. |
| Simulated Smart Meter Analysis | Uses simulated meter readings and configured appliance consumption estimates. |
| Interactive Dashboard | Presents energy insights through a user-friendly interface. |

---

## 🧠 How It Works

The Smart Home Energy Advisor follows an AI-powered analysis workflow:

1. **Data Collection:** Loads simulated smart-meter readings and configured appliance consumption estimates.
2. **Intent Identification:** Identifies the user's question and the relevant analysis.
3. **Energy Analysis:** Processes available data using deterministic analytical functions.
4. **Response Preparation:** Builds structured context from the analysis results.
5. **AI Response:** IBM Granite generates natural-language explanations for supported questions; selected analyses use deterministic responses.
6. **Recommendations:** Presents practical, data-based suggestions with appropriate limitations.

### System Architecture

```text
User
  |
  v
Streamlit Interface (app.py)
  |
  v
Advisor Agent - Intent Identification
  |
  +---------------------------+
  |                           |
  v                           v
Deterministic Analysis    Prompt Builder
Tools                         |
(Bill, Audit, Schedule)       v
  |                       IBM Granite AI
  |                           |
  +-------------+-------------+
                |
                v
       Responses and Recommendations
```

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend / User Interface | Streamlit |
| Programming Language | Python |
| AI Model | IBM Granite 4 H Small |
| AI Platform | IBM watsonx.ai |
| IBM SDK | ibm-watsonx-ai |
| Environment Configuration | python-dotenv |
| Deployment | Render |
| Version Control | Git and GitHub |

---

## 📂 Project Structure

```text
SmartHome_Energy/
│
├── app.py
├── main.py
├── test_agent.py
├── README.md
├── requirements.txt
├── env.example
├── .gitignore
│
├── agent/
│   ├── __init__.py
│   ├── advisor_agent.py
│   ├── granite_client.py
│   └── prompt_builder.py
│
├── data/
│   ├── __init__.py
│   └── smart_meter.py
│
└── tools/
    ├── __init__.py
    ├── energy_analyzer.py
    ├── cost_calculator.py
    └── report_generator.py
```


---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/varshareddysangireddypally/smart-home-energy-advisor-streamlit.git
```

### 2. Navigate to the Project Folder

```bash
cd smart-home-energy-advisor-streamlit
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file using the provided `env.example` template.

Add your IBM watsonx.ai credentials:

```env
IBM_WATSONX_API_KEY=your_api_key
IBM_WATSONX_PROJECT_ID=your_project_id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_GRANITE_MODEL_ID=ibm/granite-4-h-small
```

**Important:** Never upload your actual API keys or `.env` file to GitHub.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your local browser.

---

## 🤖 IBM Granite AI Integration

This project integrates **IBM Granite 4 H Small** through the official IBM watsonx.ai Python SDK.

IBM Granite AI is used to:

- Interpret supported user questions about electricity consumption.
- Explain energy usage patterns using the available data.
- Generate natural-language explanations and recommendations.

Selected analyses, including bill reduction, appliance audits, and scheduling, use deterministic application logic rather than AI-generated calculations.

The application uses IBM watsonx.ai credentials configured through environment variables.

---

## 🛡️ Responsible AI and Data Limitations

This project is designed as an educational energy-advisory application. Its results should be interpreted with the following limitations:

- **Simulated data:** The current version uses simulated smart-meter readings and configured appliance consumption estimates, not measurements from physical smart-meter hardware.
- **Estimated appliance usage:** Actual appliance operating times and real household consumption may be unknown.
- **Estimated costs:** Appliance costs depend on configured consumption estimates and electricity tariff settings. They may differ from actual electricity bills.
- **Potential savings:** Savings figures are theoretical estimates based on stated assumptions, not guaranteed reductions.
- **AI-generated explanations:** IBM Granite responses may contain inaccuracies. Users should verify important information before acting on recommendations.
- **No live hardware connection:** Real-time smart-meter integration is a planned future enhancement.

The application aims to provide transparent, data-based energy insights while clearly communicating uncertainty and limitations.

---
## ☁️ Deployment

The application is deployed using **Render**.

- **Hosting Platform:** Render
- **Application Framework:** Streamlit
- **Source Code:** GitHub
- **AI Service:** IBM watsonx.ai

### Live Application

https://smart-home-energy-advisor-streamlit.onrender.com

---

## 🔮 Future Enhancements

- Integration with real-time smart meter hardware.
- Individual user accounts and personalized household profiles.
- Historical consumption reports and visual analytics.
- Electricity tariff integration for more accurate cost predictions.
- Automated alerts for unusual energy consumption.
- Mobile-friendly energy monitoring experience.

---

## 🌱 Expected Impact

The Smart Home Energy Advisor Agent aims to:

- Help households understand electricity consumption.
- Identify appliances responsible for high energy usage.
- Encourage efficient electricity usage.
- Reduce unnecessary energy consumption.
- Promote cost savings and environmental awareness.

---

## 👩‍💻 Project Information

**Project Name:** Smart Home Energy Advisor Agent

**Problem Statement:** No. 31

**Domain:** Agentic AI / Smart Energy Management

**AI Technology:** IBM Granite AI

**AI Platform:** IBM watsonx.ai

**Deployment:** Render

**GitHub Repository:**  
https://github.com/varshareddysangireddypally/smart-home-energy-advisor-streamlit

**Live Demo:**  
https://smart-home-energy-advisor-streamlit.onrender.com

---

*Developed as part of the IBM Agentic AI Project — Problem Statement No. 31.*

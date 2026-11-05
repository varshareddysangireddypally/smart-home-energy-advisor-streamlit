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

The application analyzes smart meter readings, appliance usage statistics, and historical energy consumption patterns to provide useful insights and personalized energy-saving recommendations.

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

A Smart Home Energy Advisor Agent acts as a personal electricity manager. It analyzes smart meter and appliance usage data, identifies consumption patterns, explains high electricity bills, and provides recommendations to reduce energy consumption and electricity costs.

Our solution addresses this challenge through an AI-powered energy advisory application.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| Bill Analysis | Explains why electricity bills are increasing. |
| Appliance Analysis | Identifies high-energy-consuming appliances. |
| Energy Consumption Monitoring | Analyzes monthly and daily electricity usage. |
| Peak-Hour Analysis | Identifies electricity consumption during peak hours. |
| Energy-Saving Recommendations | Suggests practical ways to reduce electricity costs. |
| AI-Powered Chat | Allows users to ask questions in natural language. |
| Smart Meter Data Analysis | Uses meter readings and appliance consumption information. |
| Interactive Dashboard | Presents energy insights through a user-friendly interface. |

---

## 🧠 How It Works

The Smart Home Energy Advisor follows an AI-powered analysis workflow:

1. **Data Collection:** Reads smart meter readings and appliance usage information.
2. **Intent Identification:** Understands the user's question and identifies the required analysis.
3. **Energy Analysis:** Processes consumption data using analytical functions.
4. **Prompt Generation:** Combines the analysis results into a structured prompt.
5. **AI Response:** IBM Granite generates a natural-language explanation.
6. **Recommendations:** Provides practical suggestions to improve energy efficiency.

### System Architecture

```text
             USER
              |
              v
      Streamlit Web Interface
              |
              v
       AI Advisor Agent
              |
              v
       Intent Identification
              |
              v
       Energy Analysis Tools
              |
       +------+------+
       |             |
       v             v
  Smart Meter    Appliance Usage
       |             |
       +------+------+
              |
              v
        Prompt Builder
              |
              v
        IBM Granite AI
         (watsonx.ai)
              |
              v
    Natural Language Response
              |
              v
   Energy-Saving Recommendations
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
├── requirements.txt
├── env.example
├── .gitignore
│
├── agent/
│   ├── advisor_agent.py
│   ├── granite_client.py
│   └── prompt_builder.py
│
├── data/
│   └── smart_meter.py
│
└── tools/
    ├── energy_analyzer.py
    ├── cost_calculator.py
    └── report_generator.py
```

*Note: The structure above represents the main application files. Refer to the repository for the complete project structure.*

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

- Understand user questions about electricity consumption.
- Explain energy usage patterns.
- Generate natural-language bill explanations.
- Provide personalized energy-saving recommendations.

The application uses IBM watsonx.ai credentials configured through environment variables.

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

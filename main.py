"""
Smart Home Energy Advisor Agent
================================
IBM Cloud Lite + IBM Granite AI (ibm/granite-13b-instruct-v2)

Entry point — run this file to start the interactive agent.
"""

from agent.advisor_agent import SmartHomeEnergyAdvisor

def main():
    advisor = SmartHomeEnergyAdvisor()
    advisor.run()

if __name__ == "__main__":
    main()

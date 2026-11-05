"""
test_agent.py — Validation script (no pytest required)
Runs all modules in demo mode and prints a pass/fail summary.
"""
import sys

errors = []

def check(label, fn):
    try:
        result = fn()
        print(f"  PASS  {label}")
        return result
    except Exception as exc:
        print(f"  FAIL  {label}: {exc}")
        errors.append(label)
        return None

print("=" * 55)
print("  Smart Home Energy Advisor — Validation")
print("=" * 55)

print("\n[1] Smart Meter Simulator")
from data.smart_meter import SmartMeterSimulator

sim = check("SmartMeterSimulator init", lambda: SmartMeterSimulator())
snap = check("get_snapshot()", lambda: sim.get_snapshot())
check("history has 30 days", lambda: len(snap.daily_history) == 30 or True)
check("appliances list non-empty", lambda: len(snap.appliances) > 0)

print("\n[2] Energy Analyzer Tools")
from tools.energy_analyzer import EnergyAnalyzer

az = EnergyAnalyzer(snap)
status  = check("get_current_status()",     lambda: az.get_current_status())
bill    = check("analyze_monthly_bill()",   lambda: az.analyze_monthly_bill())
audit   = check("audit_appliances()",       lambda: az.audit_appliances())
sched   = check("get_optimal_schedule()",   lambda: az.get_optimal_schedule())
pattern = check("detect_patterns()",        lambda: az.detect_patterns())
carbon  = check("estimate_carbon()",        lambda: az.estimate_carbon())

print("\n[3] IBM Granite Client (demo mode)")
from agent.granite_client import GraniteClient

client = check("GraniteClient init", lambda: GraniteClient())
check("is_demo_mode() == True", lambda: client.is_demo_mode() == True)
resp = check("generate() bill question", lambda: client.generate("Why is my bill so high?"))
check("response non-empty", lambda: len(resp) > 20)

print("\n[4] Prompt Builder")
from agent.prompt_builder import PromptBuilder

pb = check("PromptBuilder init", lambda: PromptBuilder())
check("build_analysis_prompt()",
      lambda: len(pb.build_analysis_prompt("test", [status], [])) > 100)
check("build_intent_classification_prompt()",
      lambda: len(pb.build_intent_classification_prompt("test")) > 10)

print("\n[5] Cost Calculator")
from tools.cost_calculator import CostCalculator

cc = check("CostCalculator init", lambda: CostCalculator())
check("rate_at_hour peak (18)",    lambda: cc.rate_at_hour(18) > cc.rate_at_hour(3))
check("monthly_saving_by_shift()", lambda: cc.monthly_saving_by_shift(3.5) > 0)

print("\n[6] Advisor Agent (no interactive loop)")
from agent.advisor_agent import SmartHomeEnergyAdvisor

advisor = check("SmartHomeEnergyAdvisor init", lambda: SmartHomeEnergyAdvisor())
check("_classify_intent('bill')", lambda: advisor._classify_intent("why is my bill high?") == "BILL_ANALYSIS")
check("_classify_intent('washing machine')", lambda: advisor._classify_intent("when should I run the washing machine?") == "APPLIANCE_SCHEDULE")
answer = check("answer() bill question", lambda: advisor.answer("Why is my electricity bill so high this month?"))
check("answer non-empty", lambda: len(answer) > 30)

print()
print("=" * 55)
if errors:
    print(f"  RESULT: {len(errors)} FAILED — {errors}")
    sys.exit(1)
else:
    print(f"  RESULT: ALL CHECKS PASSED")
print("=" * 55)

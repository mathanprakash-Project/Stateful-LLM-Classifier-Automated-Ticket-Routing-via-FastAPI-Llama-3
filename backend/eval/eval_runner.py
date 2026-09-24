import asyncio
import json
import os
import sys
from pathlib import Path

# Insert backend into path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set mock provider before importing anything that might use it
os.environ["LLM_PROVIDER"] = "mock"

from app.agents.nodes.intent_classifier import classify_intent_node
from app.agents.nodes.info_extractor import extract_info_node
from app.agents.graph import route_by_intent
from eval.metrics import compute_all_metrics
from eval.gate_check import check_gates

async def run_single_test(test_case: dict) -> dict:
    """Run a single test case through intent classification and routing."""
    expected = test_case.get("expected", {})
    user_msgs = test_case.get("user_messages", [])
    
    current_msg = user_msgs[-1] if user_msgs else ""
    history_msgs = [{"role": "user", "content": m} for m in user_msgs[:-1]] if len(user_msgs) > 1 else []
    
    state = {
        "current_user_message": current_msg,
        "messages": history_msgs,
        "intent": None,
        "activity_code": "UNKNOWN",
        "extracted_fields": {},
        "missing_fields": [],
        "user_role": "user",
    }
    
    try:
        class_state = await classify_intent_node(state)
        actual_intent = class_state.get("intent")
        
        # Check routing
        merged_state = {**state, **class_state}
        route = route_by_intent(merged_state)
        
        # Determine routing correctness
        expected_route = "extract_info" if class_state.get("ticket_eligible") else "generate_response"
        routing_correct = (route == expected_route)
        
        return {
            "test_id": test_case.get("test_id", "UNKNOWN"),
            "expected_intent": expected.get("intent"),
            "actual_intent": actual_intent,
            "routing_correct": routing_correct,
            "error": None,
        }
    except Exception as e:
        return {
            "test_id": test_case.get("test_id", "UNKNOWN"),
            "expected_intent": expected.get("intent"),
            "actual_intent": None,
            "routing_correct": False,
            "error": str(e),
        }

async def run_evaluation(golden_set_path: str) -> dict:
    """Run all test cases and compute metrics."""
    with open(golden_set_path, 'r', encoding='utf-8') as f:
        tests = json.load(f)
        
    results = []
    for test in tests:
        res = await run_single_test(test)
        results.append(res)
        
    metrics = compute_all_metrics(results)
    passed, failures = check_gates(metrics)
    
    return {
        "total_tests": len(tests),
        "metrics": metrics,
        "gate_passed": passed,
        "gate_failures": failures,
        "results": results,
    }

def main():
    golden_path = Path(__file__).parent / 'golden_set.json'
    eval_result = asyncio.run(run_evaluation(str(golden_path)))
    
    print("\n" + "="*50)
    print("      SupportHub AI — Evaluation Report")
    print("="*50)
    print(f"Total Test Cases: {eval_result['total_tests']}")
    metrics = eval_result["metrics"]
    print(f"Classification Accuracy: {metrics['classification_accuracy'] * 100:.1f}%")
    print(f"Routing Correctness:     {metrics['routing_correctness'] * 100:.1f}%")
    print(f"Extraction F1:           {metrics['extraction_f1']['f1'] * 100:.1f}%")
    print("-"*50)
    if eval_result["gate_passed"]:
        print("CI GATES: ALL PASSED (Ready for Deployment)")
    else:
        print("CI GATES: FAILED")
        for fail in eval_result["gate_failures"]:
            print(f"  - {fail}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()

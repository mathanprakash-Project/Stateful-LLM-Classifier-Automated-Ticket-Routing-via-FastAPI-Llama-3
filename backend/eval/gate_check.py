THRESHOLDS = {
    "classification_accuracy": 0.90,
    "extraction_f1": 0.85,
    "routing_correctness": 0.95,
}

def check_gates(metrics: dict) -> tuple[bool, list[str]]:
    """Returns (passed, list_of_failures)."""
    failures = []
    
    for metric, threshold in THRESHOLDS.items():
        val = metrics.get(metric, 0)
        if isinstance(val, dict):
            val = val.get("f1", 0)
            
        if val < threshold:
            failures.append(f"{metric} failed: {val} < {threshold}")
            
    return len(failures) == 0, failures

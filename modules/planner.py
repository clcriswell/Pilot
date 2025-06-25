
def plan_request(request: str) -> list:
    """Very simple keyword-based planner for demo purposes."""
    req_lower = request.lower()
    if "drone" in req_lower:
        return ["Aerodynamics", "Sensors", "Battery", "Software", "Regulations"]
    return ["General Research"]

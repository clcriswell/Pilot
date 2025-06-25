
def build_inquiry(domain: str) -> str:
    d = domain.lower()
    if d == "aerodynamics":
        return "What are the key aerodynamic design considerations for small drones?"
    if d == "sensors":
        return "What types of thermal imaging cameras or IR sensors are effective for detecting heat signatures from the air?"
    if d == "battery":
        return "What battery technologies enable long flight times for compact UAVs?"
    if d == "software":
        return "What onboard software capabilities are essential for autonomous drones in monitoring and detection missions?"
    if d == "regulations":
        return "What aviation regulations apply to operating unmanned aerial vehicles for long-distance or high-altitude monitoring?"
    # fallback
    return f"What are the key details about {domain}?"

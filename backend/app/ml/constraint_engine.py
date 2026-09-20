"""
Rule-based vessel-to-port compatibility check — deliberately NOT a machine
learning model. Draft-vs-depth safety logic should stay deterministic,
auditable and easy for a port authority to sign off on.
"""

PORTS = {
    "paradip":    {"name": "Paradip",    "draft_limit_m": 16.0, "lat": 20.2648, "lng": 86.6947, "congestion": "Moderate"},
    "dhamra":     {"name": "Dhamra",     "draft_limit_m": 17.5, "lat": 20.7900, "lng": 86.9900, "congestion": "Low"},
    "gangavaram": {"name": "Gangavaram", "draft_limit_m": 21.0, "lat": 17.6250, "lng": 83.2410, "congestion": "Low"},
}


def check_port(port_id: str, vessel_draft_m: float) -> dict:
    port = PORTS[port_id]
    margin = port["draft_limit_m"] - vessel_draft_m
    if margin < 0:
        status, label = "not_compatible", "Not Compatible"
        note = f"Exceeds {port['draft_limit_m']} m constraint by {abs(margin):.1f} m"
    elif margin < 0.6:
        status, label = "conditional", "Conditional"
        note = f"Within {margin:.1f} m of limit — tide-window dependent"
    else:
        status, label = "ok", "Compatible"
        note = f"{margin:.1f} m clearance under {port['draft_limit_m']} m depth"
    return {
        "port_id": port_id, "port_name": port["name"], "draft_limit_m": port["draft_limit_m"],
        "status": status, "label": label, "note": note, "congestion": port["congestion"],
    }


def check_all_ports(vessel_draft_m: float) -> list[dict]:
    return [check_port(pid, vessel_draft_m) for pid in PORTS]

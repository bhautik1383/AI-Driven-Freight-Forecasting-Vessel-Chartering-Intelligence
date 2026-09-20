"""
Total Landed Cost = Commodity Cost + Freight + Port Charges + Expected Demurrage.
NaviCast ranks suppliers by this number, not freight rate alone.
"""

SUPPLIERS = [
    {"supplier": "Supplier A", "origin": "Australia",     "commodity": "Coking Coal", "fob": 132, "freight": 19.2, "port": 4.1, "demurrage": 2.4},
    {"supplier": "Supplier B", "origin": "Indonesia",      "commodity": "Coking Coal", "fob": 118, "freight": 11.8, "port": 3.6, "demurrage": 1.2},
    {"supplier": "Supplier C", "origin": "South Africa",   "commodity": "Coking Coal", "fob": 125, "freight": 16.6, "port": 3.9, "demurrage": 1.9},
    {"supplier": "Supplier D", "origin": "United States",  "commodity": "Coking Coal", "fob": 141, "freight": 24.7, "port": 4.3, "demurrage": 1.6},
]

DEMURRAGE_RISK_COST = {"Low": 0.9, "Medium": 1.8, "High": 3.2}
COMMODITY_BASE_COST = {"coking_coal": 126, "limestone": 84, "other_bulk": 96}


def compare_suppliers() -> list[dict]:
    rows = []
    for s in SUPPLIERS:
        total = s["fob"] + s["freight"] + s["port"] + s["demurrage"]
        rows.append({**s, "total_landed_cost": round(total, 2)})
    return rows


def compute_landed_cost(commodity: str, freight_rate: float, port_charge: float, demurrage_risk: str) -> dict:
    commodity_cost = COMMODITY_BASE_COST.get(commodity, 100)
    demurrage_cost = DEMURRAGE_RISK_COST.get(demurrage_risk, 1.2)
    total = commodity_cost + freight_rate + port_charge + demurrage_cost
    return {
        "commodity_cost": commodity_cost,
        "freight": round(freight_rate, 2),
        "port_charges": round(port_charge, 2),
        "expected_demurrage": demurrage_cost,
        "total_landed_cost": round(total, 2),
    }

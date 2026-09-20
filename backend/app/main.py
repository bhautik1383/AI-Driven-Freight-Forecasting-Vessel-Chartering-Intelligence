from __future__ import annotations

import asyncio
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="NaviCast API", version="2.0.0", description="Decision intelligence for overseas bulk-cargo chartering.")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","), allow_methods=["*"], allow_headers=["*"])

PORTS = [
    {"id": "paradip", "name": "Paradip", "draft_limit_m": 16.0, "lat": 20.2648, "lng": 86.6947, "congestion": "Moderate", "utilization": 76},
    {"id": "dhamra", "name": "Dhamra", "draft_limit_m": 17.5, "lat": 20.79, "lng": 86.99, "congestion": "Low", "utilization": 62},
    {"id": "gangavaram", "name": "Gangavaram", "draft_limit_m": 21.0, "lat": 17.625, "lng": 83.241, "congestion": "Low", "utilization": 58},
]
VESSELS = [
    {"id": "freightara-one", "name": "MV Freightara One", "vessel_type": "Capesize", "dwt": 178000, "draft_m": 15.2, "cargo": "Coking Coal", "origin": "Australia", "destination_port_id": "paradip", "eta": "18 Sep, 14:40", "speed_kn": 12.4, "heading": 301, "status": "On schedule", "delay_risk": "Low", "lat": 10.2, "lng": 82.1, "trail": [[-31,151],[0,105],[6,91],[10.2,82.1]]},
    {"id": "coral-horizon", "name": "MV Coral Horizon", "vessel_type": "Capesize", "dwt": 172500, "draft_m": 17.2, "cargo": "Coking Coal", "origin": "Australia", "destination_port_id": "dhamra", "eta": "19 Sep, 09:15", "speed_kn": 11.8, "heading": 298, "status": "Tide review", "delay_risk": "Medium", "lat": 13.7, "lng": 87.4, "trail": [[-32,150],[-5,112],[7,96],[13.7,87.4]]},
    {"id": "eastern-voyager", "name": "MV Eastern Voyager", "vessel_type": "Panamax", "dwt": 76500, "draft_m": 14.8, "cargo": "Coking Coal", "origin": "Indonesia", "destination_port_id": "paradip", "eta": "17 Sep, 22:05", "speed_kn": 12.7, "heading": 275, "status": "On schedule", "delay_risk": "Low", "lat": 8.6, "lng": 94.7, "trail": [[-4,118],[2,105],[6,99],[8.6,94.7]]},
    {"id": "steel-vanguard", "name": "MV Steel Vanguard", "vessel_type": "Capesize", "dwt": 181200, "draft_m": 18.9, "cargo": "Limestone", "origin": "South Africa", "destination_port_id": "gangavaram", "eta": "21 Sep, 07:30", "speed_kn": 10.9, "heading": 37, "status": "Weather watch", "delay_risk": "High", "lat": -8.5, "lng": 62.5, "trail": [[-34,18],[-20,42],[-12,56],[-8.5,62.5]]},
]
SUPPLIERS = [
    {"supplier":"Blackwater Resources","origin":"Australia","fob":132.0,"freight":18.7,"port":3.4,"demurrage":0.9,"transit":18,"risk":"Low","score":92},
    {"supplier":"East Kalimantan Coal","origin":"Indonesia","fob":119.0,"freight":11.8,"port":3.6,"demurrage":1.2,"transit":9,"risk":"Medium","score":88},
    {"supplier":"Richards Bay Minerals","origin":"South Africa","fob":125.0,"freight":16.6,"port":3.9,"demurrage":1.9,"transit":16,"risk":"Medium","score":81},
    {"supplier":"Gulf Carbon Partners","origin":"US Gulf","fob":141.0,"freight":24.7,"port":4.3,"demurrage":1.6,"transit":29,"risk":"High","score":64},
]

class ForecastRequest(BaseModel):
    commodity: str = "Coking Coal"
    route: str = "Australia → East Coast India"
    vessel_type: str = "Capesize"
    horizon_days: int = Field(default=14, ge=7, le=90)
    model: str = "XGBoost"

class ConstraintRequest(BaseModel):
    vessel_draft_m: float = Field(ge=1, le=30)

class RecommendationRequest(BaseModel):
    commodity: str = "Coking Coal"
    quantity_mt: int = Field(default=150000, ge=1000)
    origin: str = "Australia"
    port_id: str = "gangavaram"
    vessel_draft_m: float = Field(default=18.2, ge=1, le=30)
    laycan_start: str = "2026-09-18"
    urgency: Literal["Standard", "Expedited", "Critical"] = "Standard"

class AssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

def port_check(port: dict, draft: float) -> dict:
    clearance = round(port["draft_limit_m"] - draft, 1)
    if clearance < 0:
        status, label = "not_compatible", "Not compatible"
        detail = f"Exceeds the {port['draft_limit_m']} m operational draft limit by {abs(clearance):.1f} m."
    elif clearance < 0.6:
        status, label = "conditional", "Conditional"
        detail = f"{clearance:.1f} m clearance. Confirm tide window and berth conditions before fixing."
    else:
        status, label = "compatible", "Compatible"
        detail = f"{clearance:.1f} m clearance against the {port['draft_limit_m']} m operational limit."
    return {**port, "vessel_draft_m":draft, "clearance_m":clearance, "status":status, "label":label, "detail":detail}

def forecast_payload(req: ForecastRequest) -> dict:
    route_base = {"Australia → East Coast India": 19.2, "Indonesia → East Coast India": 11.8, "South Africa → East Coast India":16.6, "US Gulf → East Coast India":24.7}.get(req.route, 19.2)
    vessel_factor = {"Capesize":1, "Panamax":1.12, "Supramax":1.22}.get(req.vessel_type,1)
    base = route_base * vessel_factor
    historical = [round(base * (1.08 + 0.036*math.sin(i*.38) - i*.0019),2) for i in range(30)]
    current = historical[-1]
    decline = 0.084 if req.horizon_days <= 30 else 0.062
    forecast = [round(current*(1 - decline*(i+1)/req.horizon_days) + .12*math.sin(i*.72),2) for i in range(req.horizon_days)]
    bands = [round(.32 + i*.032,2) for i in range(req.horizon_days)]
    return {"labels_hist":[(datetime.now(timezone.utc)-timedelta(days=30-i)).strftime("%d %b") for i in range(30)], "historical":historical, "forecast":forecast, "forecast_upper":[round(v+b,2) for v,b in zip(forecast,bands)], "forecast_lower":[round(v-b,2) for v,b in zip(forecast,bands)], "current_rate":current, "expected_rate":forecast[-1], "pct_change":round((forecast[-1]-current)/current*100,1), "confidence":86, "model_used":req.model, "indicators":{"commodity_index":-2.1,"fx_usd_inr":0.3,"vessel_availability":14,"volatility":"Moderate"}, "data_source":"demo"}

@app.get("/")
@app.get("/health")
def health():
    return {"status":"operational", "mode":"demo", "timestamp":datetime.now(timezone.utc).isoformat(), "connectors":{"AIS":"Demo data active","Baltic Freight":"Demo data active","Port Data":"Demo data active","DGCIS":"Unavailable — Demo data active","Commodity":"Demo data active","FX":"Demo data active"}, "model":"ready"}

@app.get("/vessels")
def vessels():
    return {"vessels":VESSELS, "data_source":"demo", "updated_at":datetime.now(timezone.utc).isoformat()}

@app.get("/ports")
def ports():
    return {"ports":PORTS, "data_source":"demo"}

@app.post("/freight/forecast")
def freight_forecast(req: ForecastRequest):
    return forecast_payload(req)

@app.post("/ports/check")
def ports_check(req: ConstraintRequest):
    return {"results":[port_check(p, req.vessel_draft_m) for p in PORTS], "data_source":"demo"}

@app.get("/procurement")
def procurement():
    rows=[]
    for row in SUPPLIERS:
        total=round(row["fob"]+row["freight"]+row["port"]+row["demurrage"],2)
        rows.append({**row,"landed_cost":total})
    rows.sort(key=lambda x:x["landed_cost"])
    return {"rows":rows, "best_supplier":rows[0]["supplier"], "data_source":"demo"}

@app.post("/charter/recommendation")
def recommendation(req: RecommendationRequest):
    selected = next((p for p in PORTS if p["id"] == req.port_id), PORTS[2])
    checks=[port_check(p,req.vessel_draft_m) for p in PORTS]
    check=port_check(selected,req.vessel_draft_m)
    f=forecast_payload(ForecastRequest(commodity=req.commodity, route="Australia → East Coast India", vessel_type="Capesize", horizon_days=14))
    risk = "Low" if check["status"]=="compatible" and selected["congestion"]=="Low" else "Medium" if check["status"]=="conditional" else "High"
    port_charges=3.4 if selected["congestion"]=="Low" else 4.2
    demurrage={"Low":0.9,"Medium":1.8,"High":3.4}[risk]
    fob=132
    total=round(fob+f["expected_rate"]+port_charges+demurrage,2)
    options=[
      {"rank":1,"label":"Recommended","vessel":"MV Freightara One","port":"Gangavaram","eta":"18 Sep, 14:40","freight":f["expected_rate"],"landed_cost":total,"risk":"Low","confidence":91,"savings":round((20.2-f["expected_rate"])*req.quantity_mt,0),"reason":"Deep-water compatibility, low congestion and forecasted freight softening."},
      {"rank":2,"label":"Alternative","vessel":"MV Eastern Voyager","port":"Dhamra","eta":"19 Sep, 09:15","freight":round(f["expected_rate"]+0.8,2),"landed_cost":round(total+1.35,2),"risk":"Medium","confidence":82,"savings":round((20.2-(f["expected_rate"]+.8))*req.quantity_mt,0),"reason":"Lower transit time, subject to tide-window confirmation."},
      {"rank":3,"label":"High-risk option","vessel":"MV Steel Vanguard","port":"Paradip","eta":"21 Sep, 07:30","freight":round(f["expected_rate"]-0.3,2),"landed_cost":round(total+2.8,2),"risk":"High","confidence":42,"savings":0,"reason":"Draft exceeds Paradip's operating limit and congestion exposure is higher."}
    ]
    explanation=[{"factor":"Freight trend","value":32,"direction":"positive"},{"factor":"Port compatibility","value":25,"direction":"positive"},{"factor":"Congestion","value":17,"direction":"positive"},{"factor":"Vessel availability","value":14,"direction":"positive"},{"factor":"FX exposure","value":-7,"direction":"negative"},{"factor":"Seasonality","value":5,"direction":"positive"}]
    return {"recommendation":options[0],"alternatives":options[1:],"constraint_checks":checks,"forecast":f,"landed_cost":{"fob":fob,"freight":f["expected_rate"],"port_charges":port_charges,"demurrage":demurrage,"total":total},"explanation":explanation,"narrative":f"Freight is forecast to soften {abs(f['pct_change'])}% over 14 days. Gangavaram provides {port_check(PORTS[2], req.vessel_draft_m)['clearance_m']} m clearance with low congestion, supporting the recommended charter window.","approval_required":True,"data_source":"demo"}

@app.get("/explain")
def explain():
    return {"factors":[{"factor":"Freight trend","value":32,"direction":"positive"},{"factor":"Port compatibility","value":25,"direction":"positive"},{"factor":"Congestion","value":17,"direction":"positive"},{"factor":"Vessel availability","value":14,"direction":"positive"},{"factor":"FX exposure","value":-7,"direction":"negative"},{"factor":"Seasonality","value":5,"direction":"positive"}], "data_source":"demo"}

@app.get("/dashboard")
def dashboard():
    return {"active_vessels":4,"forecast_direction":"Softening","average_landed_cost":157.2,"potential_savings":226500,"high_risk_vessels":1,"port_utilization":[{"name":p["name"],"value":p["utilization"]} for p in PORTS],"upcoming_windows":3,"data_source":"demo"}

@app.post("/assistant/ask")
def ask_assistant(req: AssistantRequest):
    q=req.question.lower()
    if "port" in q or "draft" in q or "paradip" in q:
        answer="For an 18.2 m draft, Gangavaram is compatible with 2.8 m clearance. Paradip and Dhamra cannot accept that draft under their 16.0 m and 17.5 m operational limits. Confirm final berth and tide conditions before approval."
    elif "wait" in q or "now" in q or "charter" in q:
        f=forecast_payload(ForecastRequest())
        answer=f"The demo forecast projects a {abs(f['pct_change'])}% decline over 14 days, which supports the 18–22 Sep charter window. Waiting carries availability risk; keep the recommended vessel on hold while the planner confirms laycan."
    elif "supplier" in q or "landed" in q:
        best=min(SUPPLIERS,key=lambda x:sum(x[k] for k in ["fob","freight","port","demurrage"]))
        total=sum(best[k] for k in ["fob","freight","port","demurrage"])
        answer=f"{best['supplier']} has the lowest demo total landed cost at ${total:.1f}/t after FOB, freight, port charges and expected demurrage. This is a decision-support result and needs human validation."
    else:
        answer="NaviCast evaluates freight outlook, vessel availability, port draft compatibility and total landed cost. Ask about a charter window, port draft, vessel or supplier comparison."
    return {"answer":answer,"mode":"deterministic demo","data_source":"demo"}

@app.websocket("/ws/live")
async def live(websocket: WebSocket):
    await websocket.accept()
    tick=0
    try:
        while True:
            tick+=1
            await websocket.send_json({"type":"telemetry","timestamp":datetime.now(timezone.utc).isoformat(),"data_source":"demo","freight_index":round(101.8-.05*tick+math.sin(tick)*.16,2),"ais_signal":"healthy","vessels":[{"id":"freightara-one","lat":round(10.2+.01*tick,3),"lng":round(82.1+.012*tick,3),"speed_kn":round(12.4+.2*math.sin(tick),1)}],"congestion":{"paradip":76+tick%3,"dhamra":62,"gangavaram":58+tick%2}})
            await asyncio.sleep(4)
    except WebSocketDisconnect:
        return

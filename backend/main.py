"""
FastAPI backend — exposes the multi-agent dispute resolution system via REST.

Endpoints:
  POST /api/dispute          — file a dispute, triggers the full agent workflow
  GET  /api/trips/rider       — list rider trips from the SQLite DB
  GET  /api/trips/driver      — list driver trips
  GET  /api/trips/{trip_id}   — get a specific trip
  GET  /api/policy            — list all dispute policy rules
  GET  /api/agents            — list registered agents on the MCP bus
  GET  /api/health            — health check

The dispute endpoint instantiates a fresh MCP bus + 4 agents (case controller,
rider advocate, driver advocate, judge), runs the full workflow synchronously,
and returns the ruling + full message transcript.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mcp_bus import MCPBus
from case_controller import CaseController
from rider_advocate import RiderAdvocateAgent
from driver_advocate import DriverAdvocateAgent
from judge_agent import JudgeAgent
import data_layer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ryde Dispute Resolution — Multi-Agent Backend",
    description="Three agents (Rider Advocate, Driver Advocate, Judge) communicate via MCP to resolve ride-hailing disputes.",
    version="1.0.0",
)


# --------------------------------------------------------------------------- #
# Request / response models
# --------------------------------------------------------------------------- #

class DisputeRequest(BaseModel):
    trip_id: str = Field(..., description="Trip ID, e.g. '20261011-180500-000001'")
    filed_by: str = Field("rider", description="Who filed the dispute: 'rider' or 'driver'")
    issue_category: str = Field(..., description="Issue category, e.g. 'Fare / pricing dispute'")
    complaint_text: str = Field("", description="Free-text complaint from the filing party")


class TripResponse(BaseModel):
    trip_id: str
    rider_name: str
    driver_name: str
    datetime_sgt: str
    pickup: str
    destination: str
    status: str
    amount_sgd: float
    chat_history: str


# --------------------------------------------------------------------------- #
# Agent factory — creates a fresh MCP bus + agents for each dispute
# --------------------------------------------------------------------------- #

def create_agent_system() -> tuple[MCPBus, CaseController]:
    """Create a fresh MCP bus with all four agents registered."""
    bus = MCPBus()
    judge = JudgeAgent(bus)
    rider_advocate = RiderAdvocateAgent(bus)
    driver_advocate = DriverAdvocateAgent(bus)
    controller = CaseController(bus)
    return bus, controller


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "ryde-dispute-resolution"}


@app.get("/api/agents")
def list_agents() -> Dict[str, Any]:
    """List the agents that would be registered for a dispute."""
    return {
        "agents": [
            {"name": "case_controller", "role": "Orchestrates the workflow, opens/assigns cases, publishes outcomes"},
            {"name": "rider_advocate", "role": "Gathers evidence, builds the rider's case, cites policy, submits to Judge"},
            {"name": "driver_advocate", "role": "Gathers evidence, builds the driver's case, cites policy, submits to Judge"},
            {"name": "judge_agent", "role": "Reviews both cases, weighs evidence, applies policy, issues ruling + confidence"},
        ],
        "communication": "MCP (Model Context Protocol) message bus — agents exchange typed messages",
    }


@app.get("/api/trips/rider")
def get_rider_trips() -> List[Dict[str, Any]]:
    trips = data_layer.get_all_trips_for_rider("Rider123")
    return [dict(t) for t in trips]


@app.get("/api/trips/driver")
def get_driver_trips_endpoint() -> List[Dict[str, Any]]:
    # Get all driver trips — we need all drivers
    import sqlite3, os
    db_path = os.environ.get("RYDE_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "database", "ryde_trips.db"))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM driver_trips ORDER BY datetime_sgt").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/trips/{trip_id}")
def get_trip(trip_id: str) -> Dict[str, Any]:
    trip = data_layer.get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    return trip


@app.get("/api/policy")
def get_policy() -> List[Dict[str, Any]]:
    rules = data_layer.get_all_policy_rules()
    return data_layer.format_policy_for_case(rules)


@app.post("/api/dispute")
def file_dispute(req: DisputeRequest) -> Dict[str, Any]:
    """
    File a dispute and run the full multi-agent workflow.

    This triggers:
      1. Case controller opens the case
      2. Both advocates (rider + driver) are assigned
      3. Each advocate gathers evidence, cites policy, builds a case report
      4. Judge Agent receives both cases, weighs evidence, applies policy
      5. Judge issues a ruling with confidence and reasoning
      6. Case controller publishes the outcome

    All communication happens via the MCP message bus. The full message
    transcript is returned in the response.
    """
    # Verify the trip exists
    trip = data_layer.get_trip_by_id(req.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip {req.trip_id} not found")

    # Create a fresh agent system for this dispute
    bus, controller = create_agent_system()

    # Run the dispute workflow
    result = controller.file_dispute(
        trip_id=req.trip_id,
        filed_by=req.filed_by,
        issue_category=req.issue_category,
        complaint_text=req.complaint_text,
    )

    ruling = result.get("ruling") or {}
    transcript = result.get("transcript") or []

    return {
        "case_id": result["case_id"],
        "status": result["status"],
        "trip_id": req.trip_id,
        "filed_by": req.filed_by,
        "issue_category": req.issue_category,
        "ruling": {
            "action": ruling.get("ruling"),
            "description": ruling.get("ruling_description"),
            "in_favor_of": ruling.get("in_favor_of"),
            "adjustment_sgd": ruling.get("adjustment_sgd"),
            "confidence": ruling.get("confidence"),
            "needs_human_review": ruling.get("needs_human_review"),
            "escalation_reason": ruling.get("escalation_reason"),
            "reasoning": ruling.get("reasoning"),
            "evidence_analysis": ruling.get("evidence_analysis"),
            "policy_analysis": ruling.get("policy_analysis"),
            "rider_case_confidence": ruling.get("rider_case_confidence"),
            "driver_case_confidence": ruling.get("driver_case_confidence"),
            "policy_rules_applied": ruling.get("policy_rules_applied"),
        },
        "mcp_transcript": transcript,
        "agents": bus.registered_agents,
    }


@app.post("/api/dispute/quick")
def quick_dispute(
    trip_id: str = "20261011-180500-000001",
    filed_by: str = "rider",
    issue_category: str = "Fare / pricing dispute",
    complaint_text: str = "I was charged S$31.40 but the quote was S$27.00.",
) -> Dict[str, Any]:
    """Convenience endpoint with query params for quick testing."""
    req = DisputeRequest(
        trip_id=trip_id,
        filed_by=filed_by,
        issue_category=issue_category,
        complaint_text=complaint_text,
    )
    return file_dispute(req)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

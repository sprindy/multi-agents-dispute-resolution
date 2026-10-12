"""
Case Controller (Orchestrator)

This is the "proposed" layer from the architecture diagram. It:
  1. Opens a case from the first dispute report
  2. Notifies the other party
  3. Assigns the case to both advocates (rider + driver)
  4. Collects the ruling from the Judge
  5. Publishes the outcome

Even though the architecture says the case controller is "proposed", we
implement it here because it's the glue that wires the three agents together.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mcp_bus import MCPBus, MCPMessage, MessageType
from base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CaseController(BaseAgent):
    name = "case_controller"
    description = (
        "Orchestrates the dispute resolution workflow: opens cases, "
        "notifies parties, assigns advocates, collects the ruling, "
        "and publishes the outcome."
    )

    def __init__(self, bus: MCPBus) -> None:
        super().__init__(bus)
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._completed: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Public API — called by the FastAPI endpoint to start a dispute
    # ------------------------------------------------------------------ #

    def file_dispute(
        self,
        trip_id: str,
        filed_by: str,
        issue_category: str,
        complaint_text: str = "",
    ) -> Dict[str, Any]:
        """
        Entry point: a rider or driver files a dispute.
        Returns a case_id immediately; the workflow runs synchronously
        because the MCP bus is in-process.
        """
        case_id = str(uuid.uuid4())[:8]
        case = {
            "case_id": case_id,
            "trip_id": trip_id,
            "filed_by": filed_by,
            "issue_category": issue_category,
            "complaint_text": complaint_text,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "opened",
            "ruling": None,
            "messages": [],
        }
        self._cases[case_id] = case

        self.log_reasoning("case_opened", f"Case {case_id} opened: trip={trip_id}, filed_by={filed_by}, issue='{issue_category}'")

        # Broadcast case opened (notifies all agents)
        self.bus.broadcast(
            self.name,
            MessageType.CASE_OPENED,
            {"case_id": case_id, "trip_id": trip_id, "filed_by": filed_by, "issue_category": issue_category},
        )

        # Notify the other party
        other_party = "driver" if filed_by == "rider" else "rider"
        self.log_reasoning("party_notified", f"Case {case_id}: notifying {other_party} side")
        self.bus.broadcast(
            self.name,
            MessageType.PARTY_NOTIFIED,
            {"case_id": case_id, "notified_party": other_party, "reason": "Dispute filed against you"},
        )

        # Assign case to both advocates
        case_payload = {
            "case_id": case_id,
            "trip_id": trip_id,
            "issue_category": issue_category,
            "filed_by": filed_by,
            "complaint_text": complaint_text,
        }

        self.bus.send(
            self.name,
            "rider_advocate",
            MessageType.CASE_ASSIGNED,
            case_payload,
        )
        self.bus.send(
            self.name,
            "driver_advocate",
            MessageType.CASE_ASSIGNED,
            case_payload,
        )

        # The advocates will build their cases and submit to the Judge.
        # The Judge will issue a ruling back to us via RULING_ISSUED.
        # Since everything is synchronous (in-process bus), the ruling
        # should already be stored in self._cases[case_id]["ruling"].

        ruling = self._cases[case_id].get("ruling")
        case["status"] = "closed" if ruling else "pending"

        result = {
            "case_id": case_id,
            "status": case["status"],
            "ruling": ruling,
            "transcript": self.bus.get_transcript(),
        }

        self._completed.append(result)
        del self._cases[case_id]

        return result

    # ------------------------------------------------------------------ #
    # Receive the Judge's ruling
    # ------------------------------------------------------------------ #

    def on_ruling_issued(self, msg: MCPMessage) -> None:
        ruling = msg.payload
        case_id = ruling.get("case_id")
        if case_id in self._cases:
            self._cases[case_id]["ruling"] = ruling
            self._cases[case_id]["status"] = "closed"
            self.log_reasoning(
                "ruling_received",
                f"Case {case_id}: ruling={ruling.get('ruling')}, in_favor_of={ruling.get('in_favor_of')}, "
                f"confidence={ruling.get('confidence')}",
            )

            # Broadcast case closed
            self.bus.broadcast(
                self.name,
                MessageType.CASE_CLOSED,
                {"case_id": case_id, "ruling": ruling.get("ruling"), "in_favor_of": ruling.get("in_favor_of")},
            )

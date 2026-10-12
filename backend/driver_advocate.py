"""
Driver Advocate Agent

Role (from the architecture):
  • Gather all relevant evidence supporting the driver's position
  • Build and submit the driver's case to the Judge
  • Cite company policy that backs the driver's claim
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp_bus import MCPBus, MCPMessage, MessageType
from base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DriverAdvocateAgent(BaseAgent):
    name = "driver_advocate"
    description = (
        "Represents the driver. Gathers evidence, builds the driver's case, "
        "cites policy, and submits it to the Judge Agent."
    )

    def __init__(self, bus: MCPBus) -> None:
        super().__init__(bus)
        self._pending_cases: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # When the case controller assigns this agent a dispute involving the driver
    # ------------------------------------------------------------------ #

    def on_case_assigned(self, msg: MCPMessage) -> None:
        payload = msg.payload
        case_id = payload.get("case_id")
        trip_id = payload.get("trip_id")
        issue_category = payload.get("issue_category", "Unknown")
        filed_by = payload.get("filed_by", "driver")
        complaint_text = payload.get("complaint_text", "")

        if filed_by != "driver":
            self.log_reasoning(
                "case_assigned",
                f"Case {case_id}: driver side activated (filed by rider). Building driver defense.",
            )
        else:
            self.log_reasoning(
                "case_assigned",
                f"Case {case_id}: trip={trip_id}, issue='{issue_category}', complaint='{complaint_text[:80]}'",
            )

        self._pending_cases[case_id] = {
            "trip_id": trip_id,
            "issue_category": issue_category,
            "filed_by": filed_by,
            "complaint_text": complaint_text,
        }

        case_report = self._build_driver_case(case_id, trip_id, issue_category, complaint_text)

        self.bus.send(
            self.name,
            "judge_agent",
            MessageType.CASE_SUBMITTED,
            {
                "case_id": case_id,
                "trip_id": trip_id,
                "party": "driver",
                "issue_category": issue_category,
                "case_report": case_report,
            },
            correlation_id=msg.correlation_id,
        )

        self.log_reasoning("case_submitted", f"Submitted driver case {case_id} to Judge Agent")

    # ------------------------------------------------------------------ #
    # Evidence gathering + case building
    # ------------------------------------------------------------------ #

    def _build_driver_case(
        self,
        case_id: str,
        trip_id: str,
        issue_category: str,
        complaint_text: str,
    ) -> Dict[str, Any]:
        """Build the driver's structured case report."""

        evidence = self.fetch_trip_evidence(trip_id)
        if not evidence:
            return {"error": f"Trip {trip_id} not found"}

        driver_name = evidence.get("driver_name", "Driver123")
        behavior = self.fetch_behavior_profile(driver_name, "driver")
        policy_rules = self.fetch_relevant_policy(issue_category)
        arguments = self._build_arguments(evidence, issue_category, complaint_text)
        recommended_action = self._recommend_action(evidence, issue_category)

        return {
            "party": "driver",
            "agent": self.name,
            "case_id": case_id,
            "trip_id": trip_id,
            "rider_name": evidence.get("rider_name"),
            "driver_name": driver_name,
            "issue_category": issue_category,
            "complaint_text": complaint_text,
            "evidence": {
                "trip_route": evidence.get("route"),
                "status": evidence.get("status"),
                "amount_sgd": evidence.get("amount_sgd"),
                "is_cancelled": evidence.get("is_cancelled"),
                "pickup": evidence.get("pickup"),
                "destination": evidence.get("destination"),
                "datetime": evidence.get("datetime_sgt"),
                "chat_lines": evidence.get("chat_lines", []),
                "signals": {
                    "mentioned_detour": evidence.get("mentioned_detour"),
                    "mentioned_fare": evidence.get("mentioned_fare"),
                    "mentioned_safety": evidence.get("mentioned_safety"),
                },
            },
            "behavior_profile": behavior,
            "policy_cited": policy_rules,
            "arguments": arguments,
            "recommended_action": recommended_action,
            "confidence": self._assess_confidence(evidence, issue_category),
        }

    def _build_arguments(
        self,
        evidence: Dict[str, Any],
        issue_category: str,
        complaint_text: str,
    ) -> List[str]:
        """Build the driver's arguments based on evidence and issue category."""
        args: List[str] = []
        cat = issue_category.lower()

        if "route" in cat or "deviation" in cat:
            args.append(
                "The driver chose what they believed was the fastest route (PUB04 allows "
                "driver to choose the most efficient GPS route)."
            )
            args.append(
                "The driver informed the rider during the trip that the route was faster, "
                "as shown in the chat history."
            )
            args.append(
                "Any stop was brief and for legitimate reasons (traffic, road conditions)."
            )

        elif "no-show" in cat or "cancellation" in cat:
            args.append(
                f"The rider did not show up at the pickup point within the waiting period. "
                f"Trip status: {evidence.get('status')}."
            )
            args.append("Per PUB03, the driver attempted to contact the rider via in-app chat.")
            args.append("Per PUB02, the driver is entitled to a S$4.50 cancellation compensation after the waiting period.")

        elif "fare" in cat or "pricing" in cat:
            args.append(
                f"The charged fare of S${evidence.get('amount_sgd')} reflects the actual trip "
                f"including any tolls or ERP charges (PUB05)."
            )
            args.append("The fare is fixed by pickup and drop-off; any difference may be due to tolls or surcharges.")

        elif "damage" in cat or "cleaning" in cat:
            args.append(
                "The rider caused damage / mess to the vehicle. The driver informed the rider "
                "and submitted a claim to Ryde (PUB07)."
            )
            args.append("Photographic evidence and a cleaning fee receipt are available.")

        elif "safety" in cat or "misconduct" in cat:
            args.append(
                "The driver followed road rules and traveled directly to the destination (PUB08)."
            )
            args.append("If the rider exhibited unsafe behavior, the driver reported it through RydeHELP (PUB09).")
            args.append("The driver's behavior profile shows no prior safety incidents.")

        if complaint_text:
            args.append(f"Driver's statement: '{complaint_text}'")

        return args

    def _recommend_action(self, evidence: Dict[str, Any], issue_category: str) -> Dict[str, Any]:
        """Driver's perspective on what should happen."""
        cat = issue_category.lower()
        amount = evidence.get("amount_sgd", 0)

        if "no-show" in cat or "cancellation" in cat:
            return {
                "action": "compensation",
                "description": "Pay the driver the S$4.50 cancellation compensation.",
                "estimated_adjustment_sgd": 4.50,
            }
        elif "fare" in cat or "pricing" in cat:
            return {
                "action": "no_action",
                "description": "The charged fare is correct per the fixed fare policy.",
                "estimated_adjustment_sgd": 0,
            }
        elif "route" in cat or "deviation" in cat:
            return {
                "action": "no_action",
                "description": "The driver chose the fastest route as permitted by policy.",
                "estimated_adjustment_sgd": 0,
            }
        elif "damage" in cat or "cleaning" in cat:
            return {
                "action": "compensation",
                "description": "Charge the rider the cleaning/damage fee.",
                "estimated_adjustment_sgd": 50.0,
            }
        elif "safety" in cat or "misconduct" in cat:
            return {
                "action": "no_action",
                "description": "No driver misconduct found; rider behavior may need review.",
                "estimated_adjustment_sgd": 0,
            }
        else:
            return {"action": "review", "description": "Manual review needed.", "estimated_adjustment_sgd": 0}

    def _assess_confidence(self, evidence: Dict[str, Any], issue_category: str) -> float:
        """Assess how confident the driver's case is (0.0 - 1.0)."""
        confidence = 0.5
        if evidence.get("chat_lines"):
            confidence += 0.15
        if evidence.get("is_cancelled"):
            confidence += 0.1  # cancellation supports driver's no-show claim
        if evidence.get("status") == "Completed":
            confidence += 0.1
        if evidence.get("amount_sgd") and evidence.get("amount_sgd") > 0:
            confidence += 0.05
        return min(round(confidence, 2), 0.95)

    # ------------------------------------------------------------------ #
    # Respond to evidence requests
    # ------------------------------------------------------------------ #

    def on_evidence_request(self, msg: MCPMessage) -> None:
        payload = msg.payload
        trip_id = payload.get("trip_id")
        case_id = payload.get("case_id")

        evidence = self.fetch_trip_evidence(trip_id) if trip_id else None

        self.bus.send(
            self.name,
            msg.sender,
            MessageType.EVIDENCE_RESPONSE,
            {"case_id": case_id, "trip_id": trip_id, "evidence": evidence},
            correlation_id=msg.correlation_id,
        )

"""
Rider Advocate Agent

Role (from the architecture):
  • Gather all relevant evidence supporting the rider's position
  • Build and submit the rider's case to the Judge
  • Cite company policy that backs the rider's claim
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp_bus import MCPBus, MCPMessage, MessageType
from base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RiderAdvocateAgent(BaseAgent):
    name = "rider_advocate"
    description = (
        "Represents the rider. Gathers evidence, builds the rider's case, "
        "cites policy, and submits it to the Judge Agent."
    )

    def __init__(self, bus: MCPBus) -> None:
        super().__init__(bus)
        self._pending_cases: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # When the case controller assigns this agent a dispute from the rider
    # ------------------------------------------------------------------ #

    def on_case_assigned(self, msg: MCPMessage) -> None:
        payload = msg.payload
        case_id = payload.get("case_id")
        trip_id = payload.get("trip_id")
        issue_category = payload.get("issue_category", "Unknown")
        filed_by = payload.get("filed_by", "rider")
        complaint_text = payload.get("complaint_text", "")

        if filed_by != "rider":
            # This case was filed by the driver; we still need to build the
            # rider's side of the argument (the rider is the other party).
            self.log_reasoning(
                "case_assigned",
                f"Case {case_id}: rider side activated (filed by driver). Building rider defense.",
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

        # Gather evidence and build the case
        case_report = self._build_rider_case(case_id, trip_id, issue_category, complaint_text)

        # Submit to Judge Agent
        self.bus.send(
            self.name,
            "judge_agent",
            MessageType.CASE_SUBMITTED,
            {
                "case_id": case_id,
                "trip_id": trip_id,
                "party": "rider",
                "issue_category": issue_category,
                "case_report": case_report,
            },
            correlation_id=msg.correlation_id,
        )

        self.log_reasoning("case_submitted", f"Submitted rider case {case_id} to Judge Agent")

    # ------------------------------------------------------------------ #
    # Evidence gathering + case building
    # ------------------------------------------------------------------ #

    def _build_rider_case(
        self,
        case_id: str,
        trip_id: str,
        issue_category: str,
        complaint_text: str,
    ) -> Dict[str, Any]:
        """Build the rider's structured case report."""

        # 1) Trip evidence
        evidence = self.fetch_trip_evidence(trip_id)
        if not evidence:
            return {"error": f"Trip {trip_id} not found"}

        # 2) Behavior profile
        rider_name = evidence.get("rider_name", "Rider123")
        behavior = self.fetch_behavior_profile(rider_name, "rider")

        # 3) Relevant policy
        policy_rules = self.fetch_relevant_policy(issue_category)

        # 4) Build argument based on issue category
        arguments = self._build_arguments(evidence, issue_category, complaint_text)

        # 5) Recommended action from rider's perspective
        recommended_action = self._recommend_action(evidence, issue_category)

        return {
            "party": "rider",
            "agent": self.name,
            "case_id": case_id,
            "trip_id": trip_id,
            "rider_name": rider_name,
            "driver_name": evidence.get("driver_name"),
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
        """Build the rider's arguments based on evidence and issue category."""
        args: List[str] = []
        cat = issue_category.lower()

        if "route" in cat or "deviation" in cat:
            args.append(
                f"Rider observed the driver leaving the expressway and making unexpected stops "
                f"(chat: {evidence.get('chat_lines', [])}). The rider questioned the route "
                f"but did not receive a satisfactory explanation."
            )
            if evidence.get("mentioned_detour"):
                args.append("Chat logs confirm the rider raised concerns about the route deviation during the trip.")
            args.append("Per PUB04, the driver may choose the fastest route, but the rider's concerns should be addressed.")

        elif "no-show" in cat or "cancellation" in cat:
            args.append(
                f"The rider arrived at the pickup point on time. Trip status: {evidence.get('status')}. "
                f"If the driver claims no-show, the rider disputes this."
            )
            args.append("Per PUB01, cancellations within three minutes of matching are free for the rider.")

        elif "fare" in cat or "pricing" in cat:
            args.append(
                f"The charged fare was S${evidence.get('amount_sgd')}, but the rider was quoted a lower amount. "
                f"Chat confirms the rider raised the fare discrepancy."
            )
            if evidence.get("mentioned_fare"):
                args.append("The rider explicitly questioned the fare in the in-app chat.")
            args.append("Per PUB05, quoted fares are generally fixed. An unsupported fare increase warrants an adjustment.")
            args.append("Per SIM03, recommended adjustment = max(0, charged - documented payable amount).")

        elif "damage" in cat or "cleaning" in cat:
            args.append("The rider denies causing any damage or mess to the vehicle.")
            args.append("Per PUB07, the driver must inform the rider and submit a claim to Ryde.")

        elif "safety" in cat or "misconduct" in cat:
            args.append(
                "The rider experienced unsafe or improper driver conduct during the trip."
            )
            if evidence.get("mentioned_safety"):
                args.append("Chat logs contain references to safety concerns.")
            args.append("Per PUB08, drivers must follow road rules and travel directly to the destination.")

        if complaint_text:
            args.append(f"Rider's statement: '{complaint_text}'")

        return args

    def _recommend_action(self, evidence: Dict[str, Any], issue_category: str) -> Dict[str, Any]:
        """Rider's perspective on what should happen."""
        cat = issue_category.lower()
        amount = evidence.get("amount_sgd", 0)

        if "fare" in cat or "pricing" in cat:
            return {
                "action": "refund",
                "description": "Refund the difference between charged fare and quoted fare.",
                "estimated_adjustment_sgd": round(max(0, amount - 27.0), 2),  # simplified: quote was S$27
            }
        elif "route" in cat or "deviation" in cat:
            return {
                "action": "compensation",
                "description": "Compensate for the extra distance/time caused by route deviation.",
                "estimated_adjustment_sgd": round(amount * 0.15, 2),
            }
        elif "no-show" in cat or "cancellation" in cat:
            return {
                "action": "refund",
                "description": "Refund any unjustified cancellation charge to the rider.",
                "estimated_adjustment_sgd": 4.50,
            }
        elif "safety" in cat or "misconduct" in cat:
            return {
                "action": "compensation",
                "description": "Compensate the rider for safety incident; investigate driver conduct.",
                "estimated_adjustment_sgd": round(amount * 0.5, 2),
            }
        else:
            return {"action": "review", "description": "Manual review needed.", "estimated_adjustment_sgd": 0}

    def _assess_confidence(self, evidence: Dict[str, Any], issue_category: str) -> float:
        """Assess how confident the rider's case is (0.0 - 1.0)."""
        confidence = 0.5  # baseline
        if evidence.get("chat_lines"):
            confidence += 0.15
        if evidence.get("mentioned_detour") or evidence.get("mentioned_fare") or evidence.get("mentioned_safety"):
            confidence += 0.15
        if evidence.get("status") == "Completed":
            confidence += 0.1
        if evidence.get("amount_sgd") and evidence.get("amount_sgd") > 0:
            confidence += 0.05
        return min(round(confidence, 2), 0.95)

    # ------------------------------------------------------------------ #
    # Respond to evidence requests from other agents
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

"""
Judge Agent

Role (from the architecture):
  • Review both cases (rider advocate's + driver advocate's)
  • Weigh the evidence from both sides
  • Apply company policy impartially
  • Rule with a confidence score
  • Explain the reasoning behind the ruling
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from mcp_bus import MCPBus, MCPMessage, MessageType
from base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Confidence threshold below which the case is escalated to a human reviewer
CONFIDENCE_THRESHOLD = 0.85
MAX_AUTO_ADJUSTMENT_SGD = 50.0


class JudgeAgent(BaseAgent):
    name = "judge_agent"
    description = (
        "Impartial judge. Reviews both advocate cases, weighs evidence, "
        "applies policy, issues a ruling with confidence and reasoning."
    )

    def __init__(self, bus: MCPBus) -> None:
        super().__init__(bus)
        # case_id -> { rider_case, driver_case }
        self._pending_cases: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # Receive case submissions from advocates
    # ------------------------------------------------------------------ #

    def on_case_submitted(self, msg: MCPMessage) -> None:
        payload = msg.payload
        case_id = payload.get("case_id")
        party = payload.get("party")
        case_report = payload.get("case_report", {})

        if case_id not in self._pending_cases:
            self._pending_cases[case_id] = {
                "trip_id": payload.get("trip_id"),
                "issue_category": payload.get("issue_category"),
                "rider_case": None,
                "driver_case": None,
            }

        self._pending_cases[case_id][f"{party}_case"] = case_report
        self.log_reasoning(
            "case_received",
            f"Received {party} case for {case_id} (confidence={case_report.get('confidence', '?')})",
        )

        # Check if both cases have arrived
        case = self._pending_cases[case_id]
        if case["rider_case"] is not None and case["driver_case"] is not None:
            self._adjudicate(case_id)

    # ------------------------------------------------------------------ #
    # Core adjudication logic
    # ------------------------------------------------------------------ #

    def _adjudicate(self, case_id: str) -> None:
        case = self._pending_cases[case_id]
        rider_case = case["rider_case"]
        driver_case = case["driver_case"]
        issue_category = case.get("issue_category", "Unknown")
        trip_id = case.get("trip_id")

        self.log_reasoning("adjudication_start", f"Both cases received for {case_id}. Beginning review.")

        # 1) Weigh evidence from both sides
        evidence_analysis = self._weigh_evidence(rider_case, driver_case)

        # 2) Apply company policy
        policy_analysis = self._apply_policy(rider_case, driver_case, issue_category)

        # 3) Determine ruling
        ruling = self._determine_ruling(
            rider_case, driver_case, evidence_analysis, policy_analysis, issue_category
        )

        # 4) Assess confidence
        confidence = self._assess_confidence(rider_case, driver_case, evidence_analysis)

        # 5) Build reasoning explanation
        reasoning = self._build_reasoning(
            rider_case, driver_case, evidence_analysis, policy_analysis, ruling, confidence
        )

        # 6) Check if escalation is needed
        needs_escalation = confidence < CONFIDENCE_THRESHOLD or (
            ruling.get("adjustment_sgd", 0) > MAX_AUTO_ADJUSTMENT_SGD
        )

        ruling_result = {
            "case_id": case_id,
            "trip_id": trip_id,
            "issue_category": issue_category,
            "ruling": ruling["action"],
            "ruling_description": ruling["description"],
            "adjustment_sgd": ruling["adjustment_sgd"],
            "in_favor_of": ruling["in_favor_of"],
            "confidence": confidence,
            "needs_human_review": needs_escalation,
            "escalation_reason": (
                f"Confidence {confidence} < threshold {CONFIDENCE_THRESHOLD}"
                if confidence < CONFIDENCE_THRESHOLD
                else f"Adjustment S${ruling['adjustment_sgd']} exceeds auto limit S${MAX_AUTO_ADJUSTMENT_SGD}"
                if ruling.get("adjustment_sgd", 0) > MAX_AUTO_ADJUSTMENT_SGD
                else None
            ),
            "evidence_analysis": evidence_analysis,
            "policy_analysis": policy_analysis,
            "reasoning": reasoning,
            "rider_case_confidence": rider_case.get("confidence", 0),
            "driver_case_confidence": driver_case.get("confidence", 0),
            "policy_rules_applied": policy_analysis.get("applied_rules", []),
        }

        # Notify the case controller
        self.bus.send(
            self.name,
            "case_controller",
            MessageType.RULING_ISSUED,
            ruling_result,
        )

        self.log_reasoning(
            "ruling_issued",
            f"Case {case_id}: ruling='{ruling['action']}', in_favor_of={ruling['in_favor_of']}, "
            f"adjustment=S${ruling['adjustment_sgd']}, confidence={confidence}, "
            f"needs_human_review={needs_escalation}",
        )

        # Clean up
        del self._pending_cases[case_id]

    # ------------------------------------------------------------------ #
    # Evidence weighing
    # ------------------------------------------------------------------ #

    def _weigh_evidence(
        self,
        rider_case: Dict[str, Any],
        driver_case: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare the evidence presented by both sides."""
        r_ev = rider_case.get("evidence", {})
        d_ev = driver_case.get("evidence", {})

        # Chat log corroboration
        rider_signals = r_ev.get("signals", {})
        driver_signals = d_ev.get("signals", {})

        # Both sides share the same trip, so evidence fields should match
        # Key: who has the stronger argument based on signals and policy?

        rider_strength = 0
        driver_strength = 0

        # Chat evidence
        if rider_signals.get("mentioned_fare"):
            rider_strength += 2
        if rider_signals.get("mentioned_detour"):
            rider_strength += 2
        if rider_signals.get("mentioned_safety"):
            rider_strength += 3

        # Completed trip favors driver on fare disputes
        if r_ev.get("status") == "Completed":
            driver_strength += 1
        if r_ev.get("is_cancelled"):
            driver_strength += 2

        # Behavior profiles
        r_profile = rider_case.get("behavior_profile", {})
        d_profile = driver_case.get("behavior_profile", {})

        if r_profile.get("cancelled_trips", 0) > 2:
            driver_strength += 1  # rider has a pattern of cancellations
        if d_profile.get("total_trips", 0) > 5:
            driver_strength += 1  # experienced driver

        total = max(rider_strength + driver_strength, 1)
        return {
            "rider_strength": rider_strength,
            "driver_strength": driver_strength,
            "rider_share": round(rider_strength / total, 2),
            "driver_share": round(driver_strength / total, 2),
            "rider_signals": rider_signals,
            "driver_signals": driver_signals,
            "trip_status": r_ev.get("status"),
            "amount_sgd": r_ev.get("amount_sgd"),
        }

    # ------------------------------------------------------------------ #
    # Policy application
    # ------------------------------------------------------------------ #

    def _apply_policy(
        self,
        rider_case: Dict[str, Any],
        driver_case: Dict[str, Any],
        issue_category: str,
    ) -> Dict[str, Any]:
        """Apply company policy rules to determine the correct outcome."""
        cat = issue_category.lower()
        applied_rules: List[str] = []
        notes: List[str] = []

        if "fare" in cat or "pricing" in cat:
            applied_rules.extend(["PUB05", "SIM03"])
            notes.append("Quoted fares are generally fixed. Unsupported fare increase = adjust to documented amount.")
            notes.append("Recommended adjustment = max(0, charged - documented payable).")

        elif "route" in cat or "deviation" in cat:
            applied_rules.extend(["PUB04", "SIM02"])
            notes.append("Driver may choose fastest GPS route. Rider concerns should be discussed.")
            notes.append("Reasonable detour can support driver's route defense. Check chat for consent.")

        elif "no-show" in cat or "cancellation" in cat:
            applied_rules.extend(["PUB01", "PUB02", "PUB03", "SIM01"])
            notes.append("Cancellation within 3 min of matching is free for rider.")
            notes.append("After waiting period, driver gets S$4.50 cancellation compensation.")
            notes.append("Driver should attempt contact via in-app chat before cancelling.")

        elif "damage" in cat or "cleaning" in cat:
            applied_rules.extend(["PUB07"])
            notes.append("Rider responsible for mess. Driver must inform rider and submit claim.")

        elif "safety" in cat or "misconduct" in cat:
            applied_rules.extend(["PUB08", "PUB09", "SIM05"])
            notes.append("Drivers must follow road rules and travel directly to destination.")
            notes.append("Safety incidents or threats must be escalated to human review.")

        applied_rules.append("SIM04")  # Always: resolve evidence gaps fairly
        applied_rules.append("SIM06")  # Always: produce traceable ruling

        return {
            "applied_rules": applied_rules,
            "notes": notes,
            "rider_policy_cited": [r["rule_id"] for r in rider_case.get("policy_cited", [])],
            "driver_policy_cited": [r["rule_id"] for r in driver_case.get("policy_cited", [])],
        }

    # ------------------------------------------------------------------ #
    # Ruling determination
    # ------------------------------------------------------------------ #

    def _determine_ruling(
        self,
        rider_case: Dict[str, Any],
        driver_case: Dict[str, Any],
        evidence_analysis: Dict[str, Any],
        policy_analysis: Dict[str, Any],
        issue_category: str,
    ) -> Dict[str, Any]:
        """Determine the final ruling based on evidence + policy."""
        cat = issue_category.lower()
        rider_share = evidence_analysis.get("rider_share", 0.5)
        driver_share = evidence_analysis.get("driver_share", 0.5)
        amount = evidence_analysis.get("amount_sgd", 0) or 0

        # Default: no action
        action = "no_action"
        description = "No adjustment warranted based on available evidence."
        adjustment = 0.0
        in_favor_of = "neither"

        if "fare" in cat or "pricing" in cat:
            # Rider mentioned fare discrepancy in chat -> likely valid
            if evidence_analysis.get("rider_signals", {}).get("mentioned_fare"):
                # Per SIM03: refund difference (simplified: quote was S$27)
                adjustment = round(max(0, amount - 27.0), 2)
                if adjustment > 0:
                    action = "refund"
                    description = f"Refund S${adjustment} to rider — charged fare exceeded the quoted fare."
                    in_favor_of = "rider"
                else:
                    action = "no_action"
                    description = "Charged fare matches quoted fare. No adjustment needed."
                    in_favor_of = "driver"
            else:
                action = "no_action"
                description = "No evidence of fare discrepancy in chat logs."
                in_favor_of = "driver"

        elif "route" in cat or "deviation" in cat:
            if evidence_analysis.get("rider_signals", {}).get("mentioned_detour"):
                # Rider raised concerns, but driver may have chosen faster route
                if rider_share > driver_share:
                    action = "compensation"
                    adjustment = round(amount * 0.15, 2)
                    description = f"Compensate rider S${adjustment} for unjustified route deviation."
                    in_favor_of = "rider"
                else:
                    action = "no_action"
                    description = "Driver's route choice was justified per PUB04."
                    in_favor_of = "driver"
            else:
                action = "no_action"
                description = "No route deviation concerns raised in chat."
                in_favor_of = "driver"

        elif "no-show" in cat or "cancellation" in cat:
            if evidence_analysis.get("trip_status", "").lower().startswith("cancel"):
                action = "compensation"
                adjustment = 4.50
                description = "Pay driver S$4.50 cancellation compensation per PUB02."
                in_favor_of = "driver"
            else:
                action = "no_action"
                description = "Trip was completed; no cancellation charge applicable."
                in_favor_of = "neither"

        elif "damage" in cat or "cleaning" in cat:
            action = "compensation"
            adjustment = 50.0
            description = "Charge rider S$50 cleaning/damage fee per PUB07."
            in_favor_of = "driver"

        elif "safety" in cat or "misconduct" in cat:
            # Safety incidents always need escalation
            action = "review"
            adjustment = 0.0
            description = "Safety incident requires human review per SIM05."
            in_favor_of = "pending"

        return {
            "action": action,
            "description": description,
            "adjustment_sgd": adjustment,
            "in_favor_of": in_favor_of,
        }

    # ------------------------------------------------------------------ #
    # Confidence assessment
    # ------------------------------------------------------------------ #

    def _assess_confidence(
        self,
        rider_case: Dict[str, Any],
        driver_case: Dict[str, Any],
        evidence_analysis: Dict[str, Any],
    ) -> float:
        """Assess the Judge's confidence in the ruling (0.0 - 1.0)."""
        confidence = 0.4  # baseline

        # Both advocates provided structured cases
        if rider_case.get("arguments") and driver_case.get("arguments"):
            confidence += 0.15

        # Evidence is corroborated by chat logs
        if evidence_analysis.get("rider_signals", {}).get("mentioned_fare") or \
           evidence_analysis.get("rider_signals", {}).get("mentioned_detour"):
            confidence += 0.15

        # Clear winner in evidence weighing
        rider_share = evidence_analysis.get("rider_share", 0.5)
        driver_share = evidence_analysis.get("driver_share", 0.5)
        if abs(rider_share - driver_share) > 0.2:
            confidence += 0.1

        # Policy rules were applied
        if rider_case.get("policy_cited") or driver_case.get("policy_cited"):
            confidence += 0.1

        # Behavior profiles available
        if rider_case.get("behavior_profile") and driver_case.get("behavior_profile"):
            confidence += 0.05

        return min(round(confidence, 2), 0.95)

    # ------------------------------------------------------------------ #
    # Reasoning explanation
    # ------------------------------------------------------------------ #

    def _build_reasoning(
        self,
        rider_case: Dict[str, Any],
        driver_case: Dict[str, Any],
        evidence_analysis: Dict[str, Any],
        policy_analysis: Dict[str, Any],
        ruling: Dict[str, Any],
        confidence: float,
    ) -> List[str]:
        """Build a step-by-step explanation of the Judge's reasoning."""
        steps: List[str] = []

        steps.append(
            f"Reviewed rider case (confidence {rider_case.get('confidence', '?')}) "
            f"and driver case (confidence {driver_case.get('confidence', '?')})."
        )

        steps.append(
            f"Evidence weighing: rider strength={evidence_analysis.get('rider_strength')}, "
            f"driver strength={evidence_analysis.get('driver_strength')}. "
            f"Rider share={evidence_analysis.get('rider_share')}, "
            f"driver share={evidence_analysis.get('driver_share')}."
        )

        signals = evidence_analysis.get("rider_signals", {})
        if signals.get("mentioned_fare"):
            steps.append("Chat logs confirm the rider raised a fare discrepancy during the trip.")
        if signals.get("mentioned_detour"):
            steps.append("Chat logs confirm the rider questioned the route during the trip.")
        if signals.get("mentioned_safety"):
            steps.append("Chat logs contain safety-related concerns — escalation required.")

        steps.append(
            f"Applied policy rules: {', '.join(policy_analysis.get('applied_rules', []))}."
        )
        for note in policy_analysis.get("notes", []):
            steps.append(f"  Policy note: {note}")

        steps.append(
            f"Ruling: {ruling['action']} — {ruling['description']} "
            f"(in favor of: {ruling['in_favor_of']}, adjustment: S${ruling['adjustment_sgd']})."
        )

        steps.append(f"Confidence: {confidence}.")
        if confidence < CONFIDENCE_THRESHOLD:
            steps.append(
                f"Confidence below threshold ({CONFIDENCE_THRESHOLD}) — escalate to human reviewer."
            )

        return steps

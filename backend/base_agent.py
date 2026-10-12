"""
Base agent class — all three agents inherit from this.

Each agent:
  - Registers on the MCP bus with a name
  - Receives messages via _handle_message()
  - Can call helper methods to query the shared data layer
  - Logs its reasoning steps for transparency
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from mcp_bus import MCPBus, MCPMessage, MessageType
import data_layer

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for Rider Advocate, Driver Advocate, and Judge Agent."""

    name: str = "base_agent"
    description: str = ""

    def __init__(self, bus: MCPBus) -> None:
        self.bus = bus
        self.reasoning_log: List[Dict[str, str]] = []
        self.bus.register(self.name, self._handle_message)
        logger.info("Agent '%s' online", self.name)

    # ------------------------------------------------------------------ #
    # MCP message handling
    # ------------------------------------------------------------------ #

    def _handle_message(self, msg: MCPMessage) -> None:
        """Dispatch incoming MCP messages to type-specific handlers."""
        try:
            if msg.message_type == MessageType.CASE_OPENED:
                self.on_case_opened(msg)
            elif msg.message_type == MessageType.CASE_ASSIGNED:
                self.on_case_assigned(msg)
            elif msg.message_type == MessageType.EVIDENCE_REQUEST:
                self.on_evidence_request(msg)
            elif msg.message_type == MessageType.POLICY_QUERY:
                self.on_policy_query(msg)
            elif msg.message_type == MessageType.TRIP_DATA_QUERY:
                self.on_trip_data_query(msg)
            elif msg.message_type == MessageType.CASE_SUBMITTED:
                self.on_case_submitted(msg)
            elif msg.message_type == MessageType.RULING_ISSUED:
                self.on_ruling_issued(msg)
            elif msg.message_type == MessageType.PARTY_NOTIFIED:
                self.on_party_notified(msg)
            else:
                pass
        except Exception as exc:
            logger.exception("Agent %s error handling %s: %s", self.name, msg.message_type, exc)
            self.bus.send(
                self.name,
                "case_controller",
                MessageType.ERROR,
                {"error": str(exc), "original_message_type": msg.message_type.value},
                correlation_id=msg.correlation_id,
            )

    # ------------------------------------------------------------------ #
    # Override-able hooks (subclasses implement the ones they need)
    # ------------------------------------------------------------------ #

    def on_case_opened(self, msg: MCPMessage) -> None: ...
    def on_case_assigned(self, msg: MCPMessage) -> None: ...
    def on_evidence_request(self, msg: MCPMessage) -> None: ...
    def on_policy_query(self, msg: MCPMessage) -> None: ...
    def on_trip_data_query(self, msg: MCPMessage) -> None: ...
    def on_case_submitted(self, msg: MCPMessage) -> None: ...
    def on_ruling_issued(self, msg: MCPMessage) -> None: ...
    def on_party_notified(self, msg: MCPMessage) -> None: ...

    # ------------------------------------------------------------------ #
    # Reasoning log (shared by all agents for traceability)
    # ------------------------------------------------------------------ #

    def log_reasoning(self, step: str, detail: str = "") -> None:
        entry = {"agent": self.name, "step": step, "detail": detail}
        self.reasoning_log.append(entry)
        logger.info("[%s] %s: %s", self.name, step, detail[:200] if detail else "")
        # Also push a log message on the bus for the transcript
        self.bus.send(
            self.name,
            "case_controller",
            MessageType.LOG,
            entry,
        )

    # ------------------------------------------------------------------ #
    # Shared data-layer helpers (used by advocates and judge)
    # ------------------------------------------------------------------ #

    def fetch_trip_evidence(self, trip_id: str) -> Optional[Dict[str, Any]]:
        trip = data_layer.get_trip_by_id(trip_id)
        if not trip:
            self.log_reasoning("evidence_lookup", f"Trip {trip_id} not found")
            return None
        evidence = data_layer.extract_evidence(trip)
        self.log_reasoning("evidence_collected", f"Trip {trip_id}: {evidence['route']}, ${evidence['amount_sgd']}, cancelled={evidence['is_cancelled']}")
        return evidence

    def fetch_behavior_profile(self, name: str, role: str) -> Dict[str, Any]:
        profile = data_layer.get_behavior_profile(name, role)
        self.log_reasoning("behavior_profile", f"{role} '{name}': {profile['total_trips']} trips, {profile['completed_trips']} completed, {profile['cancelled_trips']} cancelled")
        return profile

    def fetch_relevant_policy(self, issue_category: str) -> List[Dict[str, Any]]:
        rules = data_layer.search_policy(issue_category)
        formatted = data_layer.format_policy_for_case(rules)
        self.log_reasoning(
            "policy_retrieved",
            f"Issue '{issue_category}' -> {len(formatted)} policy rules: {[r['rule_id'] for r in formatted]}",
        )
        return formatted

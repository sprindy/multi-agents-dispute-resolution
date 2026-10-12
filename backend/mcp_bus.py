"""
MCP (Model Context Protocol) message bus for inter-agent communication.

Each agent registers on the bus and can:
  - send_message(recipient, message_type, payload)
  - broadcast(message_type, payload)
  - receive messages via a callback

The bus is in-process (no external server needed) but follows the MCP
request/response pattern: agents communicate through typed messages
rather than direct function calls.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """All message types exchanged between agents via the MCP bus."""

    # Case lifecycle
    CASE_OPENED = "case_opened"
    CASE_ASSIGNED = "case_assigned"
    EVIDENCE_REQUEST = "evidence_request"
    EVIDENCE_RESPONSE = "evidence_response"
    CASE_SUBMITTED = "case_submitted"          # advocate -> judge
    RULING_ISSUED = "ruling_issued"            # judge -> controller
    CASE_CLOSED = "case_closed"
    PARTY_NOTIFIED = "party_notified"

    # Inter-agent queries
    POLICY_QUERY = "policy_query"
    POLICY_RESPONSE = "policy_response"
    TRIP_DATA_QUERY = "trip_data_query"
    TRIP_DATA_RESPONSE = "trip_data_response"

    # Misc
    LOG = "log"
    ERROR = "error"


@dataclass
class MCPMessage:
    """A single message on the MCP bus."""

    id: str
    sender: str
    recipient: Optional[str]          # None = broadcast
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None   # ties request/response pairs


class MCPBus:
    """
    In-process MCP message bus.

    Agents register with a name and a callback. Messages are delivered
    asynchronously to recipient callbacks. Broadcasts go to everyone.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[MCPMessage], Any]] = {}
        self._log: List[MCPMessage] = []
        self._lock = asyncio.Lock()

    def register(self, agent_name: str, handler: Callable[[MCPMessage], Any]) -> None:
        """Register an agent so it can receive messages."""
        self._handlers[agent_name] = handler
        logger.info("MCP bus: registered agent '%s'", agent_name)

    def unregister(self, agent_name: str) -> None:
        self._handlers.pop(agent_name, None)

    @property
    def registered_agents(self) -> List[str]:
        return list(self._handlers.keys())

    @property
    def message_log(self) -> List[MCPMessage]:
        """Full chronological log of every message that passed through the bus."""
        return list(self._log)

    def send(
        self,
        sender: str,
        recipient: str,
        message_type: MessageType,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> MCPMessage:
        """Send a direct message to a specific agent (synchronous delivery)."""
        msg = self._build_message(sender, recipient, message_type, payload, correlation_id)
        self._deliver(msg)
        return msg

    def broadcast(
        self,
        sender: str,
        message_type: MessageType,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> MCPMessage:
        """Broadcast a message to all registered agents."""
        msg = self._build_message(sender, None, message_type, payload, correlation_id)
        self._deliver(msg)
        return msg

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #

    def _build_message(
        self,
        sender: str,
        recipient: Optional[str],
        message_type: MessageType,
        payload: Optional[Dict[str, Any]],
        correlation_id: Optional[str],
    ) -> MCPMessage:
        return MCPMessage(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            payload=payload or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

    def _deliver(self, msg: MCPMessage) -> None:
        """Store the message and deliver it to recipient(s) synchronously."""
        self._log.append(msg)
        logger.debug(
            "MCP %s: %s -> %s | %s",
            msg.message_type.value,
            msg.sender,
            msg.recipient or "BROADCAST",
            {k: v for k, v in msg.payload.items() if k != "evidence"},
        )

        if msg.recipient is not None:
            handler = self._handlers.get(msg.recipient)
            if handler is None:
                logger.warning("MCP bus: no handler for '%s'", msg.recipient)
                return
            handler(msg)
        else:
            for name, handler in self._handlers.items():
                if name == msg.sender:
                    continue
                handler(msg)

    def get_transcript(self) -> List[Dict[str, Any]]:
        """Return a JSON-serializable transcript of all messages."""
        return [
            {
                "id": m.id,
                "sender": m.sender,
                "recipient": m.recipient,
                "type": m.message_type.value,
                "payload_keys": list(m.payload.keys()),
                "timestamp": m.timestamp,
                "correlation_id": m.correlation_id,
            }
            for m in self._log
        ]

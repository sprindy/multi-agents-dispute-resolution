"""
Shared Evidence & Policy data layer.

Provides read access to the SQLite database for all agents:
  - Trip data (rider_trips / driver_trips tables)
  - Dispute policy (dispute_policy / policy_sources tables)

Agents query this layer through the MCP bus via TRIP_DATA_QUERY / POLICY_QUERY
messages, and receive TRIP_DATA_RESPONSE / POLICY_RESPONSE messages back.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

from mcp_bus import MCPBus, MCPMessage, MessageType

logger = logging.getLogger(__name__)

_DB_PATH = os.environ.get(
    "RYDE_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "database", "ryde_trips.db"),
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------------------------------- #
# Evidence collection
# --------------------------------------------------------------------------- #

def get_trip_by_id(trip_id: str) -> Optional[Dict[str, Any]]:
    """Look up a trip across both rider_trips and driver_trips tables."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM rider_trips WHERE trip_id = ? UNION ALL "
            "SELECT * FROM driver_trips WHERE trip_id = ?",
            (trip_id, trip_id),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_rider_trip(trip_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM rider_trips WHERE trip_id = ?", (trip_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_driver_trip(trip_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM driver_trips WHERE trip_id = ?", (trip_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_trips_for_rider(rider_name: str) -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM rider_trips WHERE rider_name = ? ORDER BY datetime_sgt",
            (rider_name,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_trips_for_driver(driver_name: str) -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM driver_trips WHERE driver_name = ? ORDER BY datetime_sgt",
            (driver_name,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def extract_evidence(trip: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured evidence fields from a trip record, following the
    Shared Evidence & Policy Layer categories in the architecture:

      - GPS & telemetry   -> derived from route fields
      - Chat logs         -> chat_history column
      - Payment & fares   -> amount_sgd + status
      - Behavior profiles  -> trip history (past trips for same person)
    """
    chat = trip.get("chat_history") or ""
    chat_lines = [l.strip() for l in chat.split("\n") if l.strip()]

    return {
        "trip_id": trip.get("trip_id"),
        "rider_name": trip.get("rider_name"),
        "driver_name": trip.get("driver_name"),
        "datetime_sgt": trip.get("datetime_sgt"),
        "pickup": trip.get("pickup"),
        "destination": trip.get("destination"),
        "status": trip.get("status"),
        "amount_sgd": trip.get("amount_sgd"),
        "route": f"{trip.get('pickup')} -> {trip.get('destination')}",
        "chat_lines": chat_lines,
        "chat_raw": chat,
        # Derived signals
        "is_cancelled": bool(
            trip.get("status") and "cancel" in trip["status"].lower()
        ),
        "mentioned_detour": bool(
            re.search(r"route|detour|expressway|leaving|stopped|deviation", chat, re.I)
        ),
        "mentioned_fare": bool(
            re.search(r"fare|charge|overcharge|quote|\\$", chat, re.I)
        ),
        "mentioned_safety": bool(
            re.search(r"safety|unsafe|rude|misconduct|danger|threat", chat, re.I)
        ),
    }


def get_behavior_profile(person_name: str, role: str) -> Dict[str, Any]:
    """Build a simple behavior profile from trip history."""
    if role == "rider":
        trips = get_all_trips_for_rider(person_name)
    else:
        trips = get_all_trips_for_driver(person_name)

    completed = [t for t in trips if t.get("status") == "Completed"]
    cancelled = [t for t in trips if "cancel" in (t.get("status") or "").lower()]
    total_spend = sum(t.get("amount_sgd") or 0 for t in completed)

    return {
        "person": person_name,
        "role": role,
        "total_trips": len(trips),
        "completed_trips": len(completed),
        "cancelled_trips": len(cancelled),
        "total_spend_sgd": round(total_spend, 2),
        "account_age_trips": len(trips),   # simplified
    }


# --------------------------------------------------------------------------- #
# Policy access
# --------------------------------------------------------------------------- #

def get_all_policy_rules() -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM dispute_policy ORDER BY rule_id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_policy_by_rule_id(rule_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM dispute_policy WHERE rule_id = ?", (rule_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_policy_sources(source_ids: str) -> List[Dict[str, Any]]:
    """source_ids is a comma-separated string from the dispute_policy table."""
    ids = [s.strip() for s in source_ids.split(",") if s.strip()]
    if not ids:
        return []
    conn = _connect()
    try:
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT * FROM policy_sources WHERE source_id IN ({placeholders})", ids
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search_policy(query: str) -> List[Dict[str, Any]]:
    """Search dispute_policy title + description for keywords in the query."""
    keywords = [w for w in re.split(r"[^a-zA-Z]+", query) if len(w) > 2]
    if not keywords:
        return get_all_policy_rules()

    conn = _connect()
    try:
        conditions = " OR ".join(
            ["LOWER(title) LIKE ? OR LOWER(description) LIKE ?"] * len(keywords)
        )
        params = []
        for kw in keywords:
            params.extend([f"%{kw.lower()}%", f"%{kw.lower()}%"])
        rows = conn.execute(
            f"SELECT * FROM dispute_policy WHERE {conditions} ORDER BY rule_id", params
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def format_policy_for_case(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format policy rules with their sources for inclusion in a case report."""
    out = []
    for r in rules:
        sources = get_policy_sources(r.get("source_ids") or "")
        out.append({
            "rule_id": r["rule_id"],
            "rule_type": r["rule_type"],
            "title": r["title"],
            "description": r["description"],
            "sources": [{"source_id": s["source_id"], "title": s["title"], "url": s["url"]} for s in sources],
        })
    return out

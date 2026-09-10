"""
WebSocket Connection Manager for real-time security event streaming.
Supports multiple clients, role-filtered broadcasting, and safe disconnect handling.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any

from fastapi import WebSocket

from app.realtime.events import SecurityEvent

logger = logging.getLogger(__name__)


class _ClientInfo:
    """Metadata for a connected WebSocket client."""
    __slots__ = ("websocket", "user_id", "role")

    def __init__(self, websocket: WebSocket, user_id: str, role: str):
        self.websocket = websocket
        self.user_id = user_id
        self.role = role


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time security event streaming.

    Features:
    - Multiple concurrent clients
    - Role-filtered broadcasting (USER sees own events, ANALYST/ADMIN see all)
    - Safe disconnect: one client's failure never crashes the broadcast
    - Active connection count tracking
    """

    def __init__(self):
        self._clients: List[_ClientInfo] = []

    async def connect(self, websocket: WebSocket, user_id: str, role: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._clients.append(_ClientInfo(websocket, user_id, role))
        logger.info(f"WebSocket connected: user={user_id}, role={role}, total={self.connection_count}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket client safely."""
        self._clients = [c for c in self._clients if c.websocket is not websocket]
        logger.info(f"WebSocket disconnected, remaining={self.connection_count}")

    @property
    def connection_count(self) -> int:
        """Returns the number of currently connected clients."""
        return len(self._clients)

    @property
    def has_connections(self) -> bool:
        """Returns True if there is at least one active connection."""
        return len(self._clients) > 0

    async def broadcast(self, event: SecurityEvent) -> None:
        """
        Broadcast a security event to all authorized connected clients.

        Role-based filtering:
        - ADMIN / SECURITY_ANALYST: receive all events
        - USER: receive only events matching their user_id or session-unscoped system events
        """
        event_dict = event.to_dict()
        event_user_id = event.user_id
        disconnected = []

        for client in self._clients:
            # Role-based visibility filter
            if not self._client_can_see(client, event_user_id):
                continue

            try:
                await client.websocket.send_json(event_dict)
            except Exception:
                # Isolate failed client — never crash the broadcast loop
                disconnected.append(client)
                logger.debug(f"Failed to send to client user={client.user_id}, marking for removal")

        # Clean up disconnected clients
        for client in disconnected:
            self._clients = [c for c in self._clients if c is not client]

    def _client_can_see(self, client: _ClientInfo, event_user_id: Optional[str]) -> bool:
        """
        Determines if a client is authorized to see an event.
        ADMIN and SECURITY_ANALYST see all events.
        USER sees only events where user_id matches or event has no user scope.
        """
        role = (client.role or "").upper()
        if role in ("ADMIN", "SECURITY_ANALYST"):
            return True
        # USER: only sees own events or unscoped events
        if event_user_id is None:
            return True
        return client.user_id == event_user_id

    async def broadcast_dict(self, data: Dict[str, Any]) -> None:
        """Broadcast a raw dictionary to all connected clients (no filtering)."""
        disconnected = []
        for client in self._clients:
            try:
                await client.websocket.send_json(data)
            except Exception:
                disconnected.append(client)
        for client in disconnected:
            self._clients = [c for c in self._clients if c is not client]


# Global singleton instance
ws_manager = WebSocketConnectionManager()

# app/core/websocket.py
import asyncio
import logging

from fastapi import WebSocket

from backend.app.model.schemas import OutgoingWSMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections, grouped by project_id.
    Ensures thread-safe operations and clean disconnect handling.
    """

    def __init__(self):
        # project_id -> Set of active WebSockets
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, project_id: str):
        """Accepts the websocket and adds it to the project's connection pool."""
        await websocket.accept()
        async with self.lock:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()
            self.active_connections[project_id].add(websocket)
        logger.info(f"Client connected to project: {project_id}")

    async def disconnect(self, websocket: WebSocket, project_id: str):
        """Removes the websocket from the project's connection pool."""
        async with self.lock:
            if project_id in self.active_connections:
                self.active_connections[project_id].discard(websocket)
                # Clean up empty project sets to prevent memory leaks
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]
        logger.info(f"Client disconnected from project: {project_id}")

    async def send_personal_message(self, message: OutgoingWSMessage, websocket: WebSocket):
        """Sends a strictly typed Pydantic model as JSON to a specific client."""
        try:
            # model_dump() ensures we output standard JSON compatible with the frontend
            await websocket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")

    async def broadcast_to_project(self, message: OutgoingWSMessage, project_id: str):
        """Broadcasts a message to all clients connected to a specific project."""
        async with self.lock:
            connections = self.active_connections.get(project_id, set()).copy()

        # Send concurrently to avoid blocking the stream if one client is slow
        tasks = [self.send_personal_message(message, ws) for ws in connections]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global singleton instance
manager = ConnectionManager()

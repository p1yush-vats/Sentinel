import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.department_map: dict[str, set] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")

    async def broadcast_to_department(self, message: dict, department: str):
        """Broadcast a message to all connected users belonging to a department.
        
        The manager tracks connections by user_id. The department mapping is
        stored separately in a dict updated on connect/disconnect.
        We broadcast to *all* connections and let the client filter, but we
        also support a smarter routing if department_map is populated.
        """
        user_ids = self.department_map.get(department, set())
        for uid in user_ids:
            if uid in self.active_connections:
                for connection in self.active_connections[uid]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to dept {department}: {e}")

    async def broadcast_presence(self, user_id: str, department: str, status: str):
        """Broadcasts a presence update to all users in the same department."""
        payload = {
            "type": "presence",
            "user_id": user_id,
            "status": status
        }
        await self.broadcast_to_department(payload, department)

    async def set_user_department(self, user_id: str, department: str):
        """Register a user's department so we can do department-scoped broadcasts."""
        if department not in self.department_map:
            self.department_map[department] = set()
            
        was_offline = user_id not in self.department_map[department]
        self.department_map[department].add(user_id)
        
        if was_offline:
            await self.broadcast_presence(user_id, department, "online")

    async def unset_user_department(self, user_id: str):
        """Remove a user from all department maps on disconnect."""
        for dept, dept_users in self.department_map.items():
            if user_id in dept_users:
                dept_users.discard(user_id)
                await self.broadcast_presence(user_id, dept, "offline")

manager = ConnectionManager()

from typing import List, Dict
from uuid import UUID

from fastapi import WebSocket


class SocketConnectionManager:
    def __init__(self):
        self.connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: UUID):
        if user_id in self.connections:
            if websocket in self.connections[user_id]:
                self.connections[user_id].remove(websocket)
        if not self.connections[user_id]:
            del self.connections[user_id]

    async def send_message(self, user_id: UUID, message: dict):
        if self.connections.get(user_id):
            for websocket in self.connections[user_id]:
                await websocket.send_json(message)

socket_manager = SocketConnectionManager()
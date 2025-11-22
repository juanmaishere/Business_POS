from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.rooms:
            self.rooms[room] = []
        self.rooms[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.rooms:
            try:
                self.rooms[room].remove(websocket)
            except ValueError:
                pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, room: str, message: str):
        if room in self.rooms:
            for connection in list(self.rooms[room]):
                try:
                    await connection.send_text(message)
                except Exception:
                    # if send fails, remove connection
                    try:
                        self.rooms[room].remove(connection)
                    except ValueError:
                        pass

manager = ConnectionManager()

import asyncio

@router.websocket("/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=20)
            except asyncio.TimeoutError:
                # send ping or continue loop so socket stays alive
                continue
            await manager.broadcast(room, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)

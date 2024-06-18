import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity; adjust as needed.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, node_name: str):
        await websocket.accept()
        self.active_connections[node_name] = websocket
        logging.info(f"Node connected: {node_name}")

    def disconnect(self, node_name: str):
        if node_name in self.active_connections:
            del self.active_connections[node_name]
            logging.info(f"Node disconnected: {node_name}")

    async def send_to_node(self, target_node: str, data: str):
        connection = self.active_connections.get(target_node)
        if connection:
            try:
                await connection.send_text(data)
                logging.info(f"Data sent to node {target_node}")
            except Exception as e:
                logging.error(f"Error sending data to {target_node}: {e}")

manager = ConnectionManager()

@app.websocket("/ws/{node_name}")
async def websocket_endpoint(websocket: WebSocket, node_name: str):
    logging.info(f"WebSocket connection request received for node: {node_name}")
    await manager.connect(websocket, node_name)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                logging.info(f"Data received: {data}")
                message = json.loads(data)
                target_node = message.get("target_node")
                source_node = message.get("source_node")
                if target_node:
                    await manager.send_to_node(target_node, data)
            except WebSocketDisconnect:
                logging.info(f"WebSocket disconnected for node: {node_name}")
                manager.disconnect(node_name)
                break
    except Exception as e:
        logging.error(f"Connection error: {e}")
        manager.disconnect(node_name)
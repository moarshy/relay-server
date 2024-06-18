import os
import sys
import asyncio
import logging
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
from node import Node

def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    return logger

logger = get_logger()
load_dotenv()

app = FastAPI()
node_id = os.getenv("NODE_ID", "default_node_id")  # Ensure to set NODE_ID in your environment or use unique default
node = Node(node_id, os.getenv("RELAY_URL", "ws://localhost:8765"))

class MessageRequest(BaseModel):
    target_node_id: str
    message: dict

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await node.connect()
    try:
        while True:
            data = await websocket.receive_text()
            await node.send_message(node.node_id, {"message": data})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

@app.post("/send_message/")
async def send_message(request: MessageRequest, background_tasks: BackgroundTasks):
    if not node.connected:
        await node.connect()
    background_tasks.add_task(node.send_message, request.target_node_id, request.message)
    return {"status": "Message sent"}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(node.connect())

@app.on_event("shutdown")
async def shutdown_event():
    await node.disconnect()
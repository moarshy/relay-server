import asyncio
import websockets
import base64
import io
import json
import os
import shutil
import zipfile
from fastapi import UploadFile
from pathlib import Path
from uuid import uuid4
import logging
from concurrent.futures import ThreadPoolExecutor

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

NODE_ID = "node_2"
CHUNK_SIZE = 256 * 1024  # Ensure the receiver uses the same chunk size
TEMP_FILES = {}
BASE_OUTPUT_DIR = "."
executor = ThreadPoolExecutor(max_workers=4)


def decode_file_data(file_data: str, filename: str) -> UploadFile:
    """Decode a base64 encoded file to an UploadFile object."""
    file_bytes = base64.b64decode(file_data)
    file_stream = io.BytesIO(file_bytes)
    return UploadFile(filename=filename, file=file_stream)


def encode_file_data(file_path: str) -> str:
    """Encode a file to a base64 encoded string."""
    with open(file_path, "rb") as file:
        file_data = file.read()
    return base64.b64encode(file_data).decode('utf-8')


async def write_storage(file: UploadFile):
    """Write files to the storage."""
    logger.info(f"Received request to write files to storage: {file.filename}")
    folder_name = uuid4().hex
    folder_path = Path(BASE_OUTPUT_DIR) / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    temp_file_path = folder_path / file.filename

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file.filename.endswith(".zip"):
        with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
            zip_ref.extractall(folder_path)

        # delete zip file
        os.remove(temp_file_path)

    return 201, {"message": "Files written to storage", "folder_id": folder_name}


async def write_storage_ws(websocket, message: dict):
    """Write files to the storage."""
    target_node_id = message['source_node']
    source_node_id = message['target_node']
    params = message['params']
    response = {
        'target_node': target_node_id,
        'source_node': source_node_id
    }
    filename = params['filename']
    file_data = params['file_data']

    temp_dir = os.path.join(BASE_OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_filepath = os.path.join(temp_dir, f"{source_node_id}_{filename}.part")

    try:
        if file_data == 'EOF':
            # Handle EOF: process the accumulated file
            if temp_filepath in TEMP_FILES:
                with open(TEMP_FILES[temp_filepath], "rb") as temp_file:
                    file = UploadFile(filename=filename, file=temp_file)
                    status_code, message_dict = await write_storage(file)
                    logger.info(f"Status code: {status_code}, message: {message_dict}")
                    if status_code == 201:
                        response['params'] = message_dict
                    else:
                        response['params'] = {'error': message_dict['message']}
                os.remove(TEMP_FILES[temp_filepath])
                del TEMP_FILES[temp_filepath]
                logger.info(f"Completed file transfer and saved file: {filename}")
            else:
                response['params'] = {'error': 'File transfer not found'}
        else:
            # Accumulate chunks
            chunk = base64.b64decode(file_data)
            if temp_filepath not in TEMP_FILES:
                TEMP_FILES[temp_filepath] = temp_filepath

            with open(TEMP_FILES[temp_filepath], "ab") as temp_file:
                temp_file.write(chunk)

            logger.info(f"Received chunk for file {filename}")
            response['params'] = {'status': 'Chunk received'}

        logger.info(f"Response: {response}")
        await websocket.send(json.dumps(response))
    except Exception as e:
        response['params'] = {'error': str(e)}
        await websocket.send(json.dumps(response))


async def websocket_handler(uri):
    """Handles persistent WebSocket connection."""
    async with websockets.connect(uri, ping_interval=None) as websocket:
        logger.info("Connected to relay server")
        try:
            while True:
                try:
                    message = await websocket.recv()
                    message = json.loads(message)
                    logger.info(f"Received message from relay server: {message}")
                    if message["path"] == "write_storage":
                        await write_storage_ws(
                            websocket=websocket,
                            message=message
                        )

                except Exception as e:
                    logger.error(f"Error: {e}")
                    response = {
                        'target_node': message['source_node'],
                        'source_node': message['target_node'],
                        'params': {'error': str(e)}
                    }
                    await websocket.send(json.dumps(response))
        except websockets.ConnectionClosed:
            logger.error("WebSocket connection closed unexpectedly")

# Start the event loop
async def main():
    import sys
    uri = sys.argv[1] if len(sys.argv) > 1 else f'ws://localhost:8765/ws'
    uri = f"{uri}/{NODE_ID}"
    await websocket_handler(uri=uri)

if __name__ == "__main__":
    asyncio.run(main())
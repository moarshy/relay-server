import asyncio
import websockets
import json
import base64
import os
import logging
import concurrent.futures

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

NODE_ID = "node_1"
CHUNK_SIZE = 256 * 1024


def encode_file_data(file_path: str) -> str:
    """Encode a file to a base64 encoded string."""
    with open(file_path, "rb") as file:
        file_data = file.read()
    return base64.b64encode(file_data).decode('utf-8')


async def send_file(websocket, file_path, filename, target_node):
    file_size = os.path.getsize(file_path)
    chunk_index = 0

    with open(file_path, "rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            encoded_chunk = base64.b64encode(chunk).decode('utf-8')
            params = {
                'source_node': NODE_ID,
                'target_node': target_node,
                'path': 'write_storage',
                'params': {
                    'filename': filename,
                    'file_data': encoded_chunk,
                    'chunk_index': chunk_index,
                    'chunk_total': (file_size // CHUNK_SIZE) + 1
                }
            }

            await websocket.send(json.dumps(params))
            logger.info(f"Sent chunk {chunk_index + 1} of {params['params']['chunk_total']}")
            chunk_index += 1

    # Send an EOF message to signal the end of the file transfer
    eof_params = {
        'source_node': NODE_ID,
        'target_node': target_node,
        'path': 'write_storage',
        'params': {
            'filename': filename,
            'file_data': 'EOF',
            'chunk_index': chunk_index,
            'chunk_total': (file_size // CHUNK_SIZE) + 1
        }
    }
    await websocket.send(json.dumps(eof_params))
    logger.info("EOF sent")


async def interactive_mode(file_path: str):
    target_node = "node_2"
    filename = os.path.basename(file_path)

    async with websockets.connect(URI, ping_interval=None) as websocket:
        await send_file(websocket, file_path, filename, target_node)

        # Handle multiple responses
        while True:
            try:
                response = await websocket.recv()
                response_data = json.loads(response)['params']
                logger.info(f"Response: {response_data}")

                if 'message' in response_data or 'error' in response_data:
                    break

            except websockets.ConnectionClosed:
                logger.info("WebSocket connection closed")
                break

if __name__ == "__main__":
    import sys
    file_path = sys.argv[1] if len(sys.argv) > 1 else 'output.png'
    uri = sys.argv[2] if len(sys.argv) > 2 else 'ws://localhost:8765/ws'
    uri = f"{uri}/{NODE_ID}"
    asyncio.run(interactive_mode(file_path))
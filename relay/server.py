import asyncio
import websockets
import msgpack
import logging

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
connected_nodes = {}

async def handler(websocket, path):
    try:
        initial_message = await websocket.recv()
        node_id = msgpack.unpackb(initial_message, raw=False)['node_id']
        connected_nodes[node_id] = websocket
        logger.info(f"Node {node_id} registered")

        async for message in websocket:
            try:
                data = msgpack.unpackb(message, raw=False)
                target_id = data['target']
                if target_id in connected_nodes:
                    await connected_nodes[target_id].send(message)
                    logger.info(f"Message relayed from {node_id} to {target_id}")
                else:
                    logger.warning(f"Target node {target_id} not found")
            except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackValueError) as e:
                logger.error(f"Unpacking error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
    except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackValueError) as e:
        logger.error(f"Unpacking error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        del connected_nodes[node_id]
        logger.info(f"Node {node_id} unregistered")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        logger.info("Relay server started")
        await asyncio.Future()  # run forever

asyncio.run(main())
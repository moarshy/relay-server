import asyncio
import websockets
import msgpack

class Node:
    def __init__(self, node_id, relay_server):
        self.node_id = node_id
        self.relay_server = relay_server
        self.connected = False
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.relay_server)
            await self.register_node()
            self.connected = True
            asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            print(f"Connection error: {e}")

    async def register_node(self):
        register_message = msgpack.packb({'node_id': self.node_id}, use_bin_type=True)
        await self.websocket.send(register_message)

    async def listen_for_messages(self):
        while self.connected:
            try:
                response = await self.websocket.recv()
                data = msgpack.unpackb(response, raw=False)
                print(f"Received: {data}")
            except websockets.ConnectionClosed:
                print("Connection closed")
                self.connected = False
            except Exception as e:
                print(f"Error: {e}")
                self.connected = False

    async def send_message(self, target_node_id, message):
        if not self.connected or not self.websocket:
            raise Exception("Node is not connected.")
        payload = {
            "source": self.node_id,
            "target": target_node_id,
            "payload": message
        }
        await self.websocket.send(msgpack.packb(payload, use_bin_type=True))

    async def disconnect(self):
        if self.websocket:
            self.connected = False
            await self.websocket.close()
# File Transfer Relay Server

This project consists of three main components:
1. `relay_server`: Handles WebSocket connections and relays messages between nodes.
2. `receiver.py`: Mimics a node that receives and processes file chunks.
3. `sender.py`: Sends file chunks to the relay server.

## Usage

### 1. Launch the Relay Server

The relay server handles WebSocket connections and relays messages between nodes. Start the relay server with the following command:

```bash
./launch.sh
```

### 2. Start the Receiver Node
The receiver node mimics a node that receives and processes file chunks. Start the receiver with the following command:
```bash
python receiver.py
```

### 3. Start the Sender Node
The sender node sends file chunks to the relay server. Start the sender with the following command:

```bash
python sender.py path/to/file.png
```

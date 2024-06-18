# Relay Server and Node Setup

## Overview

This setup consists of a relay server and multiple nodes that communicate through the relay server. Each node is an instance of a FastAPI application. Nodes can send messages to each other through the relay server.

## Prerequisites

	•	Python 3.7+
	•	uvicorn for running the FastAPI app
	•	websockets library
	•	msgpack library
	•	fastapi library
	•	requests library (for sending HTTP requests)

## Setup

1. Relay Server

Start the relay server with the following command:
```bash
python relay/server.py
```

2. Node 1
Start Node 1 with a unique NODE_ID:
```bash
NODE_ID=node_1 uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

3. Node 2
Start Node 2 with a different unique NODE_ID:
```bash
NODE_ID=node_2 uvicorn server:app --host 0.0.0.0 --port 8002 --reload
```

## Sending Messages
Send a message from Node 1 to Node 2 using the following code:
```python
import requests

u = "http://localhost:8000/send_message/"

r = requests.post(u, json={
    "target_node_id": "node_2", 
    "message": {
        "type": "text",
        "content": "Hello"
    }
})

print(r.status_code)
print(r.json())
```

## Checking Logs
Check the logs of Node 2 to see if the message was received.
Node 2 Logs
The logs of Node 2 will show the received message. Make sure you have the logging level set to INFO to see the logs.

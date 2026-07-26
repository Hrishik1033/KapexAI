# Queue & Streaming

This document explains how the backend enqueues jobs and streams results back to the frontend via Redis.

## Flow overview

```
Frontend                    Backend                      Worker
   │                          │                           │
   │  POST /create_chat_session                            │
   │─────────────────────────►│                           │
   │                          │  1. Create Session (DB)   │
   │                          │  2. LPUSH jobs:queue      │
   │  { session_id }          │──────────────────────────►│
   │◄─────────────────────────│  3. BRPOP jobs:queue      │
   │                          │                           │
   │  WS /ws/session/{id}     │                           │
   │════════════════════════►│                           │
   │                          │  4. Run agentic workflow  │
   │                          │                           │
   │                          │  5. PUBLISH stream:{id}   │
   │◄═════════════════════════│◄──────────────────────────│
   │     { type: "token" }    │      (via redis.publish)  │
   │◄═════════════════════════│◄──────────────────────────│
   │     { type: "token" }    │                           │
   │◄═════════════════════════│◄──────────────────────────│
   │     { type: "end" }      │                           │
```

## Job queue (`jobs:queue`)

The backend pushes jobs to a Redis list. The worker pops them.

### Backend — enqueue

In `POST /create_chat_session` (`backend/main.py:68-69`):

```python
job = {"session_id": session.id, "user_input": user_data.business_idea}
await redis.lpush("jobs:queue", json.dumps(job))
```

### Worker — dequeue

The worker should block-pop from the queue in its main loop:

```python
import json
from redis_service import redis

while not stop.is_set():
    result = await redis.brpop("jobs:queue", timeout=5)
    if result is None:
        continue

    key, raw = result  # key is "jobs:queue"
    job = json.loads(raw)
    session_id = job["session_id"]
    user_input = job["user_input"]

    # --- run agentic workflow ---
    # ...
```

## Streaming results (`stream:{session_id}`)

The worker publishes results to a Redis pub/sub channel. The WebSocket endpoint subscribes to that channel and forwards messages to the frontend.

### Worker — publish

After (or during) processing, the worker publishes each chunk to the session's channel:

```python
await redis.publish(f"stream:{session_id}", json.dumps({"type": "token", "content": "Hello"}))
# ... more tokens ...
await redis.publish(f"stream:{session_id}", json.dumps({"type": "end"}))
```

### Backend WebSocket — subscribe

`GET /ws/session/{session_id}` (`backend/main.py:77-92`):

```python
@app.websocket("/ws/session/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"stream:{session_id}")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            await websocket.send_json(data)
            if data.get("type") == "end":
                break

    await pubsub.unsubscribe(f"stream:{session_id}")
    await pubsub.close()
    await websocket.close()
```

### Message protocol

Each message published to `stream:{session_id}` is a JSON string with this shape:

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Message type — `"token"`, `"end"`, or future types |
| `content` | `string` | The chunk content (only present for `"token"` type) |

The frontend receives these as JSON frames over the WebSocket. It should concatenate `"token"` payloads until it receives `"end"`.

## Session status

The `Session.status` enum (`services/database/schema.prisma`) tracks lifecycle:

| Status | Meaning |
|---|---|
| `PENDING` | Initial state after creation (should be default) |
| `ACTIVE` | Worker is processing or has completed |
| `FAILED` | Worker encountered an error |

The worker should update the session status in the database as it processes.

## Key considerations

- **Pub/sub is fire-and-forget** — if no WebSocket is connected, published messages are lost. The worker should still save the assistant's full response as a `Message` row in the database for history.
- **One channel per session** — `stream:{session_id}` is unique per session. Only one WebSocket client should connect per session.
- **Cleanup** — consider calling `await redis.expire(f"stream:{session_id}", 3600)` after the session ends to remove any residual data if you switch to a list-based approach.

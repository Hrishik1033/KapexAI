# Services

## `db-service` — PostgreSQL via Prisma

**Package:** `services/database/` (published as `db-service`)

Provides a singleton Prisma async client for PostgreSQL.

| Export | Type | Description |
|---|---|---|
| `db` | `Prisma` instance | ORM client — use for queries (e.g. `await db.user.find_many()`) |
| `connect_db()` | `async` | Connect to PostgreSQL. Idempotent. |
| `disconnect_db()` | `async` | Disconnect from PostgreSQL. Idempotent. |

Usage:

```python
from db_service import db, connect_db, disconnect_db

await connect_db()
users = await db.user.find_many()
await disconnect_db()
```

Connection string via `DATABASE_URL` env var. After schema changes, run `make generate && make migrate`.

---

## `redis-service` — Upstash Redis

**Package:** `services/redis-service/` (published as `redis-service`)

Provides a singleton Upstash Redis REST client. All calls are synchronous (REST-based, no persistent TCP connection).

| Export | Type | Description |
|---|---|---|
| `redis` | `Redis` instance | Redis client — use for commands (e.g. `redis.get("key")`) |
| `connect_redis()` | `sync` | Verifies connectivity via `ping()`. |
| `disconnect_redis()` | `sync` | No-op (Upstash has no persistent connection). |

Usage:

```python
from redis_service import redis, connect_redis, disconnect_redis

connect_redis()
redis.set("key", "value")
val = redis.get("key")
disconnect_redis()
```

Requires env vars `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.

---

## Service lifecycle

### Backend (FastAPI)

Both services are connected on startup and disconnected on shutdown via FastAPI's `lifespan`:

```
startup  → await connect_db() → connect_redis()
shutdown → await disconnect_db() → disconnect_redis()
```

### Worker

Currently only uses `db-service`:

```python
await connect_db()
# ... main loop ...
await disconnect_db()
```

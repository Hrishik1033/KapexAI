import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from backend.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def mock_lifespan():
    with (
        patch("backend.main.connect_db", new_callable=AsyncMock),
        patch("backend.main.disconnect_db", new_callable=AsyncMock),
        patch("backend.main.connect_redis", new_callable=AsyncMock),
        patch("backend.main.disconnect_redis", new_callable=AsyncMock),
    ):
        yield


@pytest.fixture(autouse=True)
async def lifespan_events(mock_lifespan):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.get("/health")
    yield


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_ok(self, client):
        async with client as c:
            response = await c.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ── Waitlist ─────────────────────────────────────────────────────────────────

class TestWaitlistEndpoint:
    @pytest.mark.asyncio
    async def test_join_waitlist_with_email_only(self, client):
        async with client as c:
            response = await c.post("/waitlist", json={"email": "test@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully joined the waitlist!"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_join_waitlist_with_email_and_name(self, client):
        async with client as c:
            response = await c.post(
                "/waitlist", json={"email": "test@example.com", "name": "John Doe"}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully joined the waitlist!"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_join_waitlist_invalid_email(self, client):
        async with client as c:
            response = await c.post("/waitlist", json={"email": "not-an-email"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_join_waitlist_missing_email(self, client):
        async with client as c:
            response = await c.post("/waitlist", json={"name": "John Doe"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_join_waitlist_empty_email(self, client):
        async with client as c:
            response = await c.post("/waitlist", json={"email": ""})
        assert response.status_code == 422


# ── CORS ──────────────────────────────────────────────────────────────────────

class TestCORSMiddleware:
    @pytest.mark.asyncio
    async def test_cors_allows_localhost_3000(self, client):
        async with client as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_cors_allows_credentials(self, client):
        async with client as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_allows_all_methods(self, client):
        async with client as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allowed_methods
        assert "GET" in allowed_methods

    @pytest.mark.asyncio
    async def test_cors_allows_all_headers(self, client):
        async with client as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,authorization",
                },
            )
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        assert "content-type" in allowed_headers.lower()
        assert "authorization" in allowed_headers.lower()

    @pytest.mark.asyncio
    async def test_cors_blocks_other_origins(self, client):
        async with client as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://evil.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"


# ── Create Chat Session ──────────────────────────────────────────────────────

class TestCreateChatSession:
    @pytest.mark.asyncio
    async def test_creates_session_and_pushes_job(self, client):
        session_id = "session-456"

        with (
            patch("backend.main.get_user", new_callable=AsyncMock, return_value=Mock(id="user-123", email="test@test.com")),
            patch("backend.main.db") as mock_db,
            patch("backend.main.redis.lpush", new_callable=AsyncMock) as mock_lpush,
        ):
            mock_db.session.create = AsyncMock(return_value=Mock(id=session_id))

            async with client as c:
                response = await c.post(
                    "/create_chat_session",
                    json={"email": "test@test.com", "business_idea": "AI SaaS"},
                )

        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == session_id
        mock_lpush.assert_called_once_with(
            "jobs:queue",
            json.dumps({"session_id": session_id, "user_input": "AI SaaS"}),
        )

    @pytest.mark.asyncio
    async def test_returns_404_when_user_not_found(self, client):
        with patch("backend.main.get_user", new_callable=AsyncMock, return_value=None):
            async with client as c:
                response = await c.post(
                    "/create_chat_session",
                    json={"email": "unknown@test.com", "business_idea": "AI SaaS"},
                )

        assert response.status_code == 404
        assert response.json() == {"message": "user not found with given email"}

    @pytest.mark.asyncio
    async def test_returns_422_for_missing_business_idea(self, client):
        async with client as c:
            response = await c.post("/create_chat_session", json={"email": "test@test.com"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_email(self, client):
        async with client as c:
            response = await c.post(
                "/create_chat_session",
                json={"email": "not-an-email", "business_idea": "AI SaaS"},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_empty_email(self, client):
        async with client as c:
            response = await c.post(
                "/create_chat_session",
                json={"email": "", "business_idea": "AI SaaS"},
            )
        assert response.status_code == 422


# ── WebSocket Stream ─────────────────────────────────────────────────────────

class TestWebSocketStream:
    @staticmethod
    def _build_pubsub_mock(raw_messages: list[str]):
        async def _listen():
            for raw in raw_messages:
                yield {"type": "message", "data": raw, "channel": "stream:test-session"}

        pubsub = MagicMock()
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.close = AsyncMock()
        pubsub.listen = _listen
        return pubsub

    def test_receives_single_message_then_ends(self):
        messages = [
            json.dumps({"type": "token", "content": "Hello"}),
            json.dumps({"type": "end"}),
        ]

        pubsub = self._build_pubsub_mock(messages)

        with patch("backend.main.redis.pubsub", return_value=pubsub):
            with TestClient(app) as client:
                with client.websocket_connect("/ws/session/test-session") as ws:
                    assert ws.receive_json() == {"type": "token", "content": "Hello"}
                    assert ws.receive_json() == {"type": "end"}

    def test_receives_multiple_messages_then_ends(self):
        messages = [
            json.dumps({"type": "token", "content": "Step 1"}),
            json.dumps({"type": "token", "content": "Step 2"}),
            json.dumps({"type": "end"}),
        ]

        pubsub = self._build_pubsub_mock(messages)

        with patch("backend.main.redis.pubsub", return_value=pubsub):
            with TestClient(app) as client:
                with client.websocket_connect("/ws/session/test-session") as ws:
                    assert ws.receive_json() == {"type": "token", "content": "Step 1"}
                    assert ws.receive_json() == {"type": "token", "content": "Step 2"}
                    assert ws.receive_json() == {"type": "end"}

    def test_websocket_accepts_connection(self):
        async def _listen():
            yield {"type": "message", "data": json.dumps({"type": "end"}), "channel": "stream:test-session"}

        pubsub = MagicMock()
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.close = AsyncMock()
        pubsub.listen = _listen

        with patch("backend.main.redis.pubsub", return_value=pubsub):
            with TestClient(app) as client:
                with client.websocket_connect("/ws/session/test-session") as ws:
                    assert ws.receive_json() == {"type": "end"}

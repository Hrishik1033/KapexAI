import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
async def lifespan_events():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.get("/health")
    yield


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_ok(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWaitlistEndpoint:
    @pytest.mark.asyncio
    async def test_join_waitlist_with_email_only(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post("/waitlist", json={"email": "test@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully joined the waitlist!"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_join_waitlist_with_email_and_name(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post(
                "/waitlist", json={"email": "test@example.com", "name": "John Doe"}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully joined the waitlist!"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_join_waitlist_invalid_email(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post("/waitlist", json={"email": "not-an-email"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_join_waitlist_missing_email(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post("/waitlist", json={"name": "John Doe"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_join_waitlist_empty_email(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post("/waitlist", json={"email": ""})
        assert response.status_code == 422


class TestCORSMiddleware:
    @pytest.mark.asyncio
    async def test_cors_allows_localhost_3000(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
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
    async def test_cors_allows_credentials(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_allows_all_methods(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
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
    async def test_cors_allows_all_headers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
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
    async def test_cors_blocks_other_origins(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.options(
                "/waitlist",
                headers={
                    "Origin": "http://evil.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"
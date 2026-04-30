import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from biblioteca_virtual.core.db import Base, get_session
from biblioteca_virtual.core.config import get_settings
from biblioteca_virtual.main import app


@pytest.fixture
async def test_app():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    # Disable redis/rate limiting for tests to avoid external dependencies
    settings = get_settings()
    def override_get_settings():
        from biblioteca_virtual.core.config import Settings
        # Copy current settings but disable redis
        return Settings(
            **{**settings.model_dump(), "redis_enabled": False, "rate_limit_enabled": False}
        )

    app.dependency_overrides[get_settings] = override_get_settings

    with patch("biblioteca_virtual.core.middleware.get_engine_no_cache", return_value=engine):
        yield app

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_full_api_flow(client: AsyncClient):
    # 1. User Creation (Public Route)
    user_data = {
        "full_name": "API Tester",
        "email": "api@tester.com",
        "password": "Password123!"
    }
    res = await client.post("/api/v1/users", json=user_data)
    assert res.status_code == 201
    user_id = res.json()["id"]

    # 2. Login
    auth_res = await client.post(
        "/api/v1/auth/token",
        data={"username": "api@tester.com", "password": "Password123!"}
    )
    assert auth_res.status_code == 200
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. List Users with Token (Pagination)
    res_users = await client.get("/api/v1/users?limit=10&offset=0", headers=headers)
    assert res_users.status_code == 200
    assert "items" in res_users.json()
    assert res_users.json()["total"] == 1

    # 4. Create Book
    book_data = {
        "title": "Clean Architecture",
        "isbn": "9780134494166",
        "author_name": "Robert C. Martin",
        "total_copies": 2
    }
    res_book = await client.post("/api/v1/books", json=book_data, headers=headers)
    assert res_book.status_code == 201
    book_id = res_book.json()["id"]

    # 5. List Books (Pagination)
    res_books = await client.get("/api/v1/books", headers=headers)
    assert res_books.status_code == 200
    assert res_books.json()["total"] == 1

    # 6. Create Loan
    loan_data = {
        "user_id": user_id,
        "book_id": book_id
    }
    res_loan = await client.post("/api/v1/loans", json=loan_data, headers=headers)
    assert res_loan.status_code == 201
    loan_id = res_loan.json()["id"]

    # 7. List Active Loans
    res_active = await client.get("/api/v1/loans/active", headers=headers)
    assert res_active.status_code == 200
    assert res_active.json()["total"] == 1

    # 8. Check Availability
    res_avail = await client.get(f"/api/v1/books/{book_id}/availability", headers=headers)
    assert res_avail.status_code == 200
    assert res_avail.json()["available_copies"] == 1

    # 9. Return Loan
    res_return = await client.post(f"/api/v1/loans/{loan_id}/return", headers=headers)
    assert res_return.status_code == 200
    assert res_return.json()["status"] == "RETURNED"

    # 10. Verify Unauthorized Without Token
    res_unauth = await client.get("/api/v1/users")
    assert res_unauth.status_code == 401

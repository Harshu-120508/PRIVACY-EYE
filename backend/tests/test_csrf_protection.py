"""
Unit and integration tests for Double-Submit Cookie CSRF protection (Phase 3).
Validates OWASP Double-Submit Cookie compliance:
- Safe methods (GET/HEAD/OPTIONS) exempt from CSRF validation
- State-changing methods (POST/PUT/PATCH/DELETE) requiring valid matching token when cookie auth is present
- Missing X-CSRF-Token header returns 403
- Tampered or mismatched X-CSRF-Token returns 403
- Valid Double-Submit token returns 2xx
- Pure Bearer token requests without cookies are exempt
- Token rotation on login and deletion on logout
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.core.config import settings
from app.core.csrf import generate_csrf_token, validate_csrf_token, set_csrf_cookie, clear_csrf_cookie


@pytest.fixture(scope="module")
async def csrf_test_client():
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


def test_csrf_token_cryptographic_verification():
    """Verify HMAC-SHA256 signature generation and validation."""
    token = generate_csrf_token()
    assert "." in token
    parts = token.split(".")
    assert len(parts) == 2

    # Matching token validates
    assert validate_csrf_token(token, token) is True

    # Tampered signature fails
    tampered_sig = parts[0] + "." + "0" * 64
    assert validate_csrf_token(tampered_sig, tampered_sig) is False

    # Mismatch between cookie and header fails
    different_token = generate_csrf_token()
    assert validate_csrf_token(token, different_token) is False

    # Session-bound token validation
    sess_token = generate_csrf_token(session_id="session-xyz-123")
    assert validate_csrf_token(sess_token, sess_token, session_id="session-xyz-123") is True
    # Still valid under unbound fallback
    assert validate_csrf_token(token, token, session_id="session-xyz-123") is True


@pytest.mark.anyio
async def test_get_requests_exempt_and_seed_csrf_cookie(csrf_test_client: AsyncClient):
    """Safe methods (GET) are exempt from CSRF checks and receive a csrf_token cookie."""
    res = await csrf_test_client.get("/health")
    assert res.status_code == 200
    assert "csrf_token" in res.cookies
    token = res.cookies["csrf_token"]
    assert "." in token


@pytest.mark.anyio
async def test_cookie_auth_post_without_csrf_header_returns_403(csrf_test_client: AsyncClient):
    """A state-changing request with cookie auth but NO X-CSRF-Token header returns 403."""
    # First register user to get valid token
    reg = await csrf_test_client.post("/api/v1/auth/register", json={
        "email": "csrf.victim@example.com",
        "password": "SecurePassword123!",
        "full_name": "CSRF Victim",
    })
    assert reg.status_code == 201
    access_token = reg.json()["tokens"]["access_token"]
    csrf_token = reg.cookies.get("csrf_token") or generate_csrf_token()

    # Simulate cross-site POST where browser sends access_token cookie, but no CSRF header
    post_res = await csrf_test_client.patch(
        "/api/v1/users/me?full_name=HackedName",
        cookies={"access_token": access_token, "csrf_token": csrf_token},
    )
    assert post_res.status_code == 403
    assert "CSRF token missing or invalid" in post_res.json()["detail"]


@pytest.mark.anyio
async def test_cookie_auth_post_with_wrong_csrf_header_returns_403(csrf_test_client: AsyncClient):
    """A state-changing request with mismatched/forged X-CSRF-Token header returns 403."""
    reg = await csrf_test_client.post("/api/v1/auth/register", json={
        "email": "csrf.victim2@example.com",
        "password": "SecurePassword123!",
        "full_name": "CSRF Victim 2",
    })
    assert reg.status_code == 201
    access_token = reg.json()["tokens"]["access_token"]
    valid_csrf_token = reg.cookies.get("csrf_token") or generate_csrf_token()

    post_res = await csrf_test_client.patch(
        "/api/v1/users/me?full_name=HackedName",
        cookies={"access_token": access_token, "csrf_token": valid_csrf_token},
        headers={"X-CSRF-Token": "forged_malicious_token"},
    )
    assert post_res.status_code == 403
    assert "CSRF token missing or invalid" in post_res.json()["detail"]


@pytest.mark.anyio
async def test_cookie_auth_post_with_valid_csrf_token_succeeds(csrf_test_client: AsyncClient):
    """A state-changing request with valid Double-Submit CSRF cookie and matching header succeeds (2xx)."""
    reg = await csrf_test_client.post("/api/v1/auth/register", json={
        "email": "csrf.legit@example.com",
        "password": "SecurePassword123!",
        "full_name": "Legit User",
    })
    assert reg.status_code == 201
    access_token = reg.json()["tokens"]["access_token"]
    csrf_token = reg.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = generate_csrf_token()

    # Valid double-submit: cookie matches header
    patch_res = await csrf_test_client.patch(
        "/api/v1/users/me?full_name=LegitNameUpdated",
        cookies={"access_token": access_token, "csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "LegitNameUpdated"


@pytest.mark.anyio
async def test_pure_bearer_token_exempt_from_csrf(csrf_test_client: AsyncClient):
    """Programmatic API clients sending Bearer auth with NO cookies are exempt from CSRF."""
    reg = await csrf_test_client.post("/api/v1/auth/register", json={
        "email": "csrf.api@example.com",
        "password": "SecurePassword123!",
        "full_name": "API Client",
    })
    assert reg.status_code == 201
    access_token = reg.json()["tokens"]["access_token"]

    # Clear cookie jar to simulate an external programmatic client sending zero cookies
    csrf_test_client.cookies.clear()

    # Request without cookies, using solely Authorization: Bearer
    patch_res = await csrf_test_client.patch(
        "/api/v1/users/me?full_name=ApiClientUpdated",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "ApiClientUpdated"


@pytest.mark.anyio
async def test_token_rotation_on_login_and_clear_on_logout(csrf_test_client: AsyncClient):
    """CSRF token rotates on authentication and is cleared on logout."""
    reg_payload = {
        "email": "rotation.user@example.com",
        "password": "SecurePassword123!",
        "full_name": "Rotation User",
    }
    reg = await csrf_test_client.post("/api/v1/auth/register", json=reg_payload)
    token_1 = reg.cookies.get("csrf_token")
    assert token_1 is not None

    # Login should rotate CSRF token
    login_res = await csrf_test_client.post("/api/v1/auth/login", json={
        "email": "rotation.user@example.com",
        "password": "SecurePassword123!",
    })
    assert login_res.status_code == 200
    token_2 = login_res.cookies.get("csrf_token")
    assert token_2 is not None
    assert token_1 != token_2

    # Logout should clear cookies
    access_tok = login_res.json()["tokens"]["access_token"]
    logout_res = await csrf_test_client.post(
        "/api/v1/auth/logout",
        cookies={"access_token": access_tok, "csrf_token": token_2},
        headers={"X-CSRF-Token": token_2},
    )
    assert logout_res.status_code == 200
    # In Set-Cookie header, csrf_token is deleted / max-age=0
    deleted_cookie_headers = [h for h in logout_res.headers.get_list("set-cookie") if "csrf_token" in h]
    assert len(deleted_cookie_headers) > 0
    assert any("max-age=0" in h.lower() or "expires=" in h.lower() for h in deleted_cookie_headers)

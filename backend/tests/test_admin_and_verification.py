"""
Privacy Eye — Admin Operations & Email Verification Test Suite
Tests:
- Email verification link generation & token validation flow
- Role-based access control (RBAC): Regular USER denied from admin endpoints (403)
- Admin telemetry stats (users, scans, active sessions, risk distributions)
- Admin user directory management (search, filter, pagination)
- Admin user activation and suspension with session revocation
- Protection against administrator self-suspension
- Admin user role change (USER -> ADMIN / ENTERPRISE)
- Protection against administrator self-demotion
- Global scans audit feed
- Immutable security audit logs stream
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def admin_test_client():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)

    async with test_engine.begin() as conn:
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
        yield client, async_session

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.mark.anyio
async def test_email_verification_lifecycle(admin_test_client):
    """Test full email verification token generation, cryptographic validation, and user activation."""
    client, _ = admin_test_client

    # 1. Register unverified user
    reg = await client.post("/api/v1/auth/register", json={
        "email": "unverified@example.com",
        "password": "Password123!",
        "full_name": "Unverified User",
    })
    assert reg.status_code == 201
    user_data = reg.json()["user"]
    assert user_data["is_verified"] is False
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Request verification token
    req_res = await client.post("/api/v1/auth/request-verification", headers=headers)
    assert req_res.status_code == 200
    v_token = req_res.json().get("verification_token")
    assert v_token is not None

    # 3. Verify email with token
    verify_res = await client.post("/api/v1/auth/verify-email", json={"token": v_token})
    assert verify_res.status_code == 200
    assert verify_res.json()["success"] is True
    assert verify_res.json()["user"]["is_verified"] is True

    # 4. Check profile reflects verified status
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["is_verified"] is True


@pytest.mark.anyio
async def test_admin_access_control_and_management(admin_test_client):
    """Test RBAC enforcement, telemetry stats, user directory, status toggling, and audit feeds."""
    client, session_maker = admin_test_client

    # 1. Register standard User
    user_reg = await client.post("/api/v1/auth/register", json={
        "email": "regular_user@example.com",
        "password": "Password123!",
        "full_name": "Regular User",
    })
    user_token = user_reg.json()["tokens"]["access_token"]
    user_id = user_reg.json()["user"]["id"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 2. Register Admin User
    admin_reg = await client.post("/api/v1/auth/register", json={
        "email": "system_admin@example.com",
        "password": "Password123!",
        "full_name": "System Admin",
    })
    admin_token = admin_reg.json()["tokens"]["access_token"]
    admin_id = admin_reg.json()["user"]["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Elevate admin user in DB to UserRole.ADMIN
    async with session_maker() as db:
        admin_obj = (await db.execute(select(User).where(User.id == admin_id))).scalar_one()
        admin_obj.role = UserRole.ADMIN
        await db.commit()

    # 3. Standard user attempts to access admin stats -> 403 Forbidden
    forbidden_res = await client.get("/api/v1/admin/stats", headers=user_headers)
    assert forbidden_res.status_code == 403
    assert "Administrative privileges required" in forbidden_res.json()["detail"]

    # 4. Admin accesses admin stats -> 200 OK
    stats_res = await client.get("/api/v1/admin/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_users"] >= 2
    assert stats["active_users"] >= 2
    assert "scans_by_risk" in stats
    assert "system_status" in stats
    assert stats["system_status"]["database"] == "connected"

    # 5. Admin lists users directory
    users_res = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    users_data = users_res.json()
    assert users_data["total"] >= 2
    assert any(u["id"] == user_id for u in users_data["items"])

    # 6. Admin suspends regular user
    suspend_res = await client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["is_active"] is False

    # Suspended user cannot access authenticated profile
    profile_attempt = await client.get("/api/v1/auth/me", headers=user_headers)
    assert profile_attempt.status_code in [401, 403]

    # 7. Admin reactivates regular user
    reactivate_res = await client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True

    # 8. Protection: Admin cannot suspend self
    self_suspend_res = await client.patch(
        f"/api/v1/admin/users/{admin_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert self_suspend_res.status_code == 400
    assert "cannot suspend their own account" in self_suspend_res.json()["detail"]

    # 9. Admin changes user role to ENTERPRISE
    role_res = await client.patch(
        f"/api/v1/admin/users/{user_id}/role",
        json={"role": "ENTERPRISE"},
        headers=admin_headers,
    )
    assert role_res.status_code == 200
    assert role_res.json()["role"] == "ENTERPRISE"

    # 10. Protection: Admin cannot demote self
    self_demote_res = await client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "USER"},
        headers=admin_headers,
    )
    assert self_demote_res.status_code == 400
    assert "cannot demote themselves" in self_demote_res.json()["detail"]

    # 11. Admin inspects global scans feed
    scans_res = await client.get("/api/v1/admin/scans", headers=admin_headers)
    assert scans_res.status_code == 200
    assert "items" in scans_res.json()

    # 12. Admin inspects security audit logs
    audit_res = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()["items"]
    assert len(audit_logs) > 0
    actions = [log["action"] for log in audit_logs]
    assert "ADMIN_USER_STATUS_CHANGE" in actions or "ADMIN_USER_ROLE_CHANGE" in actions

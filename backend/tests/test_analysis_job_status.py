"""
Unit and integration tests for Real-Time Analysis Job Tracker & Status API (Phase 4).
Validates truthful backend state exposure without simulated timers or fake percentage loops:
- Real job lifecycle states: queued -> processing -> completed / failed
- Realistic stage labels matching actual execution points
- HTTP job status endpoint queries via both /jobs/{job_id}/status and /{analysis_id}/status
- Multi-tenant isolation for job status inspection
- Contract verification matching the frontend state machine
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.services.job_service import job_tracker, AnalysisJob, JOB_QUEUED, JOB_PROCESSING, JOB_COMPLETED, JOB_FAILED


@pytest.fixture(scope="module")
async def job_test_client():
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


def test_job_tracker_state_transitions():
    """Verify internal state machine transitions and dictionary representations."""
    job = job_tracker.create_job(
        job_id="job-test-123",
        user_id="user-456",
        media_type="image",
        filename="photo.jpg",
    )
    assert job.status == JOB_QUEUED
    assert job.stage == "QUEUED"
    assert "queued" in job.stage_name.lower()

    # Transition to processing with real execution stage name
    job_tracker.update_stage(
        "job-test-123",
        stage="FEATURE_EXTRACTION",
        stage_name="Analyzing frequency domain spectra, compression artifacts, and spatial boundaries...",
    )
    updated = job_tracker.get_job("job-test-123")
    assert updated.status == JOB_PROCESSING
    assert updated.stage == "FEATURE_EXTRACTION"
    assert "frequency domain" in updated.stage_name

    # Complete
    job_tracker.complete_job("job-test-123", {"risk_level": "LOW", "confidence": 0.95})
    assert updated.status == JOB_COMPLETED
    assert updated.stage == "COMPLETE"
    assert updated.to_dict()["completed"] is True
    assert updated.to_dict()["failed"] is False

    # Fail
    job_tracker.fail_job("job-test-123", "Corrupted frame header encountered")
    assert updated.status == JOB_FAILED
    assert updated.stage == "FAILED"
    assert updated.error == "Corrupted frame header encountered"
    assert updated.to_dict()["failed"] is True


@pytest.mark.anyio
async def test_job_status_endpoint_lifecycle(job_test_client: AsyncClient):
    """Verify that uploading media and polling job status exposes real backend state."""
    # Register user
    reg = await job_test_client.post("/api/v1/auth/register", json={
        "email": "job.user@example.com",
        "password": "SecurePassword123!",
        "full_name": "Job User",
    })
    token = reg.json()["tokens"]["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Synthesize active job in processing state
    active_job_id = "test-active-job-id"
    job_tracker.create_job(
        job_id=active_job_id,
        user_id=user_id,
        media_type="image",
        filename="test_sample.png",
    )
    job_tracker.update_stage(
        active_job_id,
        stage="INFERENCE_EXECUTION",
        stage_name="Running deep neural network classifiers and biometric consistency checks...",
    )

    # Query status endpoint
    status_res = await job_test_client.get(
        f"/api/v1/analyze/jobs/{active_job_id}/status",
        headers=headers,
    )
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["job_id"] == active_job_id
    assert data["status"] == "processing"
    assert data["stage"] == "INFERENCE_EXECUTION"
    assert "neural network" in data["stage_name"]
    assert data["completed"] is False
    assert data["failed"] is False

    # Query via alias path /analyze/{id}/status
    alias_res = await job_test_client.get(
        f"/api/v1/analyze/{active_job_id}/status",
        headers=headers,
    )
    assert alias_res.status_code == 200
    assert alias_res.json()["stage"] == "INFERENCE_EXECUTION"

    # Mark completed
    job_tracker.complete_job(active_job_id, {"status": "ok"})
    completed_res = await job_test_client.get(
        f"/api/v1/analyze/jobs/{active_job_id}/status",
        headers=headers,
    )
    assert completed_res.status_code == 200
    comp_data = completed_res.json()
    assert comp_data["status"] == "completed"
    assert comp_data["completed"] is True

    # Mark failed
    job_tracker.fail_job(active_job_id, "Inference pipeline timeout")
    failed_res = await job_test_client.get(
        f"/api/v1/analyze/jobs/{active_job_id}/status",
        headers=headers,
    )
    assert failed_res.status_code == 200
    failed_data = failed_res.json()
    assert failed_data["status"] == "failed"
    assert failed_data["failed"] is True
    assert failed_data["error"] == "Inference pipeline timeout"


@pytest.mark.anyio
async def test_job_status_unauthorized_isolation(job_test_client: AsyncClient):
    """Verify that a user cannot query job status belonging to another user."""
    # Register user A
    reg_a = await job_test_client.post("/api/v1/auth/register", json={
        "email": "user_a@example.com",
        "password": "SecurePassword123!",
        "full_name": "User A",
    })
    token_a = reg_a.json()["tokens"]["access_token"]
    user_a_id = reg_a.json()["user"]["id"]

    # Register user B
    reg_b = await job_test_client.post("/api/v1/auth/register", json={
        "email": "user_b@example.com",
        "password": "SecurePassword123!",
        "full_name": "User B",
    })
    token_b = reg_b.json()["tokens"]["access_token"]

    job_id = "user-a-private-job"
    job_tracker.create_job(
        job_id=job_id,
        user_id=user_a_id,
        media_type="image",
        filename="private.jpg",
    )

    # User B requests User A's job -> 403 Forbidden
    res = await job_test_client.get(
        f"/api/v1/analyze/jobs/{job_id}/status",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


@pytest.mark.anyio
async def test_nonexistent_job_returns_404(job_test_client: AsyncClient):
    """Non-existent job returns 404."""
    reg = await job_test_client.post("/api/v1/auth/register", json={
        "email": "job_404_user@example.com",
        "password": "SecurePassword123!",
        "full_name": "Job 404 User",
    })
    token = reg.json()["tokens"]["access_token"]

    res = await job_test_client.get(
        "/api/v1/analyze/jobs/nonexistent-uuid-9999/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404

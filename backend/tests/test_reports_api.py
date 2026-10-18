"""
Privacy Eye — Evidence Reports Engine Test Suite
Tests:
- Generation of AI evidence report for completed analysis (201 Created)
- Idempotent report generation (returns existing report without duplicate creation)
- Validation gates: 400 Bad Request for pending/incomplete analysis, 404 for non-existent analysis
- Report retrieval via GET /api/v1/reports/{analysis_id}
- Cryptographic JSON report export with SHA-256 fingerprint, model specs, and signal scores
- Print-ready HTML Forensic Certificate export with security seal, media provenance, and disclaimers
- Cross-user tenant isolation: User B cannot generate, retrieve, or download User A's reports (404 Not Found)
"""
import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, UserRole, MediaAnalysis, MediaType, AnalysisStatus, RiskLevel, AnalysisSignal
from app.core.security import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def reports_test_client():
    test_engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
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
async def test_generate_and_retrieve_report(reports_test_client):
    client, async_session = reports_test_client

    async with async_session() as session:
        user_a = User(
            id=str(uuid.uuid4()),
            email="report_a@example.com",
            hashed_password=hash_password("ReportPass123!"),
            full_name="Report User A",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            scans_limit=50,
            scans_used_this_month=0,
        )
        session.add(user_a)

        analysis_id = str(uuid.uuid4())
        analysis = MediaAnalysis(
            id=analysis_id,
            user_id=user_a.id,
            original_filename="tampered_face_test.jpg",
            media_type=MediaType.IMAGE,
            status=AnalysisStatus.COMPLETE,
            risk_level=RiskLevel.HIGH,
            synthetic_probability=0.88,
            confidence=0.92,
            file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=1048576,
            mime_type="image/jpeg",
            explanation="Detected localized synthetic boundary artifacts and high-frequency noise suppression.",
            created_at=datetime.now(timezone.utc),
        )
        session.add(analysis)

        sig = AnalysisSignal(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            signal_key="FREQUENCY_ANOMALY",
            signal_label="Spectral Frequency Grid Peak",
            severity="high",
            score=0.87,
            description="Non-organic frequency distribution in facial perimeter.",
        )
        session.add(sig)
        await session.commit()

    token_a = create_access_token(user_a.id, role=user_a.role.value)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Report does not exist before generation
    res_get_init = await client.get(f"/api/v1/reports/{analysis_id}", headers=headers_a)
    assert res_get_init.status_code == 404

    # 2. Generate report
    res_gen = await client.post(f"/api/v1/reports/{analysis_id}/generate", headers=headers_a)
    assert res_gen.status_code == 201
    data = res_gen.json()
    assert data["analysis_id"] == analysis_id
    assert "tampered_face_test.jpg" in data["title"]
    assert data["summary"]

    assert data["recommendations"]
    assert data["report_json"]["file"]["sha256"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # 3. Retrieve report via GET
    res_get = await client.get(f"/api/v1/reports/{analysis_id}", headers=headers_a)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == data["id"]

    # 4. Generating again returns the existing report (idempotent)
    res_gen_repeat = await client.post(f"/api/v1/reports/{analysis_id}/generate", headers=headers_a)
    assert res_gen_repeat.status_code in (200, 201)
    assert res_gen_repeat.json()["id"] == data["id"]


@pytest.mark.anyio
async def test_report_download_json_and_html(reports_test_client):
    client, async_session = reports_test_client

    async with async_session() as session:
        user = User(
            id=str(uuid.uuid4()),
            email="export_tester@example.com",
            hashed_password=hash_password("ExportPass123!"),
            full_name="Export User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            scans_limit=50,
            scans_used_this_month=0,
        )
        session.add(user)

        analysis_id = str(uuid.uuid4())
        sha256_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        analysis = MediaAnalysis(
            id=analysis_id,
            user_id=user.id,
            original_filename="forensic_sample.png",
            media_type=MediaType.IMAGE,
            status=AnalysisStatus.COMPLETE,
            risk_level=RiskLevel.HIGH,
            synthetic_probability=0.91,
            confidence=0.94,
            file_sha256=sha256_hash,
            file_size_bytes=204800,
            mime_type="image/png",
            explanation="Uncalibrated color temperature and unnatural eye reflections detected.",
            created_at=datetime.now(timezone.utc),
        )
        session.add(analysis)

        sig = AnalysisSignal(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            signal_key="COLOR_DISCREPANCY",
            signal_label="Chromatic Boundary Discontinuity",
            severity="medium",
            score=0.74,
            description="Color gradients mismatch background ambient illumination.",
        )
        session.add(sig)
        await session.commit()

    token = create_access_token(user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}


    # Generate report
    gen_res = await client.post(f"/api/v1/reports/{analysis_id}/generate", headers=headers)
    assert gen_res.status_code == 201

    # 1. Download JSON report
    res_json = await client.get(f"/api/v1/reports/{analysis_id}/download/json", headers=headers)
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    parsed = res_json.json()
    assert parsed["file"]["sha256"] == sha256_hash
    assert parsed["assessment"]["risk_level"] == "HIGH"
    assert parsed["model"]["name"] == "PrivacyEye-Ensemble-v1"

    # 2. Download HTML Forensic Certificate
    res_html = await client.get(f"/api/v1/reports/{analysis_id}/download/html", headers=headers)
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    body = res_html.text
    assert "PRIVACY EYE" in body
    assert "Forensic Authenticity Certificate" in body
    assert sha256_hash in body
    assert "Chromatic Boundary Discontinuity" in body
    assert "SECURE VERIFIED RECORD" in body


@pytest.mark.anyio
async def test_report_validation_and_access_control(reports_test_client):
    client, async_session = reports_test_client

    async with async_session() as session:
        user_a = User(
            id=str(uuid.uuid4()),
            email="owner@example.com",
            hashed_password=hash_password("OwnerPass123!"),
            full_name="Owner User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )
        user_b = User(
            id=str(uuid.uuid4()),
            email="intruder@example.com",
            hashed_password=hash_password("IntruderPass123!"),
            full_name="Intruder User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )
        session.add_all([user_a, user_b])

        # Complete analysis for user A
        complete_a = MediaAnalysis(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            original_filename="private_doc.jpg",
            media_type=MediaType.IMAGE,
            file_size_bytes=2048,
            file_sha256="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            status=AnalysisStatus.COMPLETE,
            risk_level=RiskLevel.LOW,
            synthetic_probability=0.08,
            confidence=0.96,
        )
        # Pending analysis for user A
        pending_a = MediaAnalysis(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            original_filename="in_progress.jpg",
            media_type=MediaType.IMAGE,
            file_size_bytes=1024,
            file_sha256="9999222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            status=AnalysisStatus.PROCESSING,
        )
        session.add_all([complete_a, pending_a])
        await session.commit()


    token_a = create_access_token(user_a.id, role=user_a.role.value)
    token_b = create_access_token(user_b.id, role=user_b.role.value)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}


    # 1. Incomplete analysis rejected with 400
    res_pending = await client.post(f"/api/v1/reports/{pending_a.id}/generate", headers=headers_a)
    assert res_pending.status_code == 400
    assert "not yet complete" in res_pending.json()["detail"].lower()

    # 2. Non-existent analysis rejected with 404
    res_fake = await client.post("/api/v1/reports/00000000-0000-0000-0000-000000000000/generate", headers=headers_a)
    assert res_fake.status_code == 404

    # 3. Generate report for complete_a
    res_gen = await client.post(f"/api/v1/reports/{complete_a.id}/generate", headers=headers_a)
    assert res_gen.status_code == 201

    # 4. User B cannot generate User A's report (404)
    res_b_gen = await client.post(f"/api/v1/reports/{complete_a.id}/generate", headers=headers_b)
    assert res_b_gen.status_code == 404

    # 5. User B cannot get User A's report (404)
    res_b_get = await client.get(f"/api/v1/reports/{complete_a.id}", headers=headers_b)
    assert res_b_get.status_code == 404

    # 6. User B cannot download User A's JSON report (404)
    res_b_json = await client.get(f"/api/v1/reports/{complete_a.id}/download/json", headers=headers_b)
    assert res_b_json.status_code == 404

    # 7. User B cannot download User A's HTML certificate (404)
    res_b_html = await client.get(f"/api/v1/reports/{complete_a.id}/download/html", headers=headers_b)
    assert res_b_html.status_code == 404

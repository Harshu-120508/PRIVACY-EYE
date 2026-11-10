"""
Privacy Eye — Test Suite for Dataset REST API Endpoints
Asynchronous pytest suite with AsyncClient.
"""

import base64
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import get_current_user, require_admin
from app.database.models import User, UserRole
from app.database.session import engine

mock_admin = User(
    id="admin-test-uuid",
    email="admin@privacyeye.test",
    role=UserRole.ADMIN,
    is_active=True,
    is_verified=True,
)


@pytest.fixture(autouse=True)
async def setup_auth_overrides():
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[require_admin] = lambda: mock_admin
    yield
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_quality_gate_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a small valid test image in base64
        img = np.full((150, 150, 3), 120, dtype=np.uint8)
        cv2.circle(img, (75, 75), 40, (220, 220, 220), -1)
        cv2.rectangle(img, (20, 20), (130, 130), (50, 50, 200), 2)
        _, buffer = cv2.imencode(".jpg", img)
        b64_str = base64.b64encode(buffer).decode("utf-8")

        response = await client.post(
            "/api/v1/dataset/quality-gate",
            json={"image_base64": b64_str},
        )
        assert response.status_code == 200
        data = response.json()
        assert "passed" in data
        assert "overall_quality_score" in data
        assert "quality_label" in data
        assert "rejection_reasons" in data


@pytest.mark.anyio
async def test_dataset_record_create_and_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sample_id = f"test_sample_cat_a_{np.random.randint(10000, 99999)}"
        payload = {
            "sample_id": sample_id,
            "category": "CATEGORY_A_GENUINE",
            "source_dataset": "InternalConsent",
            "license_terms": "InternalConsent-v1",
            "subject_id": "subj_999",
            "true_label": "real",
            "split": "train",
            "consent_verified": True,
        }
        res = await client.post("/api/v1/dataset/records", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["sample_id"] == sample_id

        # Query stats
        stats_res = await client.get("/api/v1/dataset/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_samples"] >= 1
        assert "CATEGORY_A_GENUINE" in stats["category_counts"]


@pytest.mark.anyio
async def test_failure_case_logging_and_review():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "model_version": "v2.0",
            "input_type": "image",
            "device": "mac_hd",
            "resolution": "720p",
            "environment": "office",
            "true_label": "real",
            "prediction": "POSSIBLE REPLAY",
            "confidence": 0.82,
            "reason": "Screen reflection in glasses mistaken for display replay",
        }
        res = await client.post("/api/v1/dataset/failure-cases", json=payload)
        assert res.status_code == 201
        data = res.json()
        failure_id = data["failure_id"]

        # Human Review endpoint
        rev_res = await client.post(
            f"/api/v1/dataset/failure-cases/{failure_id}/review?approve_for_retraining=true"
        )
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert rev_data["is_verified_by_human"] is True
        assert rev_data["reviewed_by"] == mock_admin.id
        assert rev_data["added_to_training_set"] is True

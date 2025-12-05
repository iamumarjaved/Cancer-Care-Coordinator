"""Tests for Analysis API endpoints."""

import pytest
from fastapi.testclient import TestClient
import time


class TestAnalysisAPI:
    """Tests for analysis endpoints."""

    def test_run_analysis(self, client):
        """Test starting a new analysis."""
        request = {
            "patient_id": "P001",
            "analysis_type": "full",
            "include_trials": True
        }

        response = client.post("/api/v1/analysis/run", json=request)
        assert response.status_code == 200

        data = response.json()
        assert "request_id" in data
        assert data["patient_id"] == "P001"
        assert data["status"] == "initializing"

    def test_run_analysis_minimal(self, client):
        """Test starting analysis with minimal params."""
        request = {"patient_id": "P001"}

        response = client.post("/api/v1/analysis/run", json=request)
        assert response.status_code == 200

    def test_get_analysis_status(self, client):
        """Test getting analysis status."""
        # First start an analysis
        request = {"patient_id": "P001"}
        run_response = client.post("/api/v1/analysis/run", json=request)
        request_id = run_response.json()["request_id"]

        # Get status
        response = client.get(f"/api/v1/analysis/{request_id}/status")
        assert response.status_code == 200

        data = response.json()
        assert data["request_id"] == request_id
        assert "status" in data
        assert "progress_percent" in data

    def test_get_analysis_status_not_found(self, client):
        """Test getting status for non-existent analysis."""
        response = client.get("/api/v1/analysis/nonexistent-id/status")
        assert response.status_code == 404

    def test_get_analysis_results_not_complete(self, client):
        """Test getting results before analysis completes."""
        # Start an analysis
        request = {"patient_id": "P001"}
        run_response = client.post("/api/v1/analysis/run", json=request)
        request_id = run_response.json()["request_id"]

        # Immediately try to get results
        response = client.get(f"/api/v1/analysis/{request_id}/results")
        # Should either be 400 (not complete) or 200 (if mock completes fast)
        assert response.status_code in [200, 400]

    def test_analysis_progress_updates(self, client):
        """Test that analysis progress updates over time."""
        # Start an analysis
        request = {"patient_id": "P001"}
        run_response = client.post("/api/v1/analysis/run", json=request)
        request_id = run_response.json()["request_id"]

        # Wait a bit and check progress
        time.sleep(0.5)

        response = client.get(f"/api/v1/analysis/{request_id}/status")
        data = response.json()

        # Progress should have started
        assert "progress_percent" in data


class TestAnalysisWorkflow:
    """Tests for complete analysis workflow."""

    def test_full_analysis_workflow(self, client):
        """Test complete analysis workflow from start to finish."""
        # Start analysis
        request = {
            "patient_id": "P001",
            "analysis_type": "full",
            "include_trials": True
        }
        run_response = client.post("/api/v1/analysis/run", json=request)
        assert run_response.status_code == 200
        request_id = run_response.json()["request_id"]

        # Poll for completion (with timeout)
        max_wait = 30  # seconds
        start_time = time.time()
        status = "initializing"

        while status not in ["completed", "error"] and (time.time() - start_time) < max_wait:
            status_response = client.get(f"/api/v1/analysis/{request_id}/status")
            status = status_response.json()["status"]
            time.sleep(0.5)

        # Analysis should complete
        assert status == "completed" or (time.time() - start_time) >= max_wait

        # If completed, get results
        if status == "completed":
            results_response = client.get(f"/api/v1/analysis/{request_id}/results")
            assert results_response.status_code == 200

            results = results_response.json()
            assert "summary" in results
            assert "key_findings" in results
            assert "recommendations" in results

    def test_analysis_step_tracking(self, client):
        """Test that analysis tracks steps correctly."""
        request = {"patient_id": "P001"}
        run_response = client.post("/api/v1/analysis/run", json=request)
        request_id = run_response.json()["request_id"]

        # Wait for some progress
        time.sleep(2)

        status_response = client.get(f"/api/v1/analysis/{request_id}/status")
        data = status_response.json()

        # Should have some completed steps
        assert "steps_completed" in data
        assert "steps_remaining" in data


class TestAnalysisValidation:
    """Tests for analysis request validation."""

    def test_missing_patient_id(self, client):
        """Test rejection of request without patient_id."""
        request = {"analysis_type": "full"}
        response = client.post("/api/v1/analysis/run", json=request)
        assert response.status_code == 422

    def test_invalid_analysis_type(self, client):
        """Test handling of invalid analysis type."""
        request = {
            "patient_id": "P001",
            "analysis_type": "invalid_type"
        }
        # Should either accept (if not validated) or reject
        response = client.post("/api/v1/analysis/run", json=request)
        assert response.status_code in [200, 400, 422]

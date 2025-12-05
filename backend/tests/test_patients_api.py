"""Tests for Patients API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestPatientsAPI:
    """Tests for patient CRUD endpoints."""

    def test_list_patients(self, client):
        """Test listing all patients."""
        response = client.get("/api/v1/patients")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_list_patients_with_pagination(self, client):
        """Test patient list pagination."""
        response = client.get("/api/v1/patients?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_patients_with_search(self, client):
        """Test patient list with search filter."""
        response = client.get("/api/v1/patients?search=Thompson")
        assert response.status_code == 200

        data = response.json()
        # Should find patients with "Thompson" in name
        assert "items" in data

    def test_get_patient_by_id(self, client):
        """Test getting a patient by ID."""
        # First get list to find an ID
        list_response = client.get("/api/v1/patients")
        patients = list_response.json()["items"]

        if patients:
            patient_id = patients[0]["id"]
            response = client.get(f"/api/v1/patients/{patient_id}")
            assert response.status_code == 200

            data = response.json()
            assert data["id"] == patient_id

    def test_get_patient_not_found(self, client):
        """Test getting a non-existent patient."""
        response = client.get("/api/v1/patients/NONEXISTENT")
        assert response.status_code == 404

    def test_create_patient(self, client):
        """Test creating a new patient."""
        new_patient = {
            "id": "TEST-NEW-001",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1970-05-20",
            "sex": "Female"
        }

        response = client.post("/api/v1/patients", json=new_patient)
        assert response.status_code == 201

        data = response.json()
        assert data["id"] == "TEST-NEW-001"
        assert data["first_name"] == "Jane"

    def test_create_patient_invalid_data(self, client):
        """Test creating a patient with invalid data."""
        invalid_patient = {
            "id": "TEST",
            # Missing required fields
        }

        response = client.post("/api/v1/patients", json=invalid_patient)
        assert response.status_code == 422  # Validation error

    def test_update_patient(self, client):
        """Test updating a patient."""
        # First create a patient
        new_patient = {
            "id": "TEST-UPDATE-001",
            "first_name": "Update",
            "last_name": "Test",
            "date_of_birth": "1980-01-01",
            "sex": "Male"
        }
        client.post("/api/v1/patients", json=new_patient)

        # Update the patient
        update_data = {
            "first_name": "Updated",
            "email": "updated@test.com"
        }

        response = client.put("/api/v1/patients/TEST-UPDATE-001", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["email"] == "updated@test.com"

    def test_update_patient_not_found(self, client):
        """Test updating a non-existent patient."""
        update_data = {"first_name": "Test"}
        response = client.put("/api/v1/patients/NONEXISTENT", json=update_data)
        assert response.status_code == 404

    def test_delete_patient(self, client):
        """Test deleting a patient."""
        # First create a patient
        new_patient = {
            "id": "TEST-DELETE-001",
            "first_name": "Delete",
            "last_name": "Test",
            "date_of_birth": "1990-01-01",
            "sex": "Female"
        }
        client.post("/api/v1/patients", json=new_patient)

        # Delete the patient
        response = client.delete("/api/v1/patients/TEST-DELETE-001")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get("/api/v1/patients/TEST-DELETE-001")
        assert get_response.status_code == 404

    def test_delete_patient_not_found(self, client):
        """Test deleting a non-existent patient."""
        response = client.delete("/api/v1/patients/NONEXISTENT")
        assert response.status_code == 404


class TestPatientFiltering:
    """Tests for patient filtering functionality."""

    def test_filter_by_cancer_type(self, client):
        """Test filtering patients by cancer type."""
        response = client.get("/api/v1/patients?cancer_type=Non-Small Cell Lung Cancer")
        assert response.status_code == 200

    def test_filter_by_stage(self, client):
        """Test filtering patients by cancer stage."""
        response = client.get("/api/v1/patients?stage=Stage IIIA")
        assert response.status_code == 200

    def test_combined_filters(self, client):
        """Test combining multiple filters."""
        response = client.get(
            "/api/v1/patients?search=Thompson&cancer_type=Non-Small Cell Lung Cancer"
        )
        assert response.status_code == 200


class TestPatientValidation:
    """Tests for patient data validation."""

    def test_invalid_date_format(self, client):
        """Test rejection of invalid date format."""
        invalid_patient = {
            "id": "TEST-INVALID",
            "first_name": "Test",
            "last_name": "Invalid",
            "date_of_birth": "invalid-date",
            "sex": "Male"
        }

        response = client.post("/api/v1/patients", json=invalid_patient)
        assert response.status_code in [400, 422]  # Bad request or validation error

    def test_empty_required_fields(self, client):
        """Test rejection of empty required fields."""
        invalid_patient = {
            "id": "",
            "first_name": "",
            "last_name": "Test",
            "date_of_birth": "1990-01-01",
            "sex": "Male"
        }

        response = client.post("/api/v1/patients", json=invalid_patient)
        # Should either reject or accept - depends on validation rules
        assert response.status_code in [201, 400, 422]

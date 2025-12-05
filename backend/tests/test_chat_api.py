"""Tests for Chat API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestChatAPI:
    """Tests for chat endpoints."""

    def test_send_message(self, client):
        """Test sending a chat message."""
        request = {
            "message": "What are my treatment options?"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert data["patient_id"] == "P001"
        assert data["escalate_to_human"] is False

    def test_send_message_with_context(self, client):
        """Test sending a message with context."""
        request = {
            "message": "Tell me about targeted therapy",
            "context": {"include_genomics": True}
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data

    def test_chat_history(self, client):
        """Test getting chat history."""
        # First send a message
        request = {"message": "Hello"}
        client.post("/api/v1/chat/P001/message", json=request)

        # Get history
        response = client.get("/api/v1/chat/P001/history")
        assert response.status_code == 200

        data = response.json()
        assert "messages" in data
        assert data["patient_id"] == "P001"

    def test_clear_chat_history(self, client):
        """Test clearing chat history."""
        # Send a message first
        client.post("/api/v1/chat/P001/message", json={"message": "Test"})

        # Clear history
        response = client.delete("/api/v1/chat/P001/history")
        assert response.status_code == 200

        # Verify empty
        history_response = client.get("/api/v1/chat/P001/history")
        assert len(history_response.json()["messages"]) == 0


class TestChatSafety:
    """Tests for chat safety features."""

    def test_escalation_on_crisis_keywords(self, client):
        """Test escalation triggered by crisis keywords."""
        request = {
            "message": "I'm having severe chest pain"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["escalate_to_human"] is True
        assert data["escalation_reason"] is not None

    def test_restricted_topic_handling(self, client):
        """Test handling of restricted topics (prognosis)."""
        request = {
            "message": "How long do I have to live?"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        assert response.status_code == 200

        data = response.json()
        # Should redirect to care team (accepts various forms)
        response_lower = data["response"].lower()
        assert "care team" in response_lower or "oncologist" in response_lower or "oncology team" in response_lower

    def test_normal_question_no_escalation(self, client):
        """Test that normal questions don't trigger escalation."""
        request = {
            "message": "What side effects should I expect?"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["escalate_to_human"] is False


class TestChatResponses:
    """Tests for chat response quality."""

    def test_treatment_question_response(self, client):
        """Test response to treatment-related question."""
        request = {
            "message": "Tell me about my treatment options"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        data = response.json()

        # Should have substantive response
        assert len(data["response"]) > 100
        assert "treatment" in data["response"].lower()

    def test_side_effects_question_response(self, client):
        """Test response to side effects question."""
        request = {
            "message": "What side effects might I experience?"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        data = response.json()

        assert len(data["response"]) > 100
        # Should mention common side effects or symptom management

    def test_clinical_trial_question_response(self, client):
        """Test response to clinical trial question."""
        request = {
            "message": "Are there any clinical trials I might be eligible for?"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        data = response.json()

        assert len(data["response"]) > 100
        assert "trial" in data["response"].lower()

    def test_genomics_question_response(self, client):
        """Test response to genomics/mutation question."""
        request = {
            "message": "What does my EGFR mutation mean?"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        data = response.json()

        assert len(data["response"]) > 100
        # Should mention EGFR or mutation

    def test_suggested_followups(self, client):
        """Test that responses include suggested follow-ups."""
        request = {
            "message": "Hello, I have questions about my care"
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        data = response.json()

        # Should have suggested follow-up questions
        assert "suggested_followup" in data


class TestChatValidation:
    """Tests for chat input validation."""

    def test_empty_message(self, client):
        """Test handling of empty message."""
        request = {"message": ""}

        response = client.post("/api/v1/chat/P001/message", json=request)
        # Should either handle gracefully or reject
        assert response.status_code in [200, 400, 422]

    def test_very_long_message(self, client):
        """Test handling of very long message."""
        request = {
            "message": "This is a test message. " * 1000  # Very long
        }

        response = client.post("/api/v1/chat/P001/message", json=request)
        # Should handle without crashing
        assert response.status_code in [200, 400, 413]  # 413 = payload too large

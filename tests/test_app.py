"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities to initial state after each test"""
    from app import activities
    
    # Store original state
    original_state = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, activity in activities.items():
        activity["participants"] = original_state[name]["participants"].copy()


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that GET /activities returns expected activities"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Drama Club",
            "Debate Team",
            "Science Club"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in activities
    
    def test_get_activities_includes_required_fields(self, client):
        """Test that each activity contains required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing {field}"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_returns_200_on_success(self, client, reset_activities):
        """Test that signup returns 200 on successful registration"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "new_student@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_returns_success_message(self, client, reset_activities):
        """Test that signup returns a success message"""
        email = "new_student@mergington.edu"
        activity = "Basketball Team"
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        email = "new_student@mergington.edu"
        activity = "Basketball Team"
        
        # Signup
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Test that signing up with duplicate email returns 400"""
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_returns_200_on_success(self, client, reset_activities):
        """Test that unregister returns 200 on successful removal"""
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_unregister_returns_success_message(self, client, reset_activities):
        """Test that unregister returns a success message"""
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client):
        """Test that unregistering a non-registered participant returns 400"""
        activity = "Basketball Team"
        email = "nonexistent@mergington.edu"
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


class TestIntegration:
    """Integration tests for multiple operations"""
    
    def test_signup_then_unregister_flow(self, client, reset_activities):
        """Test the full flow of signing up and then unregistering"""
        activity = "Tennis Club"
        email = "test_student@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
    
    def test_multiple_signups_increase_capacity(self, client, reset_activities):
        """Test that multiple signups properly increase capacity"""
        activity = "Tennis Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up multiple students
        for email in emails:
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
        
        # Verify all were added
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in response.json()[activity]["participants"]

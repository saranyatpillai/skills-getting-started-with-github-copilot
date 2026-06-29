import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_success(self, client):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        # Verify structure of activities
        for name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that expected activities are present."""
        response = client.get("/activities")
        activities = response.json()
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the activity."""
        email = "testsignup@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()["Chess Club"]["participants"]

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup returns error."""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that same student can sign up for multiple activities."""
        email = "multiactivity@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Test successful unregister from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant."""
        # First sign up
        email = "unregistertest@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify they're signed up
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.post(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Verify they're removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister for student not signed up."""
        email = "notsignedup@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_unregister_cycle(self, client):
        """Test complete signup and unregister cycle."""
        email = "cycle@mergington.edu"
        activity = "Basketball%20Team"
        
        # Initial state - not signed up
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball Team"]["participants"])
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()["Basketball Team"]["participants"]
        assert len(response.json()["Basketball Team"]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify back to initial state
        response = client.get("/activities")
        assert email not in response.json()["Basketball Team"]["participants"]
        assert len(response.json()["Basketball Team"]["participants"]) == initial_count

    def test_cannot_register_twice(self, client):
        """Test that duplicate registrations are prevented."""
        email = "duplicate@mergington.edu"
        activity = "Swimming%20Club"
        
        # First signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

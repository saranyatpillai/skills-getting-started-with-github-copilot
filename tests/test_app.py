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
        # Arrange
        # No setup needed - testing default state
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure."""
        # Arrange
        # No setup needed
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that expected activities are present."""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity in expected_activities:
            assert activity in activities


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        # Arrange
        activity_name = "Chess%20Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the activity."""
        # Arrange
        email = "testsignup@mergington.edu"
        activity_name = "Chess%20Club"
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        
        # Assert
        assert new_count == initial_count + 1
        assert email in response.json()["Chess Club"]["participants"]

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup returns error."""
        # Arrange
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity_name = "Chess%20Club"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist."""
        # Arrange
        activity_name = "Nonexistent%20Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that same student can sign up for multiple activities."""
        # Arrange
        email = "multiactivity@mergington.edu"
        activity1 = "Chess%20Club"
        activity2 = "Programming%20Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Test successful unregister from an activity."""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess%20Club"
        
        # Act
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant."""
        # Arrange
        email = "unregistertest@mergington.edu"
        activity_name = "Chess%20Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        response = client.get("/activities")
        
        # Assert
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister for student not signed up."""
        # Arrange
        email = "notsignedup@mergington.edu"
        activity_name = "Chess%20Club"
        
        # Act
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from activity that doesn't exist."""
        # Arrange
        activity_name = "Nonexistent%20Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_unregister_cycle(self, client):
        """Test complete signup and unregister cycle."""
        # Arrange
        email = "cycle@mergington.edu"
        activity_name = "Basketball%20Team"
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball Team"]["participants"])
        
        # Act - Sign up
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        response = client.get("/activities")
        count_after_signup = len(response.json()["Basketball Team"]["participants"])
        
        # Act - Unregister
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 200
        
        response = client.get("/activities")
        count_after_unregister = len(response.json()["Basketball Team"]["participants"])
        
        # Assert
        assert count_after_signup == initial_count + 1
        assert count_after_unregister == initial_count
        assert email not in response.json()["Basketball Team"]["participants"]

    def test_cannot_register_twice(self, client):
        """Test that duplicate registrations are prevented."""
        # Arrange
        email = "duplicate@mergington.edu"
        activity_name = "Swimming%20Club"
        
        # Act
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]


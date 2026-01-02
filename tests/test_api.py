import pytest
from fastapi.testclient import TestClient


class TestActivitiesAPI:
    """Test cases for the Activities API"""

    def test_root_redirect(self, client: TestClient):
        """Test that root endpoint redirects to static files"""
        response = client.get("/")
        assert response.status_code == 200
        # The redirect response should serve the HTML file
        assert "Mergington High School" in response.text

    def test_get_activities(self, client: TestClient):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

        # Check that we have some expected activities
        assert "Chess Club" in data
        assert "Programming Class" in data

        # Check structure of an activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_signup_successful(self, client: TestClient):
        """Test successful signup for an activity"""
        # First get current participants
        response = client.get("/activities")
        initial_data = response.json()
        initial_participants = len(initial_data["Chess Club"]["participants"])

        # Sign up a new student
        response = client.post(
            "/activities/Chess%20Club/signup?email=test%40student.edu"
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Signed up test@student.edu for Chess Club" in data["message"]

        # Verify the student was added
        response = client.get("/activities")
        updated_data = response.json()
        updated_participants = updated_data["Chess Club"]["participants"]
        assert len(updated_participants) == initial_participants + 1
        assert "test@student.edu" in updated_participants

    def test_signup_already_registered(self, client: TestClient):
        """Test signup when student is already registered"""
        # First sign up
        client.post("/activities/Chess%20Club/signup?email=duplicate%40student.edu")

        # Try to sign up again
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate%40student.edu"
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self, client: TestClient):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test%40student.edu"
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_unregister_successful(self, client: TestClient):
        """Test successful unregister from an activity"""
        # First sign up a student
        client.post("/activities/Tennis%20Club/signup?email=unregister%40student.edu")

        # Get initial count
        response = client.get("/activities")
        initial_data = response.json()
        initial_participants = len(initial_data["Tennis Club"]["participants"])

        # Unregister the student
        response = client.delete(
            "/activities/Tennis%20Club/unregister?email=unregister%40student.edu"
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Unregistered unregister@student.edu from Tennis Club" in data["message"]

        # Verify the student was removed
        response = client.get("/activities")
        updated_data = response.json()
        updated_participants = updated_data["Tennis Club"]["participants"]
        assert len(updated_participants) == initial_participants - 1
        assert "unregister@student.edu" not in updated_participants

    def test_unregister_not_registered(self, client: TestClient):
        """Test unregister when student is not registered"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered%40student.edu"
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"]

    def test_unregister_invalid_activity(self, client: TestClient):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister?email=test%40student.edu"
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_activity_data_integrity(self, client: TestClient):
        """Test that activity data structure is maintained"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()

        # Check each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data

            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

            # Check max_participants is reasonable
            assert activity_data["max_participants"] > 0

            # Check participants are email-like strings
            for participant in activity_data["participants"]:
                assert "@" in participant
                assert isinstance(participant, str)
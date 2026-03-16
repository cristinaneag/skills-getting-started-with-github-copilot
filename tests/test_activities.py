"""
Integration tests for FastAPI activities endpoints.
Tests cover GET /activities, POST signup, and DELETE unregister endpoints.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all 9 activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9

    def test_get_activities_returns_correct_structure(self, client):
        """Test that each activity has the correct data structure"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check structure of one activity as example
        soccer = activities.get("Soccer Team")
        assert soccer is not None
        assert "description" in soccer
        assert "schedule" in soccer
        assert "max_participants" in soccer
        assert "participants" in soccer
        assert isinstance(soccer["participants"], list)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that specific expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Soccer Team",
            "Basketball Club",
            "Art Workshop",
            "Chess Club",
            "Programming Class"
        ]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Soccer Team" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the student to participants"""
        new_email = "newstudent@mergington.edu"
        
        # Signup
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": new_email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert new_email in activities["Soccer Team"]["participants"]

    def test_signup_multiple_students(self, client):
        """Test that multiple different students can signup for the same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Art Workshop/signup",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Art Workshop/signup",
            params={"email": email2}
        )
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email1 in activities["Art Workshop"]["participants"]
        assert email2 in activities["Art Workshop"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup fails with 404 when activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_signed_up(self, client):
        """Test signup fails with 400 when student is already signed up"""
        email = "lucas@mergington.edu"  # Already signed up for Soccer Team
        
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_allows_exceeding_max_participants(self, client):
        """
        Test that signup allows exceeding max_participants (no validation enforced).
        
        Note: The app currently does not validate max_participants limits.
        This test documents the current behavior - students can sign up even
        when capacity is exceeded. This could be a future enhancement.
        """
        # Art Workshop has max_participants: 10 and currently has 2 students
        # Add 9 more students (exceeding capacity of 10 max)
        for i in range(9):
            response = client.post(
                "/activities/Art Workshop/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
            assert response.status_code == 200
        
        # Verify we have 11 participants (2 initial + 9 added, exceeding max of 10)
        activities_response = client.get("/activities")
        activities = activities_response.json()
        art_workshop = activities["Art Workshop"]
        assert len(art_workshop["participants"]) == 11
        assert len(art_workshop["participants"]) > art_workshop["max_participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "lucas@mergington.edu"  # Already signed up for Soccer Team
        
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the student from participants"""
        email = "mia@mergington.edu"  # Already signed up for Soccer Team
        
        # Verify student is signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Soccer Team"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Soccer Team"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister fails with 404 when activity doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_student_not_signed_up(self, client):
        """Test unregister fails with 400 when student is not signed up"""
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and then sign up again"""
        email = "lucas@mergington.edu"
        
        # Unregister
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Sign up again should work
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify student is signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Soccer Team"]["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""

    def test_signup_unregister_flow(self, client):
        """Test complete flow of signup followed by unregister"""
        email = "integration@mergington.edu"
        activity = "Chess Club"
        
        # Initial state - student not signed up
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]

    def test_multiple_signups_across_activities(self, client):
        """Test a student signing up for multiple different activities"""
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Soccer Team", "Chess Club", "Programming Class"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is signed up for all activities
        activities_response = client.get("/activities")
        all_activities = activities_response.json()
        
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]

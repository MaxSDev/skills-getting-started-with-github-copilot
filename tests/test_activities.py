import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        name: details["participants"].copy()
        for name, details in activities.items()
    }
    yield
    for name, participants in original_participants.items():
        activities[name]["participants"][:] = participants


def test_get_activities_returns_current_participants_without_caching():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["Chess Club"]["participants"] == activities["Chess Club"]["participants"]


def test_signup_adds_participant():
    email = "new-student@mergington.edu"

    response = client.post(
        "/activities/Basketball Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email in activities["Basketball Team"]["participants"]
    assert email in client.get("/activities").json()["Basketball Team"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = activities["Chess Club"]["participants"][0]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_unregister_removes_participant():
    email = "student-to-remove@mergington.edu"
    activities["Basketball Team"]["participants"].append(email)

    response = client.delete(
        "/activities/Basketball Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email not in activities["Basketball Team"]["participants"]


def test_unregister_rejects_unknown_participant():
    response = client.delete(
        "/activities/Basketball Team/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404


def test_signup_and_unregister_reject_unknown_activity():
    signup_response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )
    unregister_response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert signup_response.status_code == 404
    assert unregister_response.status_code == 404

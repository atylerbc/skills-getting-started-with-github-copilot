import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def test_activities(monkeypatch):
    activities = {
        "Test Club": {
            "description": "A test activity",
            "schedule": "Mondays",
            "max_participants": 3,
            "participants": ["existing@example.test"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(test_activities):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client, test_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == test_activities


def test_signup_adds_participant(client, test_activities):
    response = client.post(
        "/activities/Test Club/signup",
        params={"email": "new@example.test"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@example.test for Test Club"
    }
    assert "new@example.test" in test_activities["Test Club"]["participants"]


def test_signup_rejects_duplicate_participant(client, test_activities):
    response = client.post(
        "/activities/Test Club/signup",
        params={"email": "existing@example.test"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"
    assert test_activities["Test Club"]["participants"] == ["existing@example.test"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@example.test"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, test_activities):
    response = client.delete(
        "/activities/Test Club/signup",
        params={"email": "existing@example.test"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.test from Test Club"
    }
    assert test_activities["Test Club"]["participants"] == []


def test_unregister_rejects_non_participant(client, test_activities):
    response = client.delete(
        "/activities/Test Club/signup",
        params={"email": "missing@example.test"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert test_activities["Test Club"]["participants"] == ["existing@example.test"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "existing@example.test"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

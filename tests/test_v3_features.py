"""Membership, progress and workouts (release 3.0.0)."""
from test_v2_features import add


def test_membership_state(v3):
    module, _ = v3
    assert module.membership_state("Active", None) == "Active"
    assert module.membership_state("Active", "2999-01-01") == "Active"
    assert module.membership_state("Active", "2000-01-01") == "Expired"
    assert module.membership_state("Cancelled", None) == "Inactive"


def test_client_membership(v3):
    _, client = v3
    add(client)
    assert client.get("/clients/Arun/membership").get_json() == {"membership": "Active"}
    add(client, name="Old", membership_end="2000-01-01")
    assert client.get("/clients/Old/membership").get_json()["membership"] == "Expired"
    assert client.get("/clients/Nobody/membership").status_code == 404


def test_progress(v3):
    _, client = v3
    add(client)
    ok = client.post("/clients/Arun/progress", json={"adherence": 85, "week": "W1"})
    assert ok.status_code == 201
    assert client.post("/clients/Arun/progress", json={"adherence": 150}).status_code == 400
    assert client.post("/clients/Arun/progress", json={"adherence": 70}).status_code == 201
    assert client.get("/clients/Arun/progress").get_json()[0] == {"week": "W1",
                                                                  "adherence": 85}
    assert client.post("/clients/Nobody/progress", json={"adherence": 1}).status_code == 404
    assert client.get("/clients/Nobody/progress").status_code == 404


def test_workouts(v3):
    _, client = v3
    add(client)
    assert client.post("/clients/Arun/workouts", json={}).status_code == 400
    resp = client.post("/clients/Arun/workouts",
                       json={"workout_type": "Strength", "duration_min": 60})
    assert resp.status_code == 201
    assert client.get("/clients/Arun/workouts").get_json()[0]["workout_type"] == "Strength"
    assert client.post("/clients/Nobody/workouts", json={"workout_type": "x"}).status_code == 404
    assert client.get("/clients/Nobody/workouts").status_code == 404

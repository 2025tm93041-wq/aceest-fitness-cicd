"""Client management, calories and BMI (release 2.0.0 and later)."""
import pytest


def add(client, **overrides):
    payload = {"name": "Arun", "age": 28, "height": 175, "weight": 80, "program": "MG"}
    payload.update(overrides)
    return client.post("/clients", json=payload)


@pytest.mark.parametrize("code,weight,expected",
                         [("FL", 80, 1760), ("MG", 80, 2800), ("BG", 70, 1820)])
def test_calories(v2, code, weight, expected):
    module, _ = v2
    assert module.calculate_calories(weight, code) == expected


def test_calories_invalid(v2):
    module, _ = v2
    with pytest.raises(ValueError):
        module.calculate_calories(80, "XX")
    with pytest.raises(ValueError):
        module.calculate_calories(0, "FL")


@pytest.mark.parametrize("w,h,cat", [(50, 175, "Underweight"), (70, 175, "Normal"),
                                     (85, 175, "Overweight"), (110, 175, "Obese")])
def test_bmi_categories(v2, w, h, cat):
    module, _ = v2
    assert module.calculate_bmi(w, h)[1] == cat


def test_bmi_invalid(v2):
    module, _ = v2
    with pytest.raises(ValueError):
        module.calculate_bmi(70, 0)


def test_add_and_get_client(v2):
    _, client = v2
    resp = add(client)
    assert resp.status_code == 201
    assert resp.get_json()["calories"] == 2800
    assert client.get("/clients/Arun").get_json()["program"] == "MG"
    assert client.get("/clients").get_json() == [{"name": "Arun", "program": "MG"}]


def test_add_client_validation(v2):
    _, client = v2
    assert client.post("/clients", json={}).status_code == 400
    assert add(client, program="XX").status_code == 400
    add(client)
    assert add(client).status_code == 409


def test_unknown_client_returns_404(v2):
    _, client = v2
    assert client.get("/clients/Nobody").status_code == 404
    assert client.get("/clients/Nobody/bmi").status_code == 404


def test_client_bmi(v2):
    _, client = v2
    add(client)
    assert client.get("/clients/Arun/bmi").get_json() == {"bmi": 26.1,
                                                          "category": "Overweight"}


def test_bmi_requires_measurements(v2):
    _, client = v2
    client.post("/clients", json={"name": "NoData"})
    assert client.get("/clients/NoData/bmi").status_code == 400

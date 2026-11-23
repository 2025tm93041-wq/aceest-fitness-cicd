"""Behaviour shared by every release (1.0.0, 2.0.0, 3.0.0)."""


def test_health(any_version):
    _, _, client = any_version
    assert client.get("/health").get_json() == {"status": "ok"}


def test_version_endpoint_reports_release(any_version):
    version, _, client = any_version
    data = client.get("/version").get_json()
    assert data["version"] == version
    assert data["hostname"]


def test_index(any_version):
    version, _, client = any_version
    data = client.get("/").get_json()
    assert data["status"] == "running"
    assert data["version"] == version


def test_programs(any_version):
    _, _, client = any_version
    assert set(client.get("/programs").get_json()) == {"FL", "MG", "BG"}
    assert client.get("/programs/fl").get_json()["calorie_factor"] == 22
    assert client.get("/programs/ZZ").status_code == 404


def test_older_releases_lack_newer_features(any_version):
    version, _, client = any_version
    status = client.get("/clients").status_code
    assert status == (404 if version == "1.0.0" else 200)

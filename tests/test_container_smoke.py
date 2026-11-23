"""Runs INSIDE the built Docker image: checks the image holds the right release."""
import os

import pytest

EXPECTED = os.environ.get("EXPECTED_VERSION")
pytestmark = pytest.mark.skipif(EXPECTED is None, reason="only runs inside a container")


def test_image_contains_expected_release(tmp_path):
    import ACEest_Fitness
    assert ACEest_Fitness.VERSION == EXPECTED
    client = ACEest_Fitness.create_app(str(tmp_path / "c.db")).test_client()
    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.get("/version").get_json()["version"] == EXPECTED
    assert client.get("/programs").status_code == 200

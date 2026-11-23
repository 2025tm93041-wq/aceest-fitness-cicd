import importlib.util
import os
import pathlib
import tempfile

import pytest

# Keep the import-time default database out of the repository folder.
os.environ.setdefault("DB_PATH", os.path.join(tempfile.mkdtemp(), "import.db"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION_FILES = {
    "1.0.0": ROOT / "versions" / "ACEest_Fitness_v1.py",
    "2.0.0": ROOT / "versions" / "ACEest_Fitness_v2.py",
    "3.0.0": ROOT / "ACEest_Fitness.py",
}


def load_version(version):
    """Import one release of the application from its file."""
    spec = importlib.util.spec_from_file_location(
        "aceest_" + version.replace(".", "_"), VERSION_FILES[version])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=sorted(VERSION_FILES))
def any_version(request, tmp_path):
    module = load_version(request.param)
    app = module.create_app(str(tmp_path / "t.db"))
    app.config["TESTING"] = True
    return request.param, module, app.test_client()


@pytest.fixture
def v2(tmp_path):
    module = load_version("2.0.0")
    app = module.create_app(str(tmp_path / "t.db"))
    return module, app.test_client()


@pytest.fixture
def v3(tmp_path):
    module = load_version("3.0.0")
    app = module.create_app(str(tmp_path / "t.db"))
    return module, app.test_client()

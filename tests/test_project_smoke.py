from geotech_ts import __version__
from geotech_ts.paths import DATA_DIR, PROJECT_ROOT


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_project_paths_exist() -> None:
    assert PROJECT_ROOT.is_dir()
    assert DATA_DIR.is_dir()

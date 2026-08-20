"""Verify that the project and its core scientific packages can be imported."""

from importlib.metadata import version

import geotech_ts

PACKAGES = (
    "numpy",
    "pandas",
    "scipy",
    "statsmodels",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "ruptures",
    "pyarrow",
)


def main() -> None:
    """Print installed versions as a compact environment receipt."""
    print(f"geotech_ts {geotech_ts.__version__}")
    for package in PACKAGES:
        print(f"{package} {version(package)}")


if __name__ == "__main__":
    main()

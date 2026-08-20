import hashlib
from pathlib import Path

import pytest

from geotech_ts.acquisition import (
    DOI,
    SCIENCEBASE_ITEM_ID,
    AcquisitionError,
    ScienceBaseResource,
    select_resources,
    verify_resource_file,
)


def test_select_resources_requires_expected_doi_item_shape() -> None:
    item = {
        "files": [
            {
                "name": "example.zip",
                "title": "Example",
                "downloadUri": "https://example.gov/example.zip",
                "size": 3,
                "dateUploaded": "2024-01-01T00:00:00Z",
                "checksum": {"type": "MD5", "value": "abc"},
            }
        ]
    }
    selected = select_resources(item, ["example.zip"])

    assert selected[0].name == "example.zip"
    assert selected[0].source_checksum_algorithm == "md5"
    assert DOI == "10.5066/P1P9DMFX"
    assert SCIENCEBASE_ITEM_ID == "65d8f08fd34ec3e1801e3efc"


def test_verify_resource_file_checks_size_and_official_digest(tmp_path: Path) -> None:
    path = tmp_path / "resource.bin"
    path.write_bytes(b"official bytes")
    resource = ScienceBaseResource(
        name=path.name,
        title="Synthetic test resource",
        url="https://example.gov/resource.bin",
        byte_size=path.stat().st_size,
        date_uploaded="2024-01-01T00:00:00Z",
        source_checksum_algorithm="md5",
        source_checksum=hashlib.md5(path.read_bytes()).hexdigest(),
    )

    size, sha256 = verify_resource_file(path, resource)

    assert size == len(b"official bytes")
    assert sha256 == hashlib.sha256(b"official bytes").hexdigest()

    altered = path.with_name("altered.bin")
    altered.write_bytes(b"changed bytes")
    with pytest.raises(AcquisitionError, match="Size mismatch"):
        verify_resource_file(altered, resource)


def test_resource_selection_rejects_path_traversal() -> None:
    with pytest.raises(AcquisitionError, match="Unsafe resource filename"):
        select_resources({"files": []}, ["../example.zip"])

"""Reproducible acquisition of official ScienceBase resources."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

SCIENCEBASE_ITEM_ID = "65d8f08fd34ec3e1801e3efc"
SCIENCEBASE_ITEM_URL = (
    f"https://www.sciencebase.gov/catalog/item/{SCIENCEBASE_ITEM_ID}?format=json"
)
DOI = "10.5066/P1P9DMFX"
REQUIRED_PRIMARY_RESOURCES = (
    "Cleveland_Corral_15_Minute_Data.zip",
    "Cleveland_Corral_Daily_Data.zip",
    "Cleveland_Corral_Sensor_Descriptions.csv",
)


class AcquisitionError(RuntimeError):
    """Raised when an official resource cannot be accepted unchanged."""


@dataclass(frozen=True)
class ScienceBaseResource:
    """Source metadata needed to acquire and verify one file."""

    name: str
    title: str
    url: str
    byte_size: int
    date_uploaded: str
    source_checksum_algorithm: str
    source_checksum: str


@dataclass(frozen=True)
class AcquisitionRecord:
    """Machine-readable receipt without an absolute local path."""

    doi: str
    sciencebase_item_id: str
    sciencebase_item_url: str
    filename: str
    title: str
    exact_resource_url: str
    byte_size: int
    sha256: str
    source_checksum_algorithm: str
    source_checksum: str
    source_date_uploaded: str
    item_last_updated: str
    response_last_modified: str
    response_etag: str
    access_timestamp_utc: str
    license: str
    local_raw_layer_id: str


def file_digest(path: Path, algorithm: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    """Return a streaming cryptographic digest for a local file."""

    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_sciencebase_item(
    *, session: requests.Session | None = None, timeout_seconds: float = 60
) -> dict[str, Any]:
    """Fetch the authoritative JSON metadata for the primary monitoring release."""

    client = session or requests.Session()
    response = client.get(SCIENCEBASE_ITEM_URL, timeout=timeout_seconds)
    response.raise_for_status()
    item = response.json()
    if item.get("id") != SCIENCEBASE_ITEM_ID:
        raise AcquisitionError("ScienceBase returned an unexpected item identifier")
    identifiers = {entry.get("key", "") for entry in item.get("identifiers", [])}
    if f"doi:{DOI}" not in identifiers:
        raise AcquisitionError("ScienceBase item does not advertise the expected DOI")
    return item


def select_resources(
    item: dict[str, Any], filenames: Iterable[str] = REQUIRED_PRIMARY_RESOURCES
) -> list[ScienceBaseResource]:
    """Select explicitly allowed files from ScienceBase item metadata."""

    wanted = tuple(filenames)
    if not wanted or len(set(wanted)) != len(wanted):
        raise AcquisitionError("Resource names must be a non-empty unique sequence")
    available = {resource.get("name"): resource for resource in item.get("files", [])}
    selected: list[ScienceBaseResource] = []
    for name in wanted:
        if Path(name).name != name:
            raise AcquisitionError(f"Unsafe resource filename: {name!r}")
        resource = available.get(name)
        if resource is None:
            raise AcquisitionError(f"Required resource is absent from ScienceBase: {name}")
        checksum = resource.get("checksum") or {}
        checksum_algorithm = str(checksum.get("type", "")).lower()
        checksum_value = str(checksum.get("value", "")).lower()
        if checksum_algorithm not in hashlib.algorithms_available or not checksum_value:
            raise AcquisitionError(f"Unsupported or missing source checksum for {name}")
        selected.append(
            ScienceBaseResource(
                name=name,
                title=str(resource.get("title") or "not_stated"),
                url=str(resource.get("downloadUri") or resource.get("url") or ""),
                byte_size=int(resource["size"]),
                date_uploaded=str(resource.get("dateUploaded") or "not_stated"),
                source_checksum_algorithm=checksum_algorithm,
                source_checksum=checksum_value,
            )
        )
    return selected


def verify_resource_file(path: Path, resource: ScienceBaseResource) -> tuple[int, str]:
    """Verify size and official checksum, returning size and SHA-256."""

    actual_size = path.stat().st_size
    if actual_size != resource.byte_size:
        raise AcquisitionError(
            f"Size mismatch for {resource.name}: expected {resource.byte_size}, got {actual_size}"
        )
    actual_source_checksum = file_digest(path, resource.source_checksum_algorithm)
    if actual_source_checksum != resource.source_checksum:
        raise AcquisitionError(
            f"{resource.source_checksum_algorithm.upper()} mismatch for {resource.name}"
        )
    return actual_size, file_digest(path, "sha256")


def acquire_resource(
    resource: ScienceBaseResource,
    raw_directory: Path,
    *,
    item_last_updated: str,
    rights: str,
    session: requests.Session | None = None,
    timeout_seconds: float = 120,
) -> AcquisitionRecord:
    """Download one resource atomically or verify the unchanged existing file."""

    raw_directory.mkdir(parents=True, exist_ok=True)
    target = raw_directory / resource.name
    response_last_modified = "not_stated"
    response_etag = "not_stated"
    access_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()

    if not target.exists():
        partial = target.with_name(f"{target.name}.partial")
        if partial.exists():
            raise AcquisitionError(
                "Interrupted partial download already exists; inspect it before retrying: "
                f"{partial}"
            )
        client = session or requests.Session()
        try:
            with client.get(resource.url, stream=True, timeout=timeout_seconds) as response:
                response.raise_for_status()
                response_last_modified = response.headers.get("Last-Modified", "not_stated")
                response_etag = response.headers.get("ETag", "not_stated")
                with partial.open("xb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
            verify_resource_file(partial, resource)
            partial.replace(target)
        except Exception:
            partial.unlink(missing_ok=True)
            raise

    actual_size, sha256 = verify_resource_file(target, resource)
    return AcquisitionRecord(
        doi=DOI,
        sciencebase_item_id=SCIENCEBASE_ITEM_ID,
        sciencebase_item_url=SCIENCEBASE_ITEM_URL,
        filename=resource.name,
        title=resource.title,
        exact_resource_url=resource.url,
        byte_size=actual_size,
        sha256=sha256,
        source_checksum_algorithm=resource.source_checksum_algorithm,
        source_checksum=resource.source_checksum,
        source_date_uploaded=resource.date_uploaded,
        item_last_updated=item_last_updated,
        response_last_modified=response_last_modified,
        response_etag=response_etag,
        access_timestamp_utc=access_timestamp,
        license=rights,
        local_raw_layer_id=f"cleveland_corral/{resource.name}",
    )


def acquire_required_resources(
    raw_directory: Path, *, session: requests.Session | None = None
) -> list[AcquisitionRecord]:
    """Acquire only the two data archives and their official sensor metadata."""

    item = fetch_sciencebase_item(session=session)
    resources = select_resources(item)
    item_last_updated = str((item.get("provenance") or {}).get("lastUpdated") or "not_stated")
    rights = str(item.get("rights") or "not_stated").strip()
    return [
        acquire_resource(
            resource,
            raw_directory,
            item_last_updated=item_last_updated,
            rights=rights,
            session=session,
        )
        for resource in resources
    ]


def write_local_receipt(records: Iterable[AcquisitionRecord], path: Path) -> None:
    """Write an ignored local JSON receipt alongside raw data."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

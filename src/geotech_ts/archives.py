"""Read-only inspection helpers for the official monitoring archives."""

from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path

from geotech_ts.acquisition import file_digest

PREAMBLE_LINE_COUNT = 3
WATER_YEAR_PATTERN = re.compile(r"WY(?P<year>\d{4})", re.IGNORECASE)


class ArchiveInspectionError(RuntimeError):
    """Raised when an archive does not match the expected transparent CSV structure."""


@dataclass(frozen=True)
class ArchiveMemberInspection:
    """Metadata-only inspection of one CSV archive member."""

    archive_filename: str
    archive_sha256: str
    member_path: str
    member_crc32: str
    compressed_bytes: int
    uncompressed_bytes: int
    product_type: str
    station: str
    nominal_water_year: str
    preamble_product_description: str
    timestamp_column: str
    column_count: int
    columns: tuple[str, ...]
    data_row_count: int
    first_timestamp_original: str
    last_timestamp_original: str
    timestamp_parse_failure_count: int
    duplicate_timestamp_count: int
    out_of_order_timestamp_count: int
    irregular_timestamp_step_count: int
    off_grid_timestamp_count: int
    gap_count: int
    missing_expected_interval_count: int
    observed_clock_minute_phases: str


def product_type_from_archive(path: Path) -> str:
    """Return the declared product type from an official archive filename."""

    name = path.name.casefold()
    if "15_minute" in name:
        return "15_minute"
    if "daily" in name:
        return "daily"
    raise ArchiveInspectionError(f"Unrecognized monitoring archive: {path.name}")


def station_from_member(member_path: str) -> str:
    """Infer the official station label from a member name."""

    name = Path(member_path).name.casefold()
    for station in ("middle", "toe", "upper"):
        if station in name:
            return station
    raise ArchiveInspectionError(f"Cannot infer station from member: {member_path}")


def _inspect_member(
    archive_filename: str,
    archive_sha256: str,
    product_type: str,
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
) -> ArchiveMemberInspection:
    with archive.open(info, "r") as binary:
        with TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
            preamble = [text.readline().rstrip("\r\n") for _ in range(PREAMBLE_LINE_COUNT)]
            header_line = text.readline()
    if not header_line:
        raise ArchiveInspectionError(f"Missing CSV header in {info.filename}")
    columns = tuple(next(csv.reader([header_line])))
    expected_timestamp = "date_time_PST" if product_type == "15_minute" else "date"
    if not columns or columns[0] != expected_timestamp:
        raise ArchiveInspectionError(
            f"Unexpected timestamp field in {info.filename}: {columns[0] if columns else 'missing'}"
        )
    water_year_match = WATER_YEAR_PATTERN.search(info.filename)
    timestamp_format = "%m/%d/%Y %H:%M" if product_type == "15_minute" else "%m/%d/%Y"
    expected_seconds = 15 * 60 if product_type == "15_minute" else 24 * 60 * 60
    data_row_count = 0
    first_timestamp_original = "not_available"
    last_timestamp_original = "not_available"
    parse_failures = 0
    duplicate_count = 0
    out_of_order_count = 0
    irregular_count = 0
    off_grid_count = 0
    gap_count = 0
    missing_intervals = 0
    minute_phases: set[int] = set()
    observed_timestamps: set[datetime] = set()
    previous: datetime | None = None
    with archive.open(info, "r") as binary:
        with TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
            reader = csv.reader(text)
            for _ in range(PREAMBLE_LINE_COUNT + 1):
                next(reader, None)
            for row in reader:
                data_row_count += 1
                original = row[0] if row else ""
                if data_row_count == 1:
                    first_timestamp_original = original
                last_timestamp_original = original
                try:
                    parsed = datetime.strptime(original, timestamp_format)
                except ValueError:
                    parse_failures += 1
                    continue
                minute_phases.add(parsed.minute)
                if parsed in observed_timestamps:
                    duplicate_count += 1
                observed_timestamps.add(parsed)
                if previous is not None:
                    delta_seconds = (parsed - previous).total_seconds()
                    if delta_seconds < 0:
                        out_of_order_count += 1
                    if delta_seconds != expected_seconds:
                        irregular_count += 1
                    if delta_seconds > 0 and delta_seconds % expected_seconds != 0:
                        off_grid_count += 1
                    if delta_seconds > expected_seconds:
                        gap_count += 1
                        missing_intervals += max(int(delta_seconds // expected_seconds) - 1, 0)
                previous = parsed
    return ArchiveMemberInspection(
        archive_filename=archive_filename,
        archive_sha256=archive_sha256,
        member_path=info.filename,
        member_crc32=f"{info.CRC:08x}",
        compressed_bytes=info.compress_size,
        uncompressed_bytes=info.file_size,
        product_type=product_type,
        station=station_from_member(info.filename),
        nominal_water_year=water_year_match.group("year") if water_year_match else "not_applicable",
        preamble_product_description=preamble[2],
        timestamp_column=columns[0],
        column_count=len(columns),
        columns=columns,
        data_row_count=data_row_count,
        first_timestamp_original=first_timestamp_original,
        last_timestamp_original=last_timestamp_original,
        timestamp_parse_failure_count=parse_failures,
        duplicate_timestamp_count=duplicate_count,
        out_of_order_timestamp_count=out_of_order_count,
        irregular_timestamp_step_count=irregular_count,
        off_grid_timestamp_count=off_grid_count,
        gap_count=gap_count,
        missing_expected_interval_count=missing_intervals,
        observed_clock_minute_phases=";".join(f"{minute:02d}" for minute in sorted(minute_phases)),
    )


def inspect_archive(path: Path) -> list[ArchiveMemberInspection]:
    """Validate a ZIP and inspect every CSV member without extracting it."""

    archive_sha256 = file_digest(path)
    product_type = product_type_from_archive(path)
    with zipfile.ZipFile(path, "r") as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ArchiveInspectionError(f"ZIP CRC failure in member: {corrupt_member}")
        members = [
            _inspect_member(path.name, archive_sha256, product_type, archive, info)
            for info in archive.infolist()
            if not info.is_dir() and info.filename.casefold().endswith(".csv")
        ]
    if not members:
        raise ArchiveInspectionError(f"No CSV members found in {path}")
    return members


def inspect_archives(paths: list[Path]) -> list[ArchiveMemberInspection]:
    """Inspect a deterministic list of official archives."""

    return [member for path in paths for member in inspect_archive(path)]

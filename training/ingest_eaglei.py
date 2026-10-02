"""Standardize and aggregate EAGLE-I county outage records.

This script is deliberately conservative:
- source files are never modified
- column mappings are explicit
- missing observations are not interpreted as zero
- hourly output keeps the maximum outage count observed within each hour
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from training.config import (
    EAGLEI_HOURLY_DIR,
    EAGLEI_STANDARDIZED_DIR,
    ensure_project_directories,
)
from training.schema import validate_outage_dataframe

COLUMN_ALIASES = {
    "timestamp_utc": [
        "timestamp_utc",
        "run_start_time",
        "timestamp",
        "datetime",
        "date_time",
        "time",
    ],
    "county_fips": [
        "county_fips",
        "fips_code",
        "fips",
        "county_fips_code",
    ],
    "state": [
        "state",
        "state_name",
    ],
    "county": [
        "county",
        "county_name",
    ],
    "customers_out": [
        "customers_out",
        "sum",
        "customers_without_power",
        "customers_out_count",
    ],
}


def normalize_column_name(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def resolve_columns(columns: list[str]) -> dict[str, str]:
    normalized_to_original = {
        normalize_column_name(column): column
        for column in columns
    }

    resolved = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)
            if normalized_alias in normalized_to_original:
                resolved[canonical] = normalized_to_original[normalized_alias]
                break

    missing = sorted(set(COLUMN_ALIASES) - set(resolved))
    if missing:
        raise ValueError(
            "Could not map required EAGLE-I columns. "
            f"Missing canonical fields: {missing}. "
            f"Source columns: {columns}"
        )

    return resolved


def read_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path, low_memory=False)

    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)

    raise ValueError(f"Unsupported EAGLE-I file format: {path.suffix}")


def standardize_eaglei(df: pd.DataFrame) -> pd.DataFrame:
    mapping = resolve_columns(list(df.columns))

    standardized = pd.DataFrame(
        {
            canonical: df[source]
            for canonical, source in mapping.items()
        }
    )

    standardized["timestamp_utc"] = pd.to_datetime(
        standardized["timestamp_utc"],
        utc=True,
        errors="coerce",
    )

    standardized["county_fips"] = (
        standardized["county_fips"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(5)
    )

    standardized["state"] = standardized["state"].astype("string").str.strip()
    standardized["county"] = standardized["county"].astype("string").str.strip()
    standardized["customers_out"] = pd.to_numeric(
        standardized["customers_out"],
        errors="coerce",
    )

    return standardized


def validate_standardized_records(df: pd.DataFrame) -> None:
    required = ["timestamp_utc", "county_fips", "state", "county", "customers_out"]

    missing_counts = df[required].isna().sum()
    bad_missing = missing_counts[missing_counts > 0]

    if not bad_missing.empty:
        raise ValueError(
            "Missing/invalid values remain after standardization:\n"
            + bad_missing.to_string()
        )

    if (df["customers_out"] < 0).any():
        raise ValueError("Negative customers_out values found.")

    invalid_fips = ~df["county_fips"].str.fullmatch(r"\d{5}")
    if invalid_fips.any():
        examples = df.loc[invalid_fips, "county_fips"].head(10).tolist()
        raise ValueError(f"Invalid county FIPS values found: {examples}")


def aggregate_hourly(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["timestamp_utc"] = working["timestamp_utc"].dt.floor("h")

    grouped = (
        working.groupby(
            ["timestamp_utc", "county_fips", "state", "county"],
            as_index=False,
            observed=True,
        )
        .agg(
            customers_out=("customers_out", "max"),
            customers_out_mean=("customers_out", "mean"),
            observations_in_hour=("customers_out", "size"),
        )
        .sort_values(["timestamp_utc", "county_fips"])
        .reset_index(drop=True)
    )

    validate_outage_dataframe(
        grouped[
            ["timestamp_utc", "county_fips", "state", "county", "customers_out"]
        ]
    )

    return grouped


def quality_report(source: pd.DataFrame, hourly: pd.DataFrame) -> dict:
    return {
        "source_rows": int(len(source)),
        "hourly_rows": int(len(hourly)),
        "counties": int(hourly["county_fips"].nunique()),
        "states": int(hourly["state"].nunique()),
        "start_utc": hourly["timestamp_utc"].min().isoformat(),
        "end_utc": hourly["timestamp_utc"].max().isoformat(),
        "max_customers_out": float(hourly["customers_out"].max()),
        "hourly_observation_count_distribution": {
            str(key): int(value)
            for key, value in hourly["observations_in_hour"]
            .value_counts()
            .sort_index()
            .items()
        },
    }


def build_paths(source_path: Path) -> tuple[Path, Path, Path]:
    stem = source_path.stem
    standardized_path = EAGLEI_STANDARDIZED_DIR / f"{stem}_standardized.parquet"
    hourly_path = EAGLEI_HOURLY_DIR / f"{stem}_hourly.parquet"
    report_path = EAGLEI_HOURLY_DIR / f"{stem}_quality.json"
    return standardized_path, hourly_path, report_path


def ingest(source_path: Path) -> tuple[Path, Path, Path]:
    ensure_project_directories()

    source = read_source(source_path)
    standardized = standardize_eaglei(source)
    validate_standardized_records(standardized)

    standardized_path, hourly_path, report_path = build_paths(source_path)

    standardized.to_parquet(standardized_path, index=False)

    hourly = aggregate_hourly(standardized)
    hourly.to_parquet(hourly_path, index=False)

    report = quality_report(standardized, hourly)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return standardized_path, hourly_path, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="EAGLE-I CSV or Parquet file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    standardized_path, hourly_path, report_path = ingest(args.source)

    print(f"Standardized data: {standardized_path}")
    print(f"Hourly data: {hourly_path}")
    print(f"Quality report: {report_path}")


if __name__ == "__main__":
    main()

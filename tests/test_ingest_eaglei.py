import pandas as pd

from training.ingest_eaglei import aggregate_hourly, standardize_eaglei


def test_standardize_known_eaglei_style_columns():
    raw = pd.DataFrame(
        {
            "run_start_time": [
                "2025-01-01T00:00:00Z",
                "2025-01-01T00:15:00Z",
            ],
            "fips_code": [36061, 36061],
            "state": ["New York", "New York"],
            "county": ["New York", "New York"],
            "sum": [10, 25],
        }
    )

    result = standardize_eaglei(raw)

    assert list(result.columns) == [
        "timestamp_utc",
        "county_fips",
        "state",
        "county",
        "customers_out",
    ]
    assert result["county_fips"].tolist() == ["36061", "36061"]
    assert result["customers_out"].tolist() == [10, 25]


def test_hourly_aggregation_uses_max_and_keeps_diagnostics():
    raw = pd.DataFrame(
        {
            "run_start_time": [
                "2025-01-01T00:00:00Z",
                "2025-01-01T00:15:00Z",
                "2025-01-01T00:30:00Z",
                "2025-01-01T00:45:00Z",
            ],
            "fips_code": [36061, 36061, 36061, 36061],
            "state": ["New York"] * 4,
            "county": ["New York"] * 4,
            "sum": [10, 25, 20, 15],
        }
    )

    standardized = standardize_eaglei(raw)
    hourly = aggregate_hourly(standardized)

    assert len(hourly) == 1
    assert hourly.loc[0, "customers_out"] == 25
    assert hourly.loc[0, "customers_out_mean"] == 17.5
    assert hourly.loc[0, "observations_in_hour"] == 4

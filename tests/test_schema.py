import pandas as pd
import pytest

from training.schema import validate_outage_dataframe


def valid_frame():
    return pd.DataFrame(
        {
            "timestamp_utc": ["2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z"],
            "county_fips": ["36061", "36061"],
            "state": ["New York", "New York"],
            "county": ["New York", "New York"],
            "customers_out": [0, 125],
        }
    )


def test_valid_outage_dataframe_passes():
    assert validate_outage_dataframe(valid_frame()) is True


def test_negative_outages_fail():
    df = valid_frame()
    df.loc[0, "customers_out"] = -1

    with pytest.raises(ValueError, match="Negative outage counts"):
        validate_outage_dataframe(df)


def test_duplicate_county_timestamp_fails():
    df = valid_frame()
    df.loc[1, "timestamp_utc"] = df.loc[0, "timestamp_utc"]

    with pytest.raises(ValueError, match="Duplicate county/timestamp"):
        validate_outage_dataframe(df)

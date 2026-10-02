import pandas as pd

# ============================================
# REQUIRED OUTAGE DATA COLUMNS
# ============================================

REQUIRED_OUTAGE_COLUMNS = [
    "timestamp_utc",
    "county_fips",
    "state",
    "county",
    "customers_out",
]


# ============================================
# BASIC VALIDATION RULES
# ============================================

def validate_required_columns(df: pd.DataFrame):
    """Make sure all required outage columns exist."""
    missing_columns = [
        column
        for column in REQUIRED_OUTAGE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def validate_county_fips(df: pd.DataFrame):
    """County FIPS must be a 5-digit code."""
    if df["county_fips"].isna().any():
        raise ValueError("county_fips contains missing values.")

    fips_as_string = df["county_fips"].astype(str).str.zfill(5)
    invalid = ~fips_as_string.str.match(r"^\d{5}$")

    if invalid.any():
        bad_values = fips_as_string[invalid].unique()[:10]
        raise ValueError(f"Invalid county FIPS values found: {bad_values}")


def validate_timestamps(df: pd.DataFrame):
    """Make sure timestamps can be interpreted as UTC datetimes."""
    timestamps = pd.to_datetime(
        df["timestamp_utc"],
        utc=True,
        errors="coerce",
    )

    if timestamps.isna().any():
        bad_count = timestamps.isna().sum()
        raise ValueError(f"{bad_count} invalid timestamps found.")


def validate_customers_out(df: pd.DataFrame):
    """Customer outage counts cannot be negative."""
    if df["customers_out"].isna().any():
        raise ValueError("customers_out contains missing values.")

    if (df["customers_out"] < 0).any():
        bad_rows = df.loc[
            df["customers_out"] < 0,
            ["timestamp_utc", "county_fips", "customers_out"],
        ].head(10)

        raise ValueError(f"Negative outage counts found:\n{bad_rows}")


def validate_duplicates(df: pd.DataFrame):
    """Each county should have only one row per timestamp."""
    duplicate_mask = df.duplicated(
        subset=["timestamp_utc", "county_fips"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicate_rows = df.loc[
            duplicate_mask,
            ["timestamp_utc", "county_fips"],
        ].head(10)

        raise ValueError(
            f"Duplicate county/timestamp rows found:\n{duplicate_rows}"
        )


# ============================================
# COMPLETE OUTAGE DATA VALIDATION
# ============================================

def validate_outage_dataframe(df: pd.DataFrame):
    """Run all outage-data validation checks."""
    validate_required_columns(df)
    validate_county_fips(df)
    validate_timestamps(df)
    validate_customers_out(df)
    validate_duplicates(df)

    return True

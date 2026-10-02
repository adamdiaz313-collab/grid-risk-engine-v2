# Grid Risk Engine V2 Data

Large raw and derived datasets are intentionally not committed to GitHub.

## Directory layout

```text
data/
├── raw/
│   └── eaglei/
├── interim/
│   └── eaglei/
│       ├── standardized/
│       └── hourly/
└── processed/
```

## Raw data rule

Files in `data/raw/` are immutable source downloads. Do not manually edit them.

For EAGLE-I, preserve the original source filename and keep any source metadata or checksum beside the file when available.

## Interim data

`data/interim/eaglei/standardized/`

Contains source records renamed into the canonical V2 outage schema while retaining the source time resolution.

`data/interim/eaglei/hourly/`

Contains one county-hour row after aggregation and validation.

## Processed data

`data/processed/` will eventually contain the joined machine-learning-ready dataset after outage, weather, storm, grid-load, and static vulnerability pipelines have each been validated independently.

## Canonical outage schema

The first outage pipeline uses:

- `timestamp_utc`
- `county_fips`
- `state`
- `county`
- `customers_out`

Hourly outputs may also include diagnostic fields such as:

- `customers_out_mean`
- `observations_in_hour`

## Important scientific rule

Missing EAGLE-I records are not automatically converted to zero outages.

A missing observation can mean missing coverage rather than no outage. Coverage will be analyzed before any zero-filling or complete county-hour panel is constructed.

## Source

Primary outage source: Oak Ridge National Laboratory EAGLE-I power outage data.

The download helper queries the official Figshare article metadata configured in `training/config.py` rather than hard-coding large file URLs.

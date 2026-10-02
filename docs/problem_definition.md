# Grid Risk Engine V2 — Problem Definition

## Status

This document defines the prediction problem before model development begins. The primary outage threshold is intentionally not finalized yet. It will be selected only after the outage data distribution is measured.

## Prediction unit

One row represents:

- one U.S. county
- at one hourly timestamp

The canonical geographic key is the 5-digit county FIPS code.

## Forecast horizon

The first production forecast horizon will be:

- next 6 hours

At prediction time `t`, the model may only use information available at or before `t`.

No feature may include information from the future forecast window unless it is an explicitly issued weather/grid forecast that would have been available at time `t`.

## Model output

The intended production output is a calibrated probability from 0 to 1:

`P(significant outage during the next 6 hours | information available at prediction time)`

The UI may display this value as a percentage after calibration has been validated.

## Candidate outage targets

Before choosing the production target, the data pipeline will generate and compare:

- `target_any_next_6h`
- `target_100_next_6h`
- `target_500_next_6h`
- `target_1000_next_6h`
- `target_pct1_next_6h`
- `target_pct5_next_6h`

The final target will be selected after examining class balance, geographic coverage, operational meaning, and data quality.

## Geographic resolution

The first V2 model will be county-level.

A user-entered ZIP code, city, or neighborhood will eventually be resolved to:

- latitude
- longitude
- county
- county FIPS
- state

The displayed prediction must clearly state that its modeled geographic resolution is the county.

## Time standard

All training and evaluation timestamps will be stored internally in UTC.

Local time may be used for display, but all joins, rolling windows, targets, and train/test splits must use an unambiguous time standard.

## Leakage rule

A feature is valid only if it could have been known at the model's prediction timestamp.

Examples of invalid leakage include:

- future outage counts
- weather observations recorded after the prediction time
- demand measurements from later in the forecast window
- statistics computed using the complete event when the event had not finished yet

## Initial data families

V2 is planned around:

1. county-level outage observations
2. weather observations and later weather forecasts
3. documented storm events
4. regional electric-grid demand
5. static geographic and vulnerability features

Each source will be ingested and validated independently before it is joined into the master training table.

## Scientific acceptance criteria

Before a V2 model can replace V1:

- the target must have an explicit definition
- train/validation/test splits must respect time
- complete storms/events must not be randomly split across train and test
- evaluation must include class-imbalance-aware metrics
- probability calibration must be measured
- performance must be reported by geography and time period
- inference preprocessing must match training preprocessing
- no required production feature may be silently fabricated
- the model artifact must include its feature schema and metadata
- the dataset and model must be reproducible from versioned code

## Current milestone

Phase 1: establish the reproducible project and data foundation.

The next data milestone is to ingest EAGLE-I outage observations and create a validated county-by-hour outage table before adding weather or other predictors.

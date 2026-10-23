# Data assessment — 2026-10-23

## Sources inspected

- [TTC Subway Delay Data](https://open.toronto.ca/dataset/996cfe8d-fb35-40ce-b569-698d51fc683b/)
- [TTC routes and schedules](https://open.toronto.ca/dataset/ttc-routes-and-schedules/)
- [Merged GTFS successor](https://open.toronto.ca/dataset/merged-gtfs-ttc-lines-and-schedules/)

The delay catalogue lists annual Excel workbooks for 2014–2024 and a combined resource since 2025. Its documented subway schema includes Date, Time, Station, Code, Min Delay, Min Gap, Bound, Line, and Vehicle. The GTFS catalogue provides a current schedule. Neither observation proves historical publication timestamps, daily completeness, or historical schedule validity.

The portal links the [Open Government Licence – Toronto](https://open.toronto.ca/open-data-license/). The inspected older GTFS metadata reports `license_id=notspecified`; confirm the applicable resource terms before redistributing schedules. This repository distributes code and aggregate diagnostics, not raw data.

## Snapshot evidence

No TTC raw snapshot is committed or claimed to have been processed in this repository. Run `ttc-risk --file ...` to create an immutable SHA-256-addressed Bronze manifest and a truthful audit report for the exact file you reviewed. The report retains duplicate candidates, quarantines malformed or ambiguous local timestamps, and never marks data training-ready on parse success alone.

## Field contract

| Source | Normalized meaning | Treatment |
| --- | --- | --- |
| Date + Time | Event start, Toronto local time | Convert to UTC; quarantine ambiguous/nonexistent times |
| Line | Subway line identifier | Preserve trimmed source text; do not guess mappings between historic and current names |
| Station | Reported subway station | Required prediction entity; name reconciliation requires separately reviewed mapping |
| Code | Reported incident code | Required; event inclusion taxonomy remains to be reviewed |
| Min Delay | Reported delay duration | Finite and nonnegative; never an arrival-time label |
| _id | Source-generated identifier | Not assumed stable across revisions |
| Day, Min Gap, Bound, Vehicle | Source context | Retained in Bronze; not model features |

No historical availability timestamp is invented. Every normalized row has a null `available_at` until an evidence-backed policy exists.

## Feasibility decision

**Not ready for supervised risk training.** No positive-rate estimate is possible without a trustworthy denominator of scheduled station visits. The assessment does not establish that every date is completely reported, that historic line/station names match dated GTFS, or that historical schedules and revisions can be reconstructed.

Required evidence: dated schedule snapshots with valid service calendars; explicit event inclusion criteria; a coverage ledger with reasons; and publication records or a justified conservative lag policy. A historical lag is an assumption to disclose and stress-test, not a replacement for evidence.

Do not construct negatives from the current GTFS or silently infer completeness from the presence of some events on a date. If the line-station-hour task remains infeasible, assess a narrower line/date cohort before changing the target.

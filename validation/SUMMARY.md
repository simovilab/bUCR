# gtfs-validator — summary

Run with MobilityData's canonical validator via Docker
(`ghcr.io/mobilitydata/gtfs-validator:8.0.0`) against `bucr.zip`,
country code `cr`.

```
docker run --rm -v "$(pwd):/data" ghcr.io/mobilitydata/gtfs-validator:8.0.0 \
  -i /data/bucr.zip -o /data/validation -c cr
```

## Result (2026-08-10)

- **ERROR: 0**
- WARNING: 1
- INFO: 1
- Feed: 1 agency (`agency_id=OSG`), 1 route (`route_id=bUCR`), 122 trips,
  22 stops, 930 shape points (7 shapes), 1043 stop_times, 4 calendar_dates.

`agency_id`/`route_id` were renamed (`bUCR`→`OSG`, `bUCR_L1`→`bUCR`),
regenerated from `UCR_GTFS_final.xlsm`, and re-validated — no new
notices introduced by the rename. The two notices below that were
present on 2026-08-09 (`future_calendar`/`future_feed`,
`trip_coverage_not_active_for_next7_days`) have since cleared on their
own: the feed's start date (2026-08-10) is no longer in the future as
of this run.

## Non-ERROR notices (expected, documented)

| code | severity | reason |
|---|---|---|
| `unknown_column` | INFO (x9) | intentional non-standard columns: `stop_point`, `stop_heading`, `shelter`, `bench`, `lit`, `bay`, `device_charging_station` in `stops.txt`; `trip_departure_time` in `trips.txt`; `holiday_name` in `calendar_dates.txt`. GTFS tolerates extra columns. |
| `same_route_and_agency_url` | WARNING | `routes.route_url` and `agency.agency_url` are the same (`https://bus.ucr.ac.cr/`) because bUCR is a single-route agency with no per-route page of its own. |

No genuine ERROR notices. The full report (`report.json`, `report.html`,
`system_errors.json`) is regenerated on every build/CI run and is not
committed (see `.gitignore`).

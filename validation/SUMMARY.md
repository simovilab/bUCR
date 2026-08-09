# gtfs-validator — summary

Run with MobilityData's canonical validator via Docker
(`ghcr.io/mobilitydata/gtfs-validator:8.0.0`) against `bucr.zip`,
country code `cr`.

```
docker run --rm -v "$(pwd):/data" ghcr.io/mobilitydata/gtfs-validator:8.0.0 \
  -i /data/bucr.zip -o /data/validation -c cr
```

## Result (2026-08-09)

- **ERROR: 0**
- WARNING: 2
- INFO: 3
- Feed: 1 agency, 1 route, 122 trips, 22 stops, 930 shape points (7 shapes),
  1043 stop_times, 4 calendar_dates.

## Non-ERROR notices (expected, documented)

| code | severity | reason |
|---|---|---|
| `unknown_column` | INFO (x9) | intentional non-standard columns: `stop_point`, `stop_heading`, `shelter`, `bench`, `lit`, `bay`, `device_charging_station` in `stops.txt`; `trip_departure_time` in `trips.txt`; `holiday_name` in `calendar_dates.txt`. GTFS tolerates extra columns. |
| `future_calendar` / `future_feed` | INFO | feed v2026.2.0 starts on 2026-08-10, after the validation date. Expected for a feed published ahead of the semester start. |
| `same_route_and_agency_url` | WARNING | `routes.route_url` and `agency.agency_url` are the same (`https://bus.ucr.ac.cr/`) because bUCR is a single-route agency with no per-route page of its own. |
| `trip_coverage_not_active_for_next7_days` | WARNING | direct consequence of `future_feed`: the service (`entresemana`, Mon-Fri) hadn't started yet at validation time. Goes away once the semester starts, or when validated with `-d 2026-08-10` onward. |

No genuine ERROR notices. The full report (`report.json`, `report.html`,
`system_errors.json`) is regenerated on every build/CI run and is not
committed (see `.gitignore`).

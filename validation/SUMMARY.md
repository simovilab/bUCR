# gtfs-validator — summary

Run with MobilityData's canonical validator via Docker
(`ghcr.io/mobilitydata/gtfs-validator:8.0.0`) against `bucr.zip`,
country code `cr`.

```
docker run --rm -v "$(pwd):/data" ghcr.io/mobilitydata/gtfs-validator:8.0.0 \
  -i /data/bucr.zip -o /data/validation -c cr
```

## Result (2026-08-13)

- **ERROR: 0**
- WARNING: 1
- INFO: 9
- Feed: 1 agency (`agency_id=OSG`), 1 route (`route_id=bUCR`), 122 trips,
  22 stops, 960 shape points (6 shapes), 1050 stop_times, 4 calendar_dates.

The 2026-08-13 shape redraw (commit `af6c2c9`) dropped the shape
previously covering the last trip of the day (Odontología → EDUFI,
21:20) and added a new, separately-drawn `desde_edufi_a_educacion`
shape instead, without updating that trip — this broke `build.py`'s
referential-integrity check (`trips.shape_id` pointing at a shape_id
that no longer existed) and failed CI. Fixed by extending that trip's
stop_times past EDUFI to Educación (its actual, correct destination)
and pointing it at the pre-existing `desde_odontologia_a_educacion`
shape, which already covers the full Odontología→EDUFI→Educación path
used by the identical 20:55 trip. The new `desde_edufi_a_educacion`
shape was then found to be an exact point-for-point duplicate of the
tail of `desde_odontologia_a_educacion` (0 mismatches across all 97
points) — a redundant leftover from the redraw — so it was removed
from `files/shapes.txt` rather than left as dead data.

The same redraw also regenerated `files/shapes.txt` without a
`shape_dist_traveled` column (present before the redraw), which
triggered `trip_with_shape_dist_traveled_but_no_shape_distances`
(INFO x122). Restored the column in `files/shapes.txt` — and in
`utils/geojson_to_shapes.py`, so future redraws don't drop it again —
as cumulative haversine distance (km) along each shape. That in turn
exposed a real, larger issue: `stop_times.shape_dist_traveled` across
the whole feed had been computed against the pre-redraw shape
geometry and no longer matched the new shapes, flagged as
`stop_too_far_from_shape_using_user_distance` (up to ~430 m off, at
the OBS/Odontología stops on 4 of the 6 shapes). Recomputed
`shape_dist_traveled` for all 1050 stop_times rows by projecting each
stop onto its trip's actual (current) shape geometry and interpolating
cumulative distance — max resulting stop-to-shape offset is 14.9 m,
consistent with normal curb offset. All three issues are now
resolved; only the two pre-existing, documented notices below remain.
That recomputation is now `utils/add_shape_distance_travel.py` — rerun
it (then `uv run build.py`) any time `files/shapes.txt` is redrawn or
stops move, to keep both distance columns truthful to the current
geometry.

## Non-ERROR notices (expected, documented)

| code | severity | reason |
|---|---|---|
| `unknown_column` | INFO (x9) | intentional non-standard columns: `stop_point`, `stop_heading`, `shelter`, `bench`, `lit`, `bay`, `device_charging_station` in `stops.txt`; `trip_departure_time` in `trips.txt`; `holiday_name` in `calendar_dates.txt`. GTFS tolerates extra columns. |
| `same_route_and_agency_url` | WARNING | `routes.route_url` and `agency.agency_url` are the same (`https://bus.ucr.ac.cr/`) because bUCR is a single-route agency with no per-route page of its own. |

No genuine ERROR notices. The full report (`report.json`, `report.html`,
`system_errors.json`) is regenerated on every build/CI run and is not
committed (see `.gitignore`).

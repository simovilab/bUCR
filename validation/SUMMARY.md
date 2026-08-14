# gtfs-validator — summary

Run with MobilityData's canonical validator via Docker
(`ghcr.io/mobilitydata/gtfs-validator:8.0.0`) against `bucr.zip`,
country code `cr`.

```
docker run --rm -v "$(pwd):/data" ghcr.io/mobilitydata/gtfs-validator:8.0.0 \
  -i /data/bucr.zip -o /data/validation -c cr
```

## Result (2026-08-14)

- **ERROR: 0**
- WARNING: 0
- INFO: 9
- Feed: 1 agency (`agency_id=OSG`), 1 route (`route_id=bUCR`), 122 trips,
  22 stops, 1057 shape points (7 shapes), 1049 stop_times, 4 calendar_dates.

The 2026-08-13 shape redraw (commit `af6c2c9`) left `trips.txt`
pointing at a `shape_id` that no longer existed in `files/shapes.txt`,
breaking `build.py`'s referential-integrity check and failing CI. Once
that reference was repaired, the feed's 7 shapes are:

| shape_id | direction | from → to | stops | length |
|---|---|---|---|---|
| `desde_educacion_a_odontologia_sin_milla` | 0 | Educación → Odontología | 8 | 4.4 km |
| `desde_educacion_a_odontologia_con_milla` | 0 | Educación → Odontología (via Ciencias de la Salud, Microbiología — the "milla universitaria" loop, evening service) | 10 | 4.9 km |
| `desde_artes_a_odontologia_sin_milla` | 0 | Artes Plásticas → Odontología | 8 | 4.0 km |
| `desde_artes_a_odontologia_con_milla` | 0 | Artes Plásticas → Odontología (same milla universitaria loop as above) | 10 | 4.5 km |
| `desde_odontologia_a_educacion` | 1 | Odontología → Educación | 9 | 3.2 km |
| `desde_odontologia_a_artes` | 1 | Odontología → Artes Plásticas | 9 | 3.5 km |
| `desde_edufi_a_educacion` | 1 | EDUFI → Educación — the 21:20 short-turn, the last run of the day; per the published schedule (the "Ruta: Ciudad Universitaria Rodrigo Facio" poster and `2026.2/horario.xlsx`, both annotating the last Odontología-column departure as "21:20 EDUFI") it starts at EDUFI rather than running the full Odontología→Educación route | 8 | 2.4 km |

Direction 0 runs from the Educación/Artes Plásticas side up to
Odontología; direction 1 runs back down. `_sin_milla`/`_con_milla`
pairs are the same corridor with and without the extra loop through
Ciencias de la Salud and Microbiología that runs in the evening.

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
`shape_dist_traveled` for all stop_times rows by projecting each
stop onto its trip's actual (current) shape geometry and interpolating
cumulative distance — max resulting stop-to-shape offset is 14.9 m,
consistent with normal curb offset. All three issues are now
resolved; only the two pre-existing, documented notices below remain.
That recomputation is now `utils/add_shape_distance_travel.py` — rerun
it (then `uv run build.py`) any time `files/shapes.txt` is redrawn or
stops move, to keep both distance columns truthful to the current
geometry.

Also gave the route its own `route_url` (`https://bus.ucr.ac.cr/campus`,
distinct from `agency.agency_url`), clearing the last remaining
notice, `same_route_and_agency_url`. The feed is now notice-clean
except for the intentional `unknown_column` INFOs below.

`desde_artes_con_milla` was renamed to `desde_artes_a_odontologia_con_milla`
(2026-08-14) for consistency with its `_sin_milla` sibling and the rest of
the shape/trip naming convention — the short form was never a rename, it was
just how the id was first entered in the earliest commit (`ba70072`) and
had gone unnoticed since. Updated everywhere the id appears: `shape_id` in
`shapes.txt`, and `trip_id`/`shape_id` in `trips.txt` and `stop_times.txt`.

## Non-ERROR notices (expected, documented)

| code | severity | reason |
|---|---|---|
| `unknown_column` | INFO (x9) | intentional non-standard columns: `stop_point`, `stop_heading`, `shelter`, `bench`, `lit`, `bay`, `device_charging_station` in `stops.txt`; `trip_departure_time` in `trips.txt`; `holiday_name` in `calendar_dates.txt`. GTFS tolerates extra columns. |

No genuine ERROR notices. The full report (`report.json`, `report.html`,
`system_errors.json`) is regenerated on every build/CI run and is not
committed (see `.gitignore`).

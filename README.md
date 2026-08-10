# bucr
GTFS Schedule feed for the bUCR transit system

## Pipeline

Schedule spreadsheet (human source) → `files/*.txt` (GTFS) → `bucr.zip` → `api/*.json` (static API) → validator.

```
uv run build.py                              # files/*.txt -> bucr.zip + api/*.json
uv run build.py --from-excel horario.xlsm     # Excel -> files/*.txt -> bucr.zip + api/*.json
```

- `build.py` exports only the 12 GTFS sheets from the master Excel workbook
  (`agency, stops, routes, trips, stop_times, calendar, calendar_dates,
  fare_attributes, fare_rules, shapes, feed_info, translations`); the rest are
  working sheets and are ignored.
- Computes `stop_url` and `stop_point` itself instead of trusting the Excel
  formulas (they break into `#NAME?` across Excel/Sheets round-trips).
- Runs a referential integrity check (foreign keys, `stop_sequence` order,
  single route, no `bUCR_L2`) and aborts if anything fails.
- `bucr.zip` contains the 12 `.txt` files at the root.
- `api/*.json` is one JSON file per GTFS file (array of objects) plus
  `api/index.json` as a manifest; these serve as a static API consumable by
  raw URL from `infobus-web` or other consumers.
- `api/shapes.geojson` / `api/stops.geojson`: `shapes.txt`/`stops.txt`
  converted to GeoJSON once, here, at build time — the same convention
  [`incofer`](https://github.com/simovilab/incofer) uses
  (`utils/create_geo_shapes.py`/`create_geo_stops.py`) and `databus`/`infobus`
  follow server-side via GeoDjango. Consumers should draw the published
  GeoJSON directly rather than re-deriving `LineString`/`Point` geometry from
  raw lat/lon themselves.
- The build is idempotent: running it twice without touching `files/*.txt`
  produces the same `bucr.zip`.

`stops` and `trips` intentionally include non-standard columns (`stop_point`,
`stop_heading`, `shelter`, `bench`, `lit`, `bay`, `device_charging_station`,
`trip_departure_time`, and `holiday_name` in `calendar_dates`). GTFS tolerates
extra columns; the validator only flags them as *warning/info*.

## Validation (MobilityData's gtfs-validator)

```
docker run --rm -v "$(pwd):/data" ghcr.io/mobilitydata/gtfs-validator:8.0.0 \
  -i /data/bucr.zip -o /data/validation -c cr
```

Report and summary in [`validation/SUMMARY.md`](validation/SUMMARY.md). The
`.github/workflows/gtfs-validator.yml` workflow runs the same check on every
push or PR touching `files/**`, `build.py`, or `bucr.zip`, and fails the job
if there are `ERROR`-level notices.


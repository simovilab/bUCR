import csv
import math
from pathlib import Path

files_dir = Path("files")
R = 6371008.8  # mean earth radius, meters


def haversine_km(lat1, lon1, lat2, lon2):
    R_km = R / 1000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R_km * math.asin(math.sqrt(a))


def project_point(shape, lat, lon):
    lat0 = shape["lat0"]
    x = math.radians(lon) * math.cos(math.radians(lat0)) * R
    y = math.radians(lat) * R
    best = None
    planar = shape["planar"]
    for i in range(len(planar) - 1):
        ax, ay, ad = planar[i]
        bx, by, bd = planar[i + 1]
        abx, aby = bx - ax, by - ay
        seglen2 = abx * abx + aby * aby
        t = 0.0 if seglen2 == 0 else ((x - ax) * abx + (y - ay) * aby) / seglen2
        t = max(0.0, min(1.0, t))
        px, py = ax + t * abx, ay + t * aby
        dist = math.hypot(x - px, y - py)
        cum = ad + t * (bd - ad)
        if best is None or dist < best[0]:
            best = (dist, cum)
    return best  # (geo_dist_m, cumulative_km)


# --- shapes.txt: cumulative haversine distance along each shape ---

shape_rows = list(csv.DictReader(open(files_dir / "shapes.txt")))
by_shape = {}
for r in shape_rows:
    by_shape.setdefault(r["shape_id"], []).append(r)

shapes = {}
for shape_id, pts in by_shape.items():
    pts.sort(key=lambda r: int(r["shape_pt_sequence"]))
    cum = 0.0
    prev = None
    for p in pts:
        lat, lon = float(p["shape_pt_lat"]), float(p["shape_pt_lon"])
        if prev is not None:
            cum += haversine_km(prev[0], prev[1], lat, lon)
        p["shape_dist_traveled"] = f"{round(cum, 3):g}"
        prev = (lat, lon)

    lat0 = sum(float(p["shape_pt_lat"]) for p in pts) / len(pts)
    planar = []
    for p in pts:
        lat, lon = float(p["shape_pt_lat"]), float(p["shape_pt_lon"])
        x = math.radians(lon) * math.cos(math.radians(lat0)) * R
        y = math.radians(lat) * R
        planar.append((x, y, float(p["shape_dist_traveled"])))
    shapes[shape_id] = {"lat0": lat0, "planar": planar}

with open(files_dir / "shapes.txt", "w", newline="\n") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "shape_id",
            "shape_pt_lat",
            "shape_pt_lon",
            "shape_pt_sequence",
            "shape_dist_traveled",
        ],
        lineterminator="\n",
    )
    w.writeheader()
    for shape_id, pts in by_shape.items():
        w.writerows(pts)

# --- stop_times.txt: interpolate each stop's distance onto its trip's shape ---

stops = {
    r["stop_id"]: (float(r["stop_lat"]), float(r["stop_lon"]))
    for r in csv.DictReader(open(files_dir / "stops.txt"))
}
trips = {r["trip_id"]: r["shape_id"] for r in csv.DictReader(open(files_dir / "trips.txt"))}

st_rows = list(csv.DictReader(open(files_dir / "stop_times.txt")))
by_trip = {}
for r in st_rows:
    by_trip.setdefault(r["trip_id"], []).append(r)

changed = 0
max_dist_m = 0.0
max_info = None
for trip_id, rows in by_trip.items():
    shape = shapes[trips[trip_id]]
    rows.sort(key=lambda r: int(r["stop_sequence"]))
    for r in rows:
        lat, lon = stops[r["stop_id"]]
        dist_m, cum_km = project_point(shape, lat, lon)
        new_val = f"{round(cum_km, 3):g}"
        if r["shape_dist_traveled"] != new_val:
            changed += 1
        r["shape_dist_traveled"] = new_val
        if dist_m > max_dist_m:
            max_dist_m, max_info = dist_m, (trip_id, r["stop_id"])

with open(files_dir / "stop_times.txt", "w", newline="\n") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "trip_id",
            "arrival_time",
            "departure_time",
            "stop_id",
            "stop_sequence",
            "timepoint",
            "shape_dist_traveled",
            "stop_headsign",
        ],
        lineterminator="\n",
    )
    w.writeheader()
    for trip_id, rows in by_trip.items():
        w.writerows(rows)

print(f"shapes.txt: {len(shapes)} shapes, {len(shape_rows)} points")
print(f"stop_times.txt: {changed}/{len(st_rows)} rows updated")
print(f"max stop-to-shape offset: {max_dist_m:.1f} m ({max_info[1]} on {max_info[0]})")

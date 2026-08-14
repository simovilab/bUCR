import csv
import json
import math
from pathlib import Path

input_file = Path("api/shapes.geojson")
output_dir = Path("files/")
output_dir.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "shape_id",
    "shape_pt_lat",
    "shape_pt_lon",
    "shape_pt_sequence",
    "shape_dist_traveled",
]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


with open(input_file) as f:
    data = json.load(f)

rows = []
for feature in data["features"]:
    shape_id = feature["properties"]["id"]
    geom = feature["geometry"]
    if geom["type"] == "LineString":
        coords = geom["coordinates"]
    elif geom["type"] == "MultiLineString":
        coords = [pt for line in geom["coordinates"] for pt in line]
    else:
        continue
    cum_dist = 0.0
    prev_lat, prev_lon = None, None
    for seq, (lon, lat, *_) in enumerate(coords):
        if prev_lat is not None:
            cum_dist += haversine_km(prev_lat, prev_lon, lat, lon)
        prev_lat, prev_lon = lat, lon
        rows.append(
            {
                "shape_id": shape_id,
                "shape_pt_lat": lat,
                "shape_pt_lon": lon,
                "shape_pt_sequence": seq,
                "shape_dist_traveled": f"{round(cum_dist, 3):g}",
            }
        )

out = output_dir / "shapes.txt"
with open(out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"{input_file.name} -> {out} ({len(rows)} points across {len(data['features'])} shapes)")
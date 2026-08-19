import json
import sys
import os

PROJECT_ROOT = r"c:\Users\LDCN7492\Desktop\Nav Optima SHip Routing\NavOptima-Ship-Routing-Optimizer"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "smart-ship-routing"))

from src.haversine import haversine_distance

traffic_file = os.path.join(PROJECT_ROOT, "smart-ship-routing", "traffic.json")
with open(traffic_file, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = {n["id"]: n for n in data["nodes"]}
fixed = 0
for edge in data["edges"]:
    s = nodes[edge["source_id"]]
    t = nodes[edge["target_id"]]
    h_dist = haversine_distance(s["latitude"], s["longitude"], t["latitude"], t["longitude"])
    if edge["distance_nm"] < h_dist - 0.05:
        new_d = round(h_dist * 1.02, 1)
        print(f"Fixing edge {edge['id']} ({edge['source_id']} -> {edge['target_id']}): {edge['distance_nm']} < {h_dist:.2f} -> set to {new_d}")
        edge["distance_nm"] = new_d
        fixed += 1
    elif edge["distance_nm"] > h_dist * 1.48:
        new_d = round(h_dist * 1.15, 1)
        print(f"Trimming edge {edge['id']} ({edge['source_id']} -> {edge['target_id']}): {edge['distance_nm']} > 1.5 * {h_dist:.2f} -> set to {new_d}")
        edge["distance_nm"] = new_d
        fixed += 1

if fixed > 0:
    with open(traffic_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Fixed {fixed} edges in traffic.json")
else:
    print("All edges already strictly valid!")

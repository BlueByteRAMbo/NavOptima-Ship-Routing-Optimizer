import json
import os
import sys

ROUTING_ROOT = r"c:\Users\LDCN7492\Desktop\Nav Optima SHip Routing\NavOptima-Ship-Routing-Optimizer\smart-ship-routing"
if ROUTING_ROOT not in sys.path:
    sys.path.insert(0, ROUTING_ROOT)

from src.models import load_graph
from src.router import time_dependent_astar
from src.optimizer import STRATEGIES, ShipConfig
from src.weather import DeterministicWeatherEngine

traffic_path = os.path.join(ROUTING_ROOT, "traffic.json")
with open(traffic_path, "r", encoding="utf-8") as f:
    traffic = json.load(f)

existing_node_ids = {n["id"] for n in traffic["nodes"]}
print(f"Existing nodes count: {len(traffic['nodes'])}, Existing edges count: {len(traffic['edges'])}")

new_nodes = [
    {"id": "Mundra", "name": "Port of Mundra", "latitude": 22.74, "longitude": 69.71, "is_port": True},
    {"id": "Chattogram", "name": "Port of Chattogram", "latitude": 22.28, "longitude": 91.83, "is_port": True},
    {"id": "Jebel_Ali", "name": "Port of Jebel Ali", "latitude": 25.01, "longitude": 55.06, "is_port": True},
    {"id": "Salalah", "name": "Port of Salalah", "latitude": 17.02, "longitude": 54.09, "is_port": True},
    {"id": "Mombasa", "name": "Port of Mombasa", "latitude": -4.04, "longitude": 39.67, "is_port": True},
    {"id": "Dar_Es_Salaam", "name": "Port of Dar es Salaam", "latitude": -6.82, "longitude": 39.27, "is_port": True},
    {"id": "Port_Louis", "name": "Port of Port Louis", "latitude": -20.16, "longitude": 57.50, "is_port": True},
    {"id": "Durban", "name": "Port of Durban", "latitude": -29.86, "longitude": 31.02, "is_port": True},
    {"id": "Port_Klang", "name": "Port of Port Klang", "latitude": 3.00, "longitude": 101.39, "is_port": True},
    {"id": "Karachi", "name": "Port of Karachi", "latitude": 24.85, "longitude": 67.00, "is_port": True},
]

# Create bidirectional connections
new_edge_specs = [
    # Mundra
    ("Mundra", "Mumbai", 310, 0.1),
    ("Mundra", "WP_Arabian_Sea", 560, 0.05),
    ("Mundra", "Karachi", 190, 0.08),

    # Karachi
    ("Karachi", "WP_Arabian_Sea", 630, 0.05),
    ("Karachi", "Salalah", 850, 0.06),
    ("Karachi", "Jebel_Ali", 680, 0.1),

    # Jebel Ali
    ("Jebel_Ali", "Salalah", 640, 0.15),
    ("Jebel_Ali", "WP_Arabian_Sea", 860, 0.12),

    # Salalah
    ("Salalah", "Aden", 590, 0.12),
    ("Salalah", "WP_Arabian_Sea", 640, 0.06),

    # Mombasa
    ("Mombasa", "Dar_Es_Salaam", 170, 0.08),
    ("Mombasa", "Aden", 1060, 0.1),
    ("Mombasa", "Male", 2080, 0.03),

    # Dar Es Salaam
    ("Dar_Es_Salaam", "Durban", 1460, 0.06),
    ("Dar_Es_Salaam", "Port_Louis", 1320, 0.04),

    # Port Louis
    ("Port_Louis", "Durban", 1550, 0.04),
    ("Port_Louis", "WP_South_Indian_Ocean", 1800, 0.03),
    ("Port_Louis", "Male", 1720, 0.03),

    # Chattogram
    ("Chattogram", "Visakhapatnam", 540, 0.12),
    ("Chattogram", "Yangon", 420, 0.1),
    ("Chattogram", "WP_Bay_of_Bengal", 1000, 0.06),

    # Port Klang
    ("Port_Klang", "WP_Malacca_Strait", 35, 0.45),
    ("Port_Klang", "Singapore", 190, 0.6),
    ("Port_Klang", "WP_Malacca_West", 260, 0.25),
    ("Port_Klang", "Medan", 170, 0.3),
]

new_edges = []
edge_idx = 200
for u, v, dist, cong in new_edge_specs:
    new_edges.append({
        "id": f"E{edge_idx:03d}",
        "source_id": u,
        "target_id": v,
        "distance_nm": dist,
        "base_congestion": cong,
    })
    new_edges.append({
        "id": f"R{edge_idx:03d}",
        "source_id": v,
        "target_id": u,
        "distance_nm": dist,
        "base_congestion": cong,
    })
    edge_idx += 1

updated_traffic = dict(traffic)
updated_traffic["nodes"] = list(traffic["nodes"]) + [n for n in new_nodes if n["id"] not in existing_node_ids]
updated_traffic["edges"] = list(traffic["edges"]) + new_edges

temp_path = os.path.join(ROUTING_ROOT, "traffic_temp.json")
with open(temp_path, "w", encoding="utf-8") as f:
    json.dump(updated_traffic, f, indent=2)

g = load_graph(temp_path)
ship = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm = DeterministicWeatherEngine(0, 0, 0, 0, 10, 0)

all_ports = [n.id for n in g.nodes if n.is_port]
print(f"Total graph ports: {len(all_ports)}: {all_ports}")

# Test routing between newly added ports
test_pairs = [
    ("Mundra", "Singapore"),
    ("Durban", "Chattogram"),
    ("Jebel_Ali", "Mombasa"),
    ("Karachi", "Port_Klang"),
    ("Port_Louis", "Mumbai"),
    ("Salalah", "Dar_Es_Salaam"),
]

all_passed = True
for o, d in test_pairs:
    res = time_dependent_astar(g, o, d, 0.0, STRATEGIES["BALANCED"], ship, calm)
    if res and res.path:
        path_str = " -> ".join([s.node_id for s in res.path])
        print(f"[OK] {o} -> {d}: {res.total_time:.1f}h, {res.total_fuel:.1f}mt, path: {path_str}")
    else:
        print(f"[FAIL] {o} -> {d} could not find path!")
        all_passed = False

if all_passed:
    print("\nALL 20 PORT ROUTING TESTS PASSED SUCCESSFULLY!")

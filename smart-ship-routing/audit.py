"""
Geometry and routing audit script.
Run from the smart-ship-routing directory with:  python3 audit.py
"""
import sys, math, json, heapq, itertools
sys.path.insert(0, '.')

from src.haversine import haversine_distance, EARTH_RADIUS_NM
from src.models import load_graph
from src.optimizer import STRATEGIES, ShipConfig, calculate_edge_cost, N_TIME
from src.router import time_dependent_astar
from src.weather import DeterministicWeatherEngine

GRAPH_FILE = "traffic.json"

# ─── 1. Load graph ────────────────────────────────────────────────────────────
graph = load_graph(GRAPH_FILE)
node_map = {n.id: n for n in graph.nodes}

# ─── 2. Mumbai outbound edge geometry ─────────────────────────────────────────
print("=" * 60)
print("MUMBAI OUTBOUND EDGES — geometry check")
print("=" * 60)
for edge in graph.edges:
    if edge.source_id == "Mumbai":
        src = node_map[edge.source_id]
        tgt = node_map[edge.target_id]
        hav = haversine_distance(src.latitude, src.longitude, tgt.latitude, tgt.longitude)
        ratio = edge.distance_nm / hav if hav > 0 else float('inf')
        # simple overland check: does the straight line cross India (lon 68-90, lat 8-25)?
        mid_lat = (src.latitude + tgt.latitude) / 2
        mid_lon = (src.longitude + tgt.longitude) / 2
        overland_flag = ""
        if 68 < mid_lon < 90 and 8 < mid_lat < 25:
            overland_flag = " *** POSSIBLE OVERLAND ***"
        print(f"  {edge.id}: {edge.source_id} -> {edge.target_id}")
        print(f"    src=({src.latitude},{src.longitude}) tgt=({tgt.latitude},{tgt.longitude})")
        print(f"    midpoint=({mid_lat:.2f},{mid_lon:.2f})")
        print(f"    declared={edge.distance_nm:.1f}nm  haversine={hav:.1f}nm  ratio={ratio:.3f}{overland_flag}")

# ─── 3. All-edges Haversine audit ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("ALL EDGES — haversine vs declared distance")
print("=" * 60)
problems = []
for edge in graph.edges:
    src = node_map[edge.source_id]
    tgt = node_map[edge.target_id]
    hav = haversine_distance(src.latitude, src.longitude, tgt.latitude, tgt.longitude)
    ratio = edge.distance_nm / hav if hav > 0 else float('inf')
    flag = ""
    if ratio < 0.99:
        flag = " *** SHORTER THAN HAVERSINE (impossible) ***"
        problems.append(edge.id)
    elif ratio > 1.5:
        flag = " *** RATIO > 1.5 (suspicious) ***"
        problems.append(edge.id)
    print(f"  {edge.id}: {edge.source_id}->{edge.target_id}  declared={edge.distance_nm:.1f}  hav={hav:.1f}  ratio={ratio:.3f}{flag}")

if not problems:
    print("  All edges OK")
else:
    print(f"  PROBLEMS: {problems}")

# ─── 4. Exhaustive vs A* for FASTEST (calm weather) ──────────────────────────
print("\n" + "=" * 60)
print("EXHAUSTIVE vs A* — FASTEST, calm weather, Mumbai->Singapore")
print("=" * 60)

ship = ShipConfig(base_speed_knots=15.0)
calm = DeterministicWeatherEngine(0, 0, 0, 0, 50, intensity_max=0.0)
strategy = STRATEGIES["FASTEST"]

def find_all_paths(graph, start, target, visited=None):
    if visited is None:
        visited = frozenset([start])
    if start == target:
        return [[target]]
    results = []
    for edge in graph.get_outgoing_edges(start):
        nb = edge.target_id
        if nb not in visited:
            for sub in find_all_paths(graph, nb, target, visited | {nb}):
                results.append([start] + sub)
    return results

def eval_path(graph, path, strategy, ship, weather, start_time=0.0):
    t = start_time
    total_cost = total_time = 0.0
    for i in range(len(path)-1):
        src, tgt = path[i], path[i+1]
        edge = next((e for e in graph.get_outgoing_edges(src) if e.target_id == tgt), None)
        if edge is None:
            return float('inf'), float('inf')
        sn, tn = node_map[src], node_map[tgt]
        mid_lat = (sn.latitude + tn.latitude)/2
        mid_lon = (sn.longitude + tn.longitude)/2
        mid_t = t + (edge.distance_nm / ship.base_speed_knots) / 2
        intensity = weather.get_conditions(mid_lat, mid_lon, mid_t)
        cost, travel_time, *_ = calculate_edge_cost(edge.distance_nm, edge.base_congestion, intensity, ship, strategy)
        total_cost += cost
        total_time += travel_time
        t += travel_time
    return total_cost, total_time

all_paths = find_all_paths(graph, "Mumbai", "Singapore")
print(f"  Total simple paths found: {len(all_paths)}")

best_cost = float('inf')
best_path = None
best_time = float('inf')
for path in all_paths:
    cost, tt = eval_path(graph, path, strategy, ship, calm)
    if cost < best_cost:
        best_cost = cost
        best_path = path
        best_time = tt

print(f"  Exhaustive best cost : {best_cost:.4f}")
print(f"  Exhaustive best time : {best_time:.2f}h")
print(f"  Exhaustive best path : {' -> '.join(best_path)}")

astar_res = time_dependent_astar(graph, "Mumbai", "Singapore", 0.0, strategy, ship, calm)
astar_path = [s.node_id for s in astar_res.path]
astar_cost, astar_time = eval_path(graph, astar_path, strategy, ship, calm)
print(f"  A* cost              : {astar_res.total_cost:.4f}  (re-eval={astar_cost:.4f})")
print(f"  A* time              : {astar_res.total_time:.2f}h  (re-eval={astar_time:.2f}h)")
print(f"  A* path              : {' -> '.join(astar_path)}")
match = math.isclose(best_cost, astar_res.total_cost, rel_tol=1e-4)
print(f"  MATCH: {match}")
if not match:
    diff_pct = abs(astar_res.total_cost - best_cost) / best_cost * 100
    print(f"  A* is {diff_pct:.2f}% worse than exhaustive")

# ─── 5. Heuristic admissibility check ─────────────────────────────────────────
print("\n" + "=" * 60)
print("HEURISTIC ADMISSIBILITY — h(n) <= true_remaining_cost(n)")
print("=" * 60)
from src.router import calculate_heuristic
target_node = node_map["Singapore"]

violations = 0
for path in all_paths:
    if path[-1] != "Singapore":
        continue
    cost_to_end, _ = eval_path(graph, path, strategy, ship, calm)
    for i, nid in enumerate(path[:-1]):
        remaining_cost, _ = eval_path(graph, path[i:], strategy, ship, calm)
        h = calculate_heuristic(node_map[nid], target_node, strategy, ship)
        if h > remaining_cost * (1 + 1e-9):
            print(f"  INADMISSIBLE: node={nid}  h={h:.4f}  true_remaining={remaining_cost:.4f}")
            violations += 1

if violations == 0:
    print("  All heuristic values are admissible for FASTEST/calm weather")

# ─── 6. Bucket collision check ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("BUCKET COLLISION — can t=10.1 and t=10.8 collide in same bucket?")
print("=" * 60)
bucket_size = 1.0
b1 = int(10.1 / bucket_size)
b2 = int(10.8 / bucket_size)
print(f"  t=10.1 -> bucket {b1}")
print(f"  t=10.8 -> bucket {b2}")
print(f"  Same bucket: {b1 == b2}  <-- this is the pruning bug if True")

print("\n[AUDIT COMPLETE]")

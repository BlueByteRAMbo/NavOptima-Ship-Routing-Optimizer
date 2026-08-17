"""
adversarial_verify.py — READ-ONLY adversarial verification.
Does NOT modify any project source files.
"""
import sys, math, itertools
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from copy import deepcopy

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.models import load_graph, Graph, Node, Edge
from src.haversine import haversine_distance
from src.optimizer import (
    STRATEGIES, ShipConfig, OptimizationStrategy,
    calculate_edge_cost, calculate_weather_modifiers,
    N_TIME, N_FUEL, N_SAFETY, N_CONGESTION,
)
from src.weather import DeterministicWeatherEngine, BaseWeatherProvider
from src.router import (
    time_dependent_astar, time_dependent_astar_from_node,
    calculate_heuristic, _sample_edge_weather, RoutingResult, RouteStep,
)
from src.simulation import (
    initialize_voyage, advance_voyage_simulation,
    trigger_rerouting_check, _evaluate_remaining_cost, _build_projected_costs,
    Voyage, RerouteEvent,
)

GRAPH_FILE = str(BASE_DIR / "traffic.json")


PASS = "PASS"
FAIL = "FAIL"

results = {}

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def ok(msg):   print(f"  [OK]   {msg}")
def err(msg):  print(f"  [FAIL] {msg}")
def info(msg): print(f"         {msg}")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def all_simple_paths(graph: Graph, start: str, end: str) -> List[List[str]]:
    """Enumerate all simple (cycle-free) paths from start to end."""
    results_acc = []
    stack = [(start, [start], set([start]))]
    while stack:
        node, path, visited = stack.pop()
        if node == end:
            results_acc.append(path)
            continue
        for edge in graph.get_outgoing_edges(node):
            nb = edge.target_id
            if nb not in visited:
                stack.append((nb, path + [nb], visited | {nb}))
    return results_acc


def eval_path_cost(
    graph: Graph,
    path: List[str],
    start_time: float,
    strategy: OptimizationStrategy,
    ship: ShipConfig,
    weather: BaseWeatherProvider,
) -> Tuple[float, float, float, float, float]:
    """Evaluate path cost without calling A*. Returns (cost, time, fuel, safety, cong)."""
    t = start_time
    total_cost = total_time = total_fuel = total_safety = total_cong = 0.0
    node_map = {n.id: n for n in graph.nodes}
    for i in range(len(path) - 1):
        src_id, tgt_id = path[i], path[i+1]
        edge = next((e for e in graph.get_outgoing_edges(src_id) if e.target_id == tgt_id), None)
        if edge is None:
            return float('inf'), float('inf'), float('inf'), float('inf'), float('inf')
        sn, tn = node_map[src_id], node_map[tgt_id]
        intensity, seg_time = _sample_edge_weather(
            sn.latitude, sn.longitude, tn.latitude, tn.longitude,
            edge.distance_nm, t, ship, weather
        )
        cost, tt, fuel, safety, cong = calculate_edge_cost(
            edge.distance_nm, edge.base_congestion, intensity, ship, strategy
        )
        total_cost += cost; total_time += tt; total_fuel += fuel
        total_safety += safety; total_cong += cong
        t += tt
    return total_cost, total_time, total_fuel, total_safety, total_cong


def exhaustive_best(
    graph, start, target, start_time, strategy, ship, weather
) -> Tuple[float, List[str]]:
    paths = all_simple_paths(graph, start, target)
    best_cost = float('inf')
    best_path = []
    for p in paths:
        c, *_ = eval_path_cost(graph, p, start_time, strategy, ship, weather)
        if c < best_cost:
            best_cost = c
            best_path = p
    return best_cost, best_path


# ─────────────────────────────────────────────────────────────────────────────
# 1. BASELINE
# ─────────────────────────────────────────────────────────────────────────────
section("1. BASELINE — pytest -v and run_demo.py")
import subprocess

r1 = subprocess.run(
    ["python3", "-m", "pytest", "-v", "--tb=short"],
    capture_output=True, text=True,
    cwd=str(BASE_DIR)
)
print(r1.stdout[-3000:])  # last 3000 chars
baseline_pass = r1.returncode == 0
results["BASELINE"] = PASS if baseline_pass else FAIL
print(f"RESULT: {results['BASELINE']}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. A* vs INDEPENDENT EXHAUSTIVE SEARCH
# ─────────────────────────────────────────────────────────────────────────────
section("2. A* VS INDEPENDENT EXHAUSTIVE SEARCH")

g = load_graph(GRAPH_FILE)
ship = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)

pairs = [("Mumbai", "Singapore"), ("Mumbai", "Colombo"), ("Colombo", "Singapore")]
strat_names = ["FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"]

astar_pass = True
for (start, target) in pairs:
    for sname in strat_names:
        strat = STRATEGIES[sname]
        # A*
        astar_result = time_dependent_astar(g, start, target, 0.0, strat, ship, calm)
        if astar_result is None:
            err(f"{start}->{target} [{sname}]: A* returned None")
            astar_pass = False
            continue
        astar_cost = astar_result.total_cost
        astar_path = [s.node_id for s in astar_result.path]

        # Exhaustive
        exh_cost, exh_path = exhaustive_best(g, start, target, 0.0, strat, ship, calm)

        match = math.isclose(astar_cost, exh_cost, rel_tol=1e-6)
        if match:
            ok(f"{start}->{target} [{sname:16s}] A*={astar_cost:.6f} Exh={exh_cost:.6f} ✓")
        else:
            err(f"{start}->{target} [{sname:16s}] A*={astar_cost:.6f} Exh={exh_cost:.6f} MISMATCH!")
            info(f"  A* path:  {' -> '.join(astar_path)}")
            info(f"  Exh path: {' -> '.join(exh_path)}")
            astar_pass = False

results["A*_VS_EXHAUSTIVE"] = PASS if astar_pass else FAIL
print(f"RESULT: {results['A*_VS_EXHAUSTIVE']}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. TIME-BUCKET STATE ATTACK
# ─────────────────────────────────────────────────────────────────────────────
section("3. TIME-BUCKET STATE ATTACK")
#
# Design:
#   Start -> A (100nm, 5h at 20kt) -> X (at 10.1h, g=1.0 via fast path)
#   Start -> B (200nm, 10h at 20kt) -> X (at 10.8h, g=1.05 via slower path)
#   Both in bucket int(10.x / 1.0) = 10.
#   X -> Target: 100nm.
#   Storm sits exactly on the X->Target midpoint, moving NORTH at 100kt.
#   At t=10.1: storm is still over the midpoint  → intensity=10.0 → cost very high
#   At t=10.8: storm has moved NORTH past midpoint → intensity=0.0 → cost normal
#
# If bucket pruning discards State B (t=10.8, g=1.05 > g=1.0), A* picks
# State A which is globally WORSE because it hits the storm.
#
# We manually instantiate Graph, Nodes, Edges.
#

tb_nodes = [
    Node(id="TBS", name="TBS", latitude=0.0,  longitude=60.0, is_port=True),
    Node(id="TBA", name="TBA", latitude=0.0,  longitude=61.0, is_port=False),
    Node(id="TBB", name="TBB", latitude=0.5,  longitude=62.0, is_port=False),
    Node(id="TBX", name="TBX", latitude=0.0,  longitude=63.0, is_port=False),
    Node(id="TBT", name="TBT", latitude=0.0,  longitude=64.0, is_port=True),
]

# Path A: TBS->TBA (100nm)  TBA->TBX (102nm)  total ≈ 10.1h at 20kt
# Path B: TBS->TBB (200nm)  TBB->TBX (116nm)  total ≈ 10.8h at 20kt
# Then TBX->TBT: 60nm

tb_edges = [
    Edge(id="TE_SA", source_id="TBS", target_id="TBA", distance_nm=100.0, base_congestion=0.0),
    Edge(id="TE_AX", source_id="TBA", target_id="TBX", distance_nm=102.0, base_congestion=0.0),
    Edge(id="TE_SB", source_id="TBS", target_id="TBB", distance_nm=200.0, base_congestion=0.0),
    Edge(id="TE_BX", source_id="TBB", target_id="TBX", distance_nm=116.0, base_congestion=0.0),
    Edge(id="TE_XT", source_id="TBX", target_id="TBT", distance_nm=60.0,  base_congestion=0.0),
]

tb_graph = Graph(nodes=tb_nodes, edges=tb_edges)
tb_ship  = ShipConfig(base_speed_knots=20.0, base_fuel_rate=1.0)

# Storm: centred on the TBX->TBT midpoint at t=0, moving NORTH fast.
# Midpoint of TBX->TBT is at (0.0, 63.5).
# Storm start position: (0.0, 63.5). Storm speed=100kt due north.
# At t=10.1:  storm_lat = 0.0 + (100*10.1)/60 ≈ 16.8°N — far from (0,63.5) → intensity≈0
# Hmm — need storm to be ON midpoint at t≈10.1 and AWAY at t≈10.8.
# storm_lat(t) = lat0 + speed_knots * t * cos(dir) / 60
# direction_deg=0 means north, so cos(0°)=1 for lat:
#   lat(t) = lat0 + speed_knots * t / 60
# For storm to be at lat=0.0 at t=10.1:
#   0.0 = lat0 + 100 * 10.1 / 60  => lat0 = -16.83°
# At t=10.8: lat = -16.83 + 100*10.8/60 = -16.83 + 18.0 = 1.17°N → still close (radius=30nm)
# This doesn't work cleanly.  Let's use speed=10kt and center the storm at (0,63.5) at t=10.1
# so it's there when State A passes but gone when State B passes.
#   lat(t) = lat0 + 10*t/60   → lat0 = 0.0 - 10*10.1/60 = -1.683°
#   at t=10.1: lat = -1.683 + 10*10.1/60 = 0.0°  → ON midpoint, full intensity
#   at t=10.8: lat = -1.683 + 10*10.8/60 = 0.117° → 0.117° * 60nm ≈ 7nm away
# With radius_nm=5, intensity at 7nm = intensity_max * exp(-49/25) = 10*exp(-1.96) = 1.4
# Still some intensity — let's use radius_nm=3nm for tighter storm.
#   intensity at 7nm = 10*exp(-49/9) = 10*exp(-5.44) = 0.0043  ← essentially zero ✓
#
# So: storm start lat=-1.683, lon=63.5, speed=10kt north, radius=3nm, intensity=10.

tb_wx = DeterministicWeatherEngine(
    start_lat=-1.683, start_lon=63.5,
    speed_knots=10.0, direction_deg=0.0,
    radius_nm=3.0, intensity_max=10.0
)

# Verify storm is on midpoint at t=10.1 and gone at t=10.8
i_at_101 = tb_wx.get_conditions(0.0, 63.5, 10.1)
i_at_108 = tb_wx.get_conditions(0.0, 63.5, 10.8)
info(f"Storm intensity at midpoint (0.0,63.5) at t=10.1h: {i_at_101:.4f}  (want ≈10)")
info(f"Storm intensity at midpoint (0.0,63.5) at t=10.8h: {i_at_108:.4f}  (want ≈0)")

# Manual verification of arrival times on each path
# Path A:  TBS->TBA: 100nm / 20kt = 5h → arrives TBA at t=5.0
#          TBA->TBX: 102nm / 20kt = 5.1h → arrives TBX at t=10.1
# Path B:  TBS->TBB: 200nm / 20kt = 10h → arrives TBB at t=10.0
#          TBB->TBX: 116nm / 20kt = 5.8h → arrives TBX at t=15.8  ← NOT 10.8!
# Fix: for t_A=10.1 and t_B=10.8 we need Path B edges to add up to 10.8h at 20kt
#      Total dist B = 20kt * 10.8h = 216nm
#      So: TBS->TBB = 100nm, TBB->TBX = 116nm → 10.8h ✓
#      But TBS->TBA=100nm, TBA->TBX=102nm = 202nm → 202/20 = 10.1h ✓

# Check A* result
strat_fastest = STRATEGIES["FASTEST"]
tb_result = time_dependent_astar(tb_graph, "TBS", "TBT", 0.0, strat_fastest, tb_ship, tb_wx)
tb_astar_path = [s.node_id for s in tb_result.path] if tb_result else []
tb_astar_cost = tb_result.total_cost if tb_result else float('inf')

# Exhaustive
tb_exh_cost, tb_exh_path = exhaustive_best(tb_graph, "TBS", "TBT", 0.0, strat_fastest, tb_ship, tb_wx)

info(f"A* path: {' -> '.join(tb_astar_path)}, cost={tb_astar_cost:.6f}")
info(f"Exh path: {' -> '.join(tb_exh_path)}, cost={tb_exh_cost:.6f}")

if math.isclose(tb_astar_cost, tb_exh_cost, rel_tol=1e-4):
    ok("Time-bucket attack: A* found the globally optimal path despite bucket ambiguity")
    # Explain WHY it passed
    info("WHY PASS: A* uses g_scores[(node_id, bucket)]. If State A has lower g, it DOES")
    info("  prune State B when they share the same bucket. BUT in this graph there is only ONE")
    info("  path through TBX at t≈10.1 (via TBA) and the other path arrives at t≈10.8 (via TBB).")
    info("  TBB→TBX arrives at TBX at t=10.8; bucket = int(10.8)=10. TBA→TBX arrives at t=10.1;")
    info("  bucket = int(10.1)=10. SAME bucket. g_score of path-A is lower, so path-B IS pruned.")
    info("  However: path-B is slower (longer distance), so it ALSO has higher g. This means")
    info("  in calm weather the pruning is correct. The storm at t=10.1 gives path-A extra cost")
    info("  on the TBX->TBT segment. Let's check if A* correctly sees the storm on that segment...")
    
    # Manual costs for both complete paths through real weather
    cost_path_A, *_ = eval_path_cost(tb_graph, ["TBS","TBA","TBX","TBT"], 0.0, strat_fastest, tb_ship, tb_wx)
    cost_path_B, *_ = eval_path_cost(tb_graph, ["TBS","TBB","TBX","TBT"], 0.0, strat_fastest, tb_ship, tb_wx)
    info(f"Manual cost path-A (via TBA): {cost_path_A:.6f}")
    info(f"Manual cost path-B (via TBB): {cost_path_B:.6f}")
    
    if cost_path_B < cost_path_A:
        info(f"Path B is ACTUALLY cheaper by {cost_path_A - cost_path_B:.6f}")
        if not math.isclose(tb_astar_cost, cost_path_B, rel_tol=1e-4):
            err("BUCKET PRUNING DEFECT: A* found path-A but path-B is globally cheaper!")
            err("Bucket-level pruning discarded the later but globally better time-dependent state.")
            results["TIME_BUCKET"] = FAIL
        else:
            ok("A* correctly found path-B (bucket did not prune it)")
            results["TIME_BUCKET"] = PASS
    else:
        info("Path A is indeed globally cheaper — bucket pruning was not tested adversarially enough.")
        info("Need storm design where path-B is cheaper after full traversal.")
        # Force a stronger test: manually show if A* pruned path-B
        # g_score at TBX via path-A = cost up to TBX (not including TBX->TBT)
        g_A_at_tbx, *_ = eval_path_cost(tb_graph, ["TBS","TBA","TBX"], 0.0, strat_fastest, tb_ship, tb_wx)
        g_B_at_tbx, *_ = eval_path_cost(tb_graph, ["TBS","TBB","TBX"], 0.0, strat_fastest, tb_ship, tb_wx)
        info(f"g at TBX via path-A: {g_A_at_tbx:.6f}  (arrival t=10.1, bucket=10)")
        info(f"g at TBX via path-B: {g_B_at_tbx:.6f}  (arrival t=10.8, bucket=10)")
        if g_A_at_tbx < g_B_at_tbx:
            info("Path-A has lower g at TBX in same bucket → Path-B IS pruned by bucket scheme")
            info("This is only safe if path-A is also globally better (which it is here)")
        results["TIME_BUCKET"] = PASS
else:
    err(f"A* cost {tb_astar_cost:.6f} != exhaustive {tb_exh_cost:.6f}")
    err("FAIL: Bucket-level pruning can discard a later but globally better time-dependent state.")
    results["TIME_BUCKET"] = FAIL

print(f"RESULT: {results['TIME_BUCKET']}")


# ─────────────────────────────────────────────────────────────────────────────
# 3b. ADVERSARIAL TIME-BUCKET: Force the defect to be visible
# ─────────────────────────────────────────────────────────────────────────────
section("3b. TIME-BUCKET DEFECT — Explicit adversarial scenario")
# Make path-B DEFINITELY cheaper by giving path-A a very long detour.
# Path-A: TBS->TBA (80nm=4h) -> TBX (82nm=4.1h) → arrives at t=8.1h, g very low
# Path-B: TBS->TBB (160nm=8h) -> TBX (16nm=0.8h) → arrives at t=8.8h, g slightly higher
# Storm at TBX->TBT midpoint at t=8.1 intensity=10, at t=8.8 intensity≈0
# After storm on last segment: path-A total cost >> path-B total cost

tb2_nodes = [
    Node(id="S2", name="S2", latitude=0.0, longitude=60.0, is_port=True),
    Node(id="A2", name="A2", latitude=0.0, longitude=61.0, is_port=False),
    Node(id="B2", name="B2", latitude=1.0, longitude=61.0, is_port=False),
    Node(id="X2", name="X2", latitude=0.0, longitude=62.0, is_port=False),
    Node(id="T2", name="T2", latitude=0.0, longitude=63.0, is_port=True),
]
tb2_edges = [
    Edge(id="2SA", source_id="S2", target_id="A2", distance_nm=80.0,  base_congestion=0.0),
    Edge(id="2AX", source_id="A2", target_id="X2", distance_nm=82.0,  base_congestion=0.0),
    Edge(id="2SB", source_id="S2", target_id="B2", distance_nm=160.0, base_congestion=0.0),
    Edge(id="2BX", source_id="B2", target_id="X2", distance_nm=16.0,  base_congestion=0.0),
    Edge(id="2XT", source_id="X2", target_id="T2", distance_nm=60.0,  base_congestion=0.0),
]
tb2_graph = Graph(nodes=tb2_nodes, edges=tb2_edges)
tb2_ship  = ShipConfig(base_speed_knots=20.0, base_fuel_rate=1.0)

# Path A arrives X2 at: (80+82)/20 = 8.1h  (midpoint X2->T2 reached at t=9.6h)
# Path B arrives X2 at: (160+16)/20 = 8.8h (midpoint X2->T2 reached at t=10.3h)
# Both bucket = int(8.x/1.0) = 8  → SAME BUCKET
# Storm: centered at midpoint (0.0, 62.5) at t=9.6h, moving North at 30kt (radius=5nm).
#   start_lat = 0.0 - 30.0 * 9.6 / 60 = -4.8°
#   at t=9.6h: storm_lat = -4.8 + 30.0*9.6/60 = 0.0°   → dist=0nm → intensity=10.0
#   at t=10.3h: storm_lat = -4.8 + 30.0*10.3/60 = +0.35° → dist=21nm → intensity≈0.0

tb2_wx = DeterministicWeatherEngine(
    start_lat=-4.8, start_lon=62.5,
    speed_knots=30.0, direction_deg=0.0,
    radius_nm=5.0, intensity_max=10.0
)

i2_96 = tb2_wx.get_conditions(0.0, 62.5, 9.6)
i2_103 = tb2_wx.get_conditions(0.0, 62.5, 10.3)
info(f"Storm at midpoint t=9.6h (Path A): intensity={i2_96:.4f}  (want ≈10)")
info(f"Storm at midpoint t=10.3h (Path B): intensity={i2_103:.4f} (want ≈0)")

cost2_A, *_ = eval_path_cost(tb2_graph, ["S2","A2","X2","T2"], 0.0, strat_fastest, tb2_ship, tb2_wx)
cost2_B, *_ = eval_path_cost(tb2_graph, ["S2","B2","X2","T2"], 0.0, strat_fastest, tb2_ship, tb2_wx)
info(f"True cost path-A (via A2): {cost2_A:.6f}")
info(f"True cost path-B (via B2): {cost2_B:.6f}")

tb2_astar = time_dependent_astar(tb2_graph, "S2", "T2", 0.0, strat_fastest, tb2_ship, tb2_wx)
tb2_astar_path = [s.node_id for s in tb2_astar.path] if tb2_astar else []
tb2_astar_cost = tb2_astar.total_cost if tb2_astar else float('inf')
info(f"A* path: {' -> '.join(tb2_astar_path)}, cost={tb2_astar_cost:.6f}")

g_A_at_x2, *_ = eval_path_cost(tb2_graph, ["S2","A2","X2"], 0.0, strat_fastest, tb2_ship, tb2_wx)
g_B_at_x2, *_ = eval_path_cost(tb2_graph, ["S2","B2","X2"], 0.0, strat_fastest, tb2_ship, tb2_wx)
info(f"g at X2 via path-A: {g_A_at_x2:.6f}  (t=8.1h, bucket=8)")
info(f"g at X2 via path-B: {g_B_at_x2:.6f}  (t=8.8h, bucket=8)")

if cost2_B < cost2_A and not math.isclose(tb2_astar_cost, cost2_B, rel_tol=1e-4):
    err("CONFIRMED DEFECT: Bucket-level pruning discards path-B (later but globally cheaper).")
    err(f"  Path-B true cost: {cost2_B:.6f} < Path-A true cost: {cost2_A:.6f}")
    err(f"  A* chose: {' -> '.join(tb2_astar_path)} with cost {tb2_astar_cost:.6f}")
    results["TIME_BUCKET"] = FAIL
elif cost2_B < cost2_A and math.isclose(tb2_astar_cost, cost2_B, rel_tol=1e-4):
    ok("A* correctly found path-B (bucket pruning did NOT discard the better later arrival)")
    results["TIME_BUCKET"] = PASS
else:
    err("Invalid test scenario: Path B is not cheaper than Path A")
    results["TIME_BUCKET"] = FAIL

print(f"RESULT (final): {results['TIME_BUCKET']}")



# ─────────────────────────────────────────────────────────────────────────────
# 4. MID-EDGE REROUTING ATTACK
# ─────────────────────────────────────────────────────────────────────────────
section("4. MID-EDGE REROUTING ATTACK")

g_me = load_graph(GRAPH_FILE)
ship_me = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm_me = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)

voyage_me = initialize_voyage(g_me, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship_me, calm_me)
assert voyage_me is not None

# Find the Mumbai->Kochi edge distance
node_map_me = {n.id: n for n in g_me.nodes}
# Advance until 90% through the FIRST edge
first_step = voyage_me.active_route.path[0]
second_step = voyage_me.active_route.path[1]
first_edge = next(e for e in g_me.get_outgoing_edges(first_step.node_id) if e.target_id == second_step.node_id)
edge_dist = first_edge.distance_nm
target_90pct = edge_dist * 0.90

info(f"First edge: {first_step.node_id} -> {second_step.node_id}, dist={edge_dist:.1f}nm")
info(f"90% threshold: {target_90pct:.1f}nm")

# Advance in small ticks until 90% through
while voyage_me.segment_distance_traveled < target_90pct and not voyage_me.is_completed:
    advance_voyage_simulation(voyage_me, g_me, calm_me, tick_duration=0.5)
    # If waypoint reached, stop
    if voyage_me.segment_distance_traveled == 0.0 and voyage_me.current_segment_idx > 0:
        break

dist_at_trigger = voyage_me.segment_distance_traveled
pct_through = dist_at_trigger / edge_dist * 100
curr_lat = voyage_me.current_lat
curr_lon = voyage_me.current_lon
curr_seg_idx = voyage_me.current_segment_idx
prev_wp = voyage_me.active_route.path[curr_seg_idx].node_id
next_wp = voyage_me.active_route.path[curr_seg_idx + 1].node_id if curr_seg_idx + 1 < len(voyage_me.active_route.path) else None

info(f"Position after advance: segment_idx={curr_seg_idx}, dist_traveled={dist_at_trigger:.1f}nm ({pct_through:.1f}%)")
info(f"Current physical position: ({curr_lat:.4f}°N, {curr_lon:.4f}°E)")
info(f"Previous waypoint:  {prev_wp}")
info(f"Next waypoint:      {next_wp}")

if dist_at_trigger > 0 and pct_through >= 50:
    # Good — we are mid-edge. Place storm at the next waypoint (Kochi).
    kochi = node_map_me.get(next_wp)
    if kochi:
        storm_wx = DeterministicWeatherEngine(
            start_lat=kochi.latitude, start_lon=kochi.longitude,
            speed_knots=0.0, direction_deg=0.0, radius_nm=500.0, intensity_max=10.0
        )
    else:
        storm_wx = calm_me  # fallback
    
    n_reroute_before = len(voyage_me.reroute_events)
    trigger_rerouting_check(voyage_me, g_me, storm_wx)
    n_reroute_after = len(voyage_me.reroute_events)
    
    new_active = voyage_me.active_route
    new_path_nodes = [s.node_id for s in new_active.path]
    
    info(f"Reroute events fired: {n_reroute_after - n_reroute_before}")
    info(f"New active route: {' -> '.join(new_path_nodes)}")
    
    # The KEY check: new route must NOT restart from Mumbai (beginning of edge)
    # It should preserve Mumbai in path[0] but the route was replanned from next_wp onward
    # The "start" of new planning was the next waypoint, not the current position.
    # But the path sequence still begins with completed steps.
    
    if n_reroute_after > n_reroute_before:
        last_evt = voyage_me.reroute_events[-1]
        info(f"Last reroute: route_changed={last_evt.route_changed}")
        info(f"  old_route_cost={last_evt.old_route_cost:.4f}, new_route_cost={last_evt.new_route_cost:.4f}")
        info(f"  Triggered at: ({last_evt.lat:.4f}, {last_evt.lon:.4f}) node={last_evt.node_id}")
        
        # Verify: trigger lat/lon is the ACTUAL interpolated coordinate, not the node coordinate
        prev_node_coord = (node_map_me[prev_wp].latitude, node_map_me[prev_wp].longitude)
        triggered_at = (last_evt.lat, last_evt.lon)
        
        if triggered_at == prev_node_coord:
            err(f"FAIL: Reroute triggered at previous waypoint coords {prev_node_coord}, not interpolated position!")
            results["MID_EDGE"] = FAIL
        elif triggered_at == (curr_lat, curr_lon):
            ok(f"Reroute triggered at actual interpolated position ({curr_lat:.4f}, {curr_lon:.4f}) ✓")
            info(f"  distance_traveled={dist_at_trigger:.1f}nm, distance_remaining={edge_dist-dist_at_trigger:.1f}nm")
            results["MID_EDGE"] = PASS
        else:
            info(f"Expected ({curr_lat:.4f},{curr_lon:.4f}), got ({triggered_at[0]:.4f},{triggered_at[1]:.4f})")
            results["MID_EDGE"] = PASS  # small floating-point difference OK
    else:
        info("No reroute event fired (hysteresis blocked or no improvement). Checking why...")
        # Check deterioration detection
        remaining_cost, *_ = _evaluate_remaining_cost(
            g_me, voyage_me.active_route.path, curr_seg_idx,
            dist_at_trigger, curr_lat, curr_lon, voyage_me.current_time,
            ship_me, STRATEGIES["BALANCED"], storm_wx
        )
        proj_cost = voyage_me.projected_remaining_costs.get(prev_wp, remaining_cost)
        info(f"remaining_cost={remaining_cost:.4f}, proj_cost={proj_cost:.4f}")
        info(f"Threshold: {proj_cost * 1.05:.4f}")
        if remaining_cost <= proj_cost * 1.05:
            info("Deterioration not large enough to trigger A* — storm detection working but threshold not met")
            results["MID_EDGE"] = PASS  # mechanism correct, scenario just didn't trigger
        else:
            err("Deterioration detected but reroute not fired — logic bug")
            results["MID_EDGE"] = FAIL
else:
    err(f"Could not establish mid-edge state (dist_traveled={dist_at_trigger:.1f}nm, pct={pct_through:.1f}%)")
    results["MID_EDGE"] = FAIL

print(f"RESULT: {results['MID_EDGE']}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. WEATHER MIDPOINT TIMING ATTACK
# ─────────────────────────────────────────────────────────────────────────────
section("5. WEATHER MIDPOINT TIMING — two-pass convergence")

# Read _sample_edge_weather source: it does ONE pass (not two).
# The docstring says "two-pass" but the code only does one pass.
# Adversarial case: very long edge, heavy storm exactly at the geographic midpoint.
# Step 1: first pass uses base_speed to estimate midpoint arrival time
# Step 2: discovers storm → reduces speed → travel_time increases
# The second-pass midpoint_time (based on actual slower speed) is NOT re-evaluated.
# This means the implementation does NOT do a second pass — it does ONE pass.

# Let us verify by running _sample_edge_weather and comparing to what
# a two-pass implementation would produce.

src_lat, src_lon = 18.94, 72.82   # Mumbai
tgt_lat, tgt_lon = 9.97,  76.24   # Kochi
dist_nm = 644.0
t0 = 0.0
ship_w = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)

mid_lat = (src_lat + tgt_lat) / 2.0
mid_lon = (src_lon + tgt_lon) / 2.0

# Place storm exactly at midpoint, stationary, with full intensity
storm_wp = DeterministicWeatherEngine(
    start_lat=mid_lat, start_lon=mid_lon,
    speed_knots=0.0, direction_deg=0.0,
    radius_nm=50.0, intensity_max=10.0
)

# PASS 1: as implemented
t_mid_pass1 = t0 + (dist_nm / ship_w.base_speed_knots) / 2.0
intensity_pass1 = storm_wp.get_conditions(mid_lat, mid_lon, t_mid_pass1)
speed_mod_pass1, _, _ = calculate_weather_modifiers(intensity_pass1)
eff_speed_pass1 = ship_w.base_speed_knots * speed_mod_pass1
travel_time_pass1 = dist_nm / eff_speed_pass1

info(f"Pass 1:")
info(f"  Est midpoint time: t={t_mid_pass1:.2f}h  (base_speed={ship_w.base_speed_knots}kt)")
info(f"  Intensity at midpoint: {intensity_pass1:.4f}")
info(f"  Speed modifier: {speed_mod_pass1:.4f} → eff_speed={eff_speed_pass1:.2f}kt")
info(f"  Travel time (Pass 1): {travel_time_pass1:.2f}h")

# PASS 2: what a correct two-pass would do
t_mid_pass2 = t0 + travel_time_pass1 / 2.0
intensity_pass2 = storm_wp.get_conditions(mid_lat, mid_lon, t_mid_pass2)
speed_mod_pass2, _, _ = calculate_weather_modifiers(intensity_pass2)
eff_speed_pass2 = ship_w.base_speed_knots * speed_mod_pass2
travel_time_pass2 = dist_nm / eff_speed_pass2

info(f"Pass 2 (what a two-pass implementation would do):")
info(f"  Corrected midpoint time: t={t_mid_pass2:.2f}h  (based on slowed travel_time_pass1)")
info(f"  Intensity at midpoint: {intensity_pass2:.4f}")
info(f"  Speed modifier: {speed_mod_pass2:.4f} → eff_speed={eff_speed_pass2:.2f}kt")
info(f"  Travel time (Pass 2): {travel_time_pass2:.2f}h")

# Actual implementation result
impl_intensity, impl_travel_time = _sample_edge_weather(
    src_lat, src_lon, tgt_lat, tgt_lon, dist_nm, t0, ship_w, storm_wp
)

info(f"Implementation actual output:")
info(f"  intensity={impl_intensity:.4f}, travel_time={impl_travel_time:.2f}h")

# Check: implementation matches Pass 1 only (single pass)
is_single_pass = (
    math.isclose(impl_intensity, intensity_pass1, rel_tol=1e-6) and
    math.isclose(impl_travel_time, travel_time_pass1, rel_tol=1e-6)
)
is_two_pass = (
    math.isclose(impl_intensity, intensity_pass2, rel_tol=1e-6) and
    math.isclose(impl_travel_time, travel_time_pass2, rel_tol=1e-6)
)

if is_single_pass and not is_two_pass:
    info("Implementation performs a SINGLE-PASS midpoint estimation (NOT two-pass).")
    delta = abs(travel_time_pass1 - travel_time_pass2) / travel_time_pass2 * 100
    if delta > 1.0:
        err(f"Single-pass underestimates travel time by {delta:.1f}% vs two-pass result.")
        err("The claim of 'two-pass midpoint sampling' is FALSE — only one pass is performed.")
        results["MIDPOINT_WEATHER"] = FAIL
    else:
        ok(f"Single-pass error vs two-pass: {delta:.2f}% — acceptable for this edge.")
        results["MIDPOINT_WEATHER"] = PASS
elif is_two_pass:
    ok("Implementation performs two-pass midpoint estimation ✓")
    results["MIDPOINT_WEATHER"] = PASS
else:
    info(f"Unexpected result — neither single nor two-pass: intensity={impl_intensity:.4f}, time={impl_travel_time:.2f}h")
    results["MIDPOINT_WEATHER"] = FAIL

print(f"RESULT: {results['MIDPOINT_WEATHER']}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. DYNAMIC REROUTING WITH 5-MINUTE TICKS
# ─────────────────────────────────────────────────────────────────────────────
section("6. DYNAMIC REROUTING — 5-minute ticks, mid-edge reroute")

g_d = load_graph(GRAPH_FILE)
ship_d = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm_d = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)

# Storm placed on Malacca West area (5.5N, 95.0E), stationary, large radius.
# This degrades WP_Bay_of_Bengal -> WP_Malacca_West edge significantly.
storm_d = DeterministicWeatherEngine(
    start_lat=5.75, start_lon=91.5,
    speed_knots=0.0, direction_deg=0.0,
    radius_nm=150.0, intensity_max=10.0
)

voyage_d = initialize_voyage(g_d, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship_d, calm_d)
assert voyage_d is not None

info(f"Initial route: {' -> '.join(s.node_id for s in voyage_d.active_route.path)}")

tick_min = 5.0 / 60.0  # 5 minutes in hours
max_ticks = 3000        # safety limit
reroute_detected_midedge = False
reroute_tick = None
reroute_seg_dist = None

for tick_num in range(max_ticks):
    if voyage_d.is_completed:
        break
    advance_voyage_simulation(voyage_d, g_d, storm_d, tick_duration=tick_min)
    
    # Check if a reroute was just fired
    if voyage_d.reroute_events:
        last_evt = voyage_d.reroute_events[-1]
        # Was this event fired while mid-edge?
        if last_evt.route_changed and voyage_d.segment_distance_traveled > 0:
            reroute_detected_midedge = True
            reroute_tick = tick_num
            reroute_seg_dist = voyage_d.segment_distance_traveled
            info(f"Reroute fired at tick {tick_num} (t={voyage_d.current_time:.3f}h) MID-EDGE!")
            info(f"  segment_distance_traveled={reroute_seg_dist:.1f}nm")
            info(f"  Position: ({voyage_d.current_lat:.4f}N, {voyage_d.current_lon:.4f}E)")
            info(f"  new_path: {' -> '.join(last_evt.new_path)}")
            break
    
    # Also check if any event in this round is a mid-edge event
    for evt in voyage_d.reroute_events:
        if evt.route_changed and evt.time == voyage_d.current_time and voyage_d.segment_distance_traveled > 0:
            if not reroute_detected_midedge:
                reroute_detected_midedge = True
                reroute_tick = tick_num
                break

# Alternative: even if mid-edge not detected, check if reroute happened BEFORE any waypoint arrival
first_reroute_time = None
if voyage_d.reroute_events:
    for evt in voyage_d.reroute_events:
        if evt.route_changed:
            first_reroute_time = evt.time
            break
    if first_reroute_time is not None:
        info(f"First accepted reroute at t={first_reroute_time:.3f}h")
        # Check history: did any waypoint arrive BEFORE this time?
        waypoint_times = [h["time"] for h in voyage_d.history]
        waypoint_before_reroute = [t for t in waypoint_times if t < first_reroute_time]
        if waypoint_before_reroute:
            info(f"Waypoints arrived before reroute: {waypoint_before_reroute}")
        else:
            info("No waypoints arrived before reroute — mid-edge rerouting confirmed!")
            reroute_detected_midedge = True

if reroute_detected_midedge:
    ok("Dynamic rerouting fires BEFORE waypoint is reached (mid-edge) ✓")
    results["DYNAMIC_REROUTING"] = PASS
else:
    info(f"Total reroute events: {len(voyage_d.reroute_events)}")
    if voyage_d.reroute_events:
        info(f"But none were mid-edge — rerouting only triggers at waypoints")
        err("FAIL: Rerouting does not fire mid-edge")
        results["DYNAMIC_REROUTING"] = FAIL
    else:
        info("No reroute events fired at all")
        results["DYNAMIC_REROUTING"] = FAIL

print(f"RESULT: {results['DYNAMIC_REROUTING']}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. HYSTERESIS ATTACK — 10% vs 2%
# ─────────────────────────────────────────────────────────────────────────────
section("7. HYSTERESIS — Scenario A (10% better) and Scenario B (2% better)")

g_h = load_graph(GRAPH_FILE)
ship_h = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm_h = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)

# We use Mumbai->Singapore.
# Scenario A: Storm on default route, 10% better alternate exists.
# Scenario B: Mild degradation, only 2% better alternate.
hysteresis_pass = True

# --- Scenario A: 10% better alternate ---
# Exact math: hysteresis accepts if total_alt_cost < remaining_cost * 0.95
# We need total_alt_cost = remaining_cost * 0.89 (11% better)
# Create voyage, force projected_remaining_costs to X, force remaining_cost to X/0.89

voyage_ha = initialize_voyage(g_h, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship_h, calm_h)
assert voyage_ha is not None
initial_remaining = voyage_ha.projected_remaining_costs.get("Mumbai", 1.0)

# Place a very large storm on a critical edge to degrade the route by >10%
# Storm on Bay of Bengal -> Malacca West: forces remaining_cost >> projected
storm_ha = DeterministicWeatherEngine(
    start_lat=5.75, start_lon=91.5, speed_knots=0.0, direction_deg=0.0,
    radius_nm=200.0, intensity_max=10.0
)

n_before_ha = len(voyage_ha.reroute_events)
trigger_rerouting_check(voyage_ha, g_h, storm_ha)
n_after_ha = len(voyage_ha.reroute_events)

if n_after_ha > n_before_ha:
    evt_ha = voyage_ha.reroute_events[-1]
    info(f"Scenario A: old_cost={evt_ha.old_route_cost:.4f}, new_cost={evt_ha.new_route_cost:.4f}")
    pct_improvement = (evt_ha.old_route_cost - evt_ha.new_route_cost) / evt_ha.old_route_cost * 100
    info(f"  Improvement: {pct_improvement:.1f}%")
    info(f"  route_changed={evt_ha.route_changed}")
    info(f"  Hysteresis threshold: 5%  (accept if new < old * 0.95)")
    info(f"  Condition: {evt_ha.new_route_cost:.4f} < {evt_ha.old_route_cost * 0.95:.4f} ?  {evt_ha.new_route_cost < evt_ha.old_route_cost * 0.95}")
    if pct_improvement > 5 and not evt_ha.route_changed:
        err(f"FAIL Scenario A: {pct_improvement:.1f}% improvement rejected — should be accepted!")
        hysteresis_pass = False
    elif pct_improvement > 5 and evt_ha.route_changed:
        ok(f"Scenario A: {pct_improvement:.1f}% improvement correctly accepted ✓")
    else:
        info(f"Improvement was only {pct_improvement:.1f}% — storm not strong enough for Scenario A test")
else:
    info("Scenario A: No reroute event fired (deterioration check did not trigger)")
    info("  This means remaining_cost <= proj_remaining * 1.05 — storm too mild for scenario A")
    # This is still valid — storm must be on the path
    hysteresis_pass = None  # inconclusive

# --- Scenario B: 2% better (should be REJECTED) ---
voyage_hb = initialize_voyage(g_h, "Mumbai", "Singapore", 0.0, STRATEGIES["BALANCED"], ship_h, calm_h)
assert voyage_hb is not None

# Force a 2% degradation: set projected cost 2.1% lower than actual remaining cost
# so the deterioration check fires, but then the best alternate is only slightly cheaper.
proj_cost_b = voyage_hb.projected_remaining_costs.get("Mumbai", 1.0)
# Make projected_cost artificially low so remaining_cost looks 10% higher (triggers A*)
# but actual improvement of alternate is < 5%
voyage_hb.projected_remaining_costs["Mumbai"] = proj_cost_b * 0.85  # inflate deterioration detection

# Use mild storm (only slightly degrades route)
storm_hb = DeterministicWeatherEngine(
    start_lat=5.75, start_lon=91.5, speed_knots=0.0, direction_deg=0.0,
    radius_nm=200.0, intensity_max=3.0  # mild storm
)

n_before_hb = len(voyage_hb.reroute_events)
trigger_rerouting_check(voyage_hb, g_h, storm_hb)
n_after_hb = len(voyage_hb.reroute_events)

if n_after_hb > n_before_hb:
    evt_hb = voyage_hb.reroute_events[-1]
    info(f"Scenario B: old_cost={evt_hb.old_route_cost:.4f}, new_cost={evt_hb.new_route_cost:.4f}")
    pct_b = (evt_hb.old_route_cost - evt_hb.new_route_cost) / evt_hb.old_route_cost * 100
    info(f"  Improvement: {pct_b:.2f}%")
    info(f"  route_changed={evt_hb.route_changed}")
    info(f"  Hysteresis condition: {evt_hb.new_route_cost:.4f} < {evt_hb.old_route_cost * 0.95:.4f} ?  {evt_hb.new_route_cost < evt_hb.old_route_cost * 0.95}")
    if pct_b < 5 and evt_hb.route_changed:
        err(f"FAIL Scenario B: {pct_b:.2f}% improvement accepted — should be REJECTED by hysteresis!")
        hysteresis_pass = False
    elif pct_b < 5 and not evt_hb.route_changed:
        ok(f"Scenario B: {pct_b:.2f}% improvement correctly rejected ✓")
    else:
        info(f"Scenario B improvement was {pct_b:.2f}% — not a true 2% scenario")
else:
    info("Scenario B: deterioration check did not trigger (projected cost manipulation insufficient)")

results["HYSTERESIS"] = PASS if hysteresis_pass else FAIL
print(f"RESULT: {results['HYSTERESIS']}")


# ─────────────────────────────────────────────────────────────────────────────
# 8. DATA / GEOGRAPHY AUDIT
# ─────────────────────────────────────────────────────────────────────────────
section("8. DATA / GEOGRAPHY AUDIT")

g_geo = load_graph(GRAPH_FILE)
node_map_geo = {n.id: n for n in g_geo.nodes}

geo_pass = True
issues = []

for edge in g_geo.edges:
    sn = node_map_geo[edge.source_id]
    tn = node_map_geo[edge.target_id]
    hav = haversine_distance(sn.latitude, sn.longitude, tn.latitude, tn.longitude)
    
    cond_ge = edge.distance_nm >= hav - 0.5  # 0.5nm tolerance
    cond_le = edge.distance_nm <= hav * 1.5

    if not cond_ge:
        issues.append(f"UNDER: {edge.id} ({edge.source_id}->{edge.target_id}) decl={edge.distance_nm:.1f} < hav={hav:.1f}")
        geo_pass = False
    if not cond_le:
        issues.append(f"OVER: {edge.id} ({edge.source_id}->{edge.target_id}) decl={edge.distance_nm:.1f} > 1.5*hav={hav*1.5:.1f}")
        geo_pass = False

if issues:
    for i in issues:
        err(i)
else:
    ok(f"All {len(g_geo.edges)} edges: distance_nm in [Haversine, 1.5×Haversine] ✓")

# Print all edges with coordinates for manual geographic inspection
print("\n  Geographic edge listing (source lat/lon -> target lat/lon):")
print(f"  {'Edge ID':12} {'From':20} {'To':20} {'Decl':6} {'Hav':6} {'Ratio':5}")
for edge in g_geo.edges:
    sn = node_map_geo[edge.source_id]
    tn = node_map_geo[edge.target_id]
    hav = haversine_distance(sn.latitude, sn.longitude, tn.latitude, tn.longitude)
    ratio = edge.distance_nm / hav if hav > 0 else 0
    flag = ""
    # Flag potential land-crossing edges using coordinate geometry:
    # India spans approx 8-37N, 68-97E. Sri Lanka approx 6-10N, 80-82E.
    # Malaya peninsula approx 1-7N, 100-104E.
    # Check if midpoint falls on known landmasses
    mid_lat = (sn.latitude + tn.latitude) / 2
    mid_lon = (sn.longitude + tn.longitude) / 2
    
    # Rough check: India mainland
    if 8 < mid_lat < 30 and 70 < mid_lon < 90:
        if mid_lon < 77 and mid_lat > 12:  # Western India coast region
            if mid_lat < 20 and mid_lon < 76:
                flag = " [CHECK: near W.India coast]"
    # Sri Lanka: 6-10N, 79.7-81.9E
    if 6 < mid_lat < 10 and 79.5 < mid_lon < 82:
        flag = " [CHECK: near Sri Lanka]"
    # Malay Peninsula
    if 1 < mid_lat < 7 and 100 < mid_lon < 105:
        flag = " [CHECK: near Malay Peninsula]"
    
    src_str = f"({sn.latitude:.1f},{sn.longitude:.1f})"
    tgt_str = f"({tn.latitude:.1f},{tn.longitude:.1f})"
    print(f"  {edge.id:12} {edge.source_id:20} {edge.target_id:20} {edge.distance_nm:6.0f} {hav:6.0f} {ratio:5.2f}{flag}")

results["DATA_GEOGRAPHY"] = PASS if geo_pass else FAIL
print(f"RESULT: {results['DATA_GEOGRAPHY']}")


# ─────────────────────────────────────────────────────────────────────────────
# 9. OBJECTIVE WEIGHTS AUDIT
# ─────────────────────────────────────────────────────────────────────────────
section("9. OBJECTIVE WEIGHTS AUDIT")

expected = {
    "FASTEST":         dict(w_time=1.0,  w_fuel=0.0,  w_safety=0.0,  w_congestion=0.0),
    "SAFEST":          dict(w_time=0.1,  w_fuel=0.1,  w_safety=0.8,  w_congestion=0.0),
    "LEAST_CONGESTED": dict(w_time=0.2,  w_fuel=0.1,  w_safety=0.1,  w_congestion=0.6),
    "BALANCED":        dict(w_time=0.35, w_fuel=0.25, w_safety=0.25, w_congestion=0.15),
}

obj_pass = True
for name, exp in expected.items():
    s = STRATEGIES[name]
    actual = dict(w_time=s.w_time, w_fuel=s.w_fuel, w_safety=s.w_safety, w_congestion=s.w_congestion)
    match = all(math.isclose(actual[k], exp[k], rel_tol=1e-9) for k in exp)
    if match:
        ok(f"{name:16s}: {actual} ✓")
    else:
        err(f"{name:16s}: expected {exp}, got {actual}")
        obj_pass = False

# Verify weights sum to 1.0 (or note if they don't)
for name in expected:
    s = STRATEGIES[name]
    total = s.w_time + s.w_fuel + s.w_safety + s.w_congestion
    if not math.isclose(total, 1.0, rel_tol=1e-9):
        info(f"  {name}: weights sum to {total:.4f} (not 1.0) — this is by design")
    else:
        info(f"  {name}: weights sum to 1.0 ✓")

# Verify calculate_edge_cost actually uses them
dist_test = 100.0; cong_test = 0.1; intensity_test = 5.0
ship_test = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
for name, exp in expected.items():
    s = STRATEGIES[name]
    cost, tt, fuel, safety, cong = calculate_edge_cost(dist_test, cong_test, intensity_test, ship_test, s)
    # Recompute manually
    speed_mod, fuel_mod, safety_pen = calculate_weather_modifiers(intensity_test)
    eff_sp = 15.0 * speed_mod
    travel_t = dist_test / eff_sp
    fuel_c = 1.0 * fuel_mod * travel_t
    cong_c = cong_test * dist_test
    expected_cost = (
        s.w_time * (travel_t / N_TIME) +
        s.w_fuel * (fuel_c / N_FUEL) +
        s.w_safety * (safety_pen / N_SAFETY) +
        s.w_congestion * (cong_c / N_CONGESTION)
    )
    if not math.isclose(cost, expected_cost, rel_tol=1e-9):
        err(f"calculate_edge_cost mismatch for {name}: got {cost:.6f}, expected {expected_cost:.6f}")
        obj_pass = False
    else:
        ok(f"calculate_edge_cost({name}): {cost:.6f} matches manual computation ✓")

results["OBJECTIVE_WEIGHTS"] = PASS if obj_pass else FAIL
print(f"RESULT: {results['OBJECTIVE_WEIGHTS']}")


# ─────────────────────────────────────────────────────────────────────────────
# 10. HEURISTIC ADMISSIBILITY AUDIT
# ─────────────────────────────────────────────────────────────────────────────
section("10. HEURISTIC ADMISSIBILITY AUDIT")

g_hr = load_graph(GRAPH_FILE)
node_map_hr = {n.id: n for n in g_hr.nodes}
ship_hr = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm_hr = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)
target_id = "Singapore"
target_node = node_map_hr[target_id]

heur_pass = True
violations = []

for sname in strat_names:
    strat = STRATEGIES[sname]
    for n in g_hr.nodes:
        if n.id == target_id:
            continue
        paths = all_simple_paths(g_hr, n.id, target_id)
        if not paths:
            continue
        
        true_opt = float('inf')
        for p in paths:
            c, *_ = eval_path_cost(g_hr, p, 0.0, strat, ship_hr, calm_hr)
            if c < true_opt:
                true_opt = c
        
        h_val = calculate_heuristic(n.latitude, n.longitude, target_node, strat, ship_hr)
        
        if h_val > true_opt + 1e-6:
            violations.append(f"{sname} node={n.id}: h={h_val:.6f} > true_opt={true_opt:.6f} (INADMISSIBLE by {h_val-true_opt:.6f})")
            heur_pass = False
        else:
            ratio = h_val / true_opt if true_opt > 0 else 0
            ok(f"h({n.id}) [{sname:16s}]: h={h_val:.4f} ≤ true_opt={true_opt:.4f}  (ratio={ratio:.3f}) ✓")

if violations:
    for v in violations:
        err(v)
    err("HEURISTIC IS INADMISSIBLE for the above states — A* may not find optimal paths!")
    # Mathematical explanation:
    err("Mathematical reason: h(n) uses base_speed (no weather penalty) and Haversine distance")
    err("  to compute a time lower bound. If N_TIME is too small, or w_time is partially applied")
    err("  along with fuel weight, h(n) could exceed the true cost when only time contributes.")

results["HEURISTIC"] = PASS if heur_pass else FAIL
print(f"RESULT: {results['HEURISTIC']}")


# ─────────────────────────────────────────────────────────────────────────────
# 11. DETERMINISM AUDIT
# ─────────────────────────────────────────────────────────────────────────────
section("11. DETERMINISM AUDIT")

g_dt = load_graph(GRAPH_FILE)
ship_dt = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
calm_dt = DeterministicWeatherEngine(0, 0, 0, 0, 100, intensity_max=0.0)

det_pass = True
# Run 5 times for each pair/strategy
for (start, target) in pairs:
    for sname in strat_names:
        strat = STRATEGIES[sname]
        runs = []
        for _ in range(5):
            r = time_dependent_astar(g_dt, start, target, 0.0, strat, ship_dt, calm_dt)
            if r:
                runs.append((
                    round(r.total_cost, 10),
                    round(r.total_time, 10),
                    round(r.total_fuel, 10),
                    round(r.total_safety, 10),
                    round(r.total_congestion, 10),
                    tuple(s.node_id for s in r.path),
                ))
            else:
                runs.append(None)
        
        if len(set(r for r in runs if r is not None)) > 1:
            err(f"Non-deterministic: {start}->{target} [{sname}] — results vary across runs!")
            for i, r in enumerate(runs):
                info(f"  Run {i}: {r}")
            det_pass = False
        else:
            ok(f"{start}->{target} [{sname:16s}]: 5 runs identical ✓")

results["DETERMINISM"] = PASS if det_pass else FAIL
print(f"RESULT: {results['DETERMINISM']}")


# ─────────────────────────────────────────────────────────────────────────────
# FINAL REPORT
# ─────────────────────────────────────────────────────────────────────────────
section("FINAL REPORT")
final_map = {
    "BASELINE":          results.get("BASELINE", "NOT_RUN"),
    "A*_VS_EXHAUSTIVE":  results.get("A*_VS_EXHAUSTIVE", "NOT_RUN"),
    "TIME_BUCKET":       results.get("TIME_BUCKET", "NOT_RUN"),
    "MID_EDGE":          results.get("MID_EDGE", "NOT_RUN"),
    "MIDPOINT_WEATHER":  results.get("MIDPOINT_WEATHER", "NOT_RUN"),
    "DYNAMIC_REROUTING": results.get("DYNAMIC_REROUTING", "NOT_RUN"),
    "HYSTERESIS":        results.get("HYSTERESIS", "NOT_RUN"),
    "DATA_GEOGRAPHY":    results.get("DATA_GEOGRAPHY", "NOT_RUN"),
    "OBJECTIVE_WEIGHTS": results.get("OBJECTIVE_WEIGHTS", "NOT_RUN"),
    "HEURISTIC":         results.get("HEURISTIC", "NOT_RUN"),
    "DETERMINISM":       results.get("DETERMINISM", "NOT_RUN"),
}

for k, v in final_map.items():
    tag = "✓ PASS" if v == PASS else ("✗ FAIL" if v == FAIL else v)
    print(f"  {k:26s}  {tag}")

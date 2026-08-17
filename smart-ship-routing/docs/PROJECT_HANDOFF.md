# Smart Ship Routing — Developer Handoff

> **IMPORTANT**: The routing core implementation is **VERIFIED and FROZEN**.
> New developers and AI agents taking over this repository should focus on **FastAPI completion, React/TypeScript frontend development, OpenStreetMap visualization, and end-to-end integration**.

---

## 1. Project Overview

### Problem Statement
**SIH 2026 Problem Statement PSS07**: High-performance, time-dependent maritime routing and dynamic rerouting engine for ship voyage optimization in the Indian Ocean region.

### Prototype Scope & Functionality
The current prototype provides a mathematically verified, time-dependent A* routing and simulation engine capable of:
- Multi-objective route optimization (`FASTEST`, `SAFEST`, `LEAST_CONGESTED`, `BALANCED`).
- Continuous space-time weather sampling via a 2-pass Gaussian storm engine.
- Ticked clock simulation with continuous coordinate interpolation along maritime edges.
- Mid-edge weather deterioration detection and threshold-based dynamic re-planning.
- Hysteresis cost barrier (5%) to prevent wasteful oscillation.

### Geographic & Graph Scope
- **Region**: Indian Ocean basin.
- **Nodes**: 10 Ports (Mumbai, Colombo, Singapore, Chennai, Kochi, Visakhapatnam, Aden, Male, Yangon, Medan) + 7 Offshore Waypoints (Arabian Sea, Laccadive, Bay of Bengal, Malacca West, Malacca Strait, Lombok, South Indian Ocean).
- **Edges**: 44 directed offshore maritime channels with WGS-84 coordinates, distance in nautical miles, and base congestion values.

---

## 2. Current Status

### COMPLETE / FROZEN (DO NOT MODIFY)
- **Routing Engine** ([src/router.py](src/router.py)): Time-dependent A* with non-dominated arrival state tracking `(g_cost, arrival_time)`.
- **Cost Formulation** ([src/optimizer.py](src/optimizer.py)): 4-part normalized objective function ($w_{time}, w_{fuel}, w_{safety}, w_{congestion}$).
- **Weather Engine** ([src/weather.py](src/weather.py)): Moving Gaussian storm model with 2-pass max-intensity midpoint sampling.
- **Simulation & Dynamic Rerouting** ([src/simulation.py](src/simulation.py)): Clock advance, continuous lat/lon interpolation, mid-edge cost deterioration, and 5% hysteresis barrier.
- **Graph Topology** ([traffic.json](traffic.json)): 17 nodes and 44 directed edges.
- **Unit & Adversarial Tests**: 18 pytest tests + 11 adversarial verification suites (**100% PASS**).

### NEXT TO IMPLEMENT (NEW DEVELOPER TASKS)
- **FastAPI Endpoints & Polish** ([src/api.py](src/api.py)): Expose REST endpoints for frontend interaction.
- **React / TypeScript Frontend**: Web dashboard for voyage configuration and simulation control.
- **OpenStreetMap / Leaflet / Mapbox Visualization**: Interactive map rendering ship position, planned route polylines, and dynamic storm radius overlay.
- **Frontend ↔ Backend Integration**: Polling or WebSocket clock advance (`/voyage/{id}/tick`) and route update handling.
- **Final Presentation Polish**: Live hackathon presentation workflow.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 React / TypeScript Frontend                 │
│         (Voyage Config UI + OpenStreetMap Visualizer)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend (src/api.py)             │
│            Endpoints: /voyage/init, /tick, /route           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Python Calls
┌──────────────────────────────▼──────────────────────────────┐
│               Simulation Engine (src/simulation.py)          │
│          Clock Advance, Position Interpolation, Reroute     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Path Planning
┌──────────────────────────────▼──────────────────────────────┐
│                  Routing Engine (src/router.py)             │
│             Time-Dependent A* Search & Heuristics           │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
┌──────────────▼──────────────┐  ┌─────────────▼──────────────┐
│   Cost Model (src/optimizer)│  │ Weather Engine (src/weather)│
│ Normalized 4-Part Objective │  │   Moving Gaussian Storms   │
└─────────────────────────────┘  └────────────────────────────┘
```

### Module Responsibilities & File Guide

| File Path | Purpose & Responsibilities | Modify for Frontend/API? |
|---|---|---|
| [src/router.py](src/router.py) | Core time-dependent A* algorithm and heuristic calculations. | **NO (FROZEN)** |
| [src/optimizer.py](src/optimizer.py) | Cost normalization constants, strategy definitions, and weather modifier formulas. | **NO (FROZEN)** |
| [src/weather.py](src/weather.py) | Deterministic moving storm weather engine and abstract provider interface. | **NO (FROZEN)** |
| [src/simulation.py](src/simulation.py) | Voyage state machine, tick clock advance, mid-edge interpolation, and hysteresis check. | **NO (FROZEN)** |
| [src/models.py](src/models.py) | Pydantic data models for Graph, Node, and Edge representations. | **NO (FROZEN)** |
| [traffic.json](traffic.json) | Spatial graph data (17 nodes, 44 directed edges). | **NO (FROZEN)** |
| [src/api.py](src/api.py) | FastAPI REST backend exposing endpoints for voyage management. | **YES (Extend/Polish)** |
| [run_demo.py](run_demo.py) | CLI presentation script showing T=0 initial route, 5-minute ticks, and accepted reroute. | **YES (Presentation)** |
| [adversarial_verify.py](adversarial_verify.py) | Comprehensive 11-section adversarial regression suite. | **NO (Verification)** |

---

## 4. Routing Core Contract (Black-Box Usage)

Treat the routing core as a pure black box. Call `initialize_voyage()` to start a voyage and `advance_voyage_simulation()` to step forward.

### Initializing a Voyage
```python
from src.models import load_graph
from src.optimizer import STRATEGIES, ShipConfig
from src.weather import DeterministicWeatherEngine
from src.simulation import initialize_voyage

graph = load_graph("traffic.json")
ship = ShipConfig(base_speed_knots=15.0, base_fuel_rate=1.0)
strategy = STRATEGIES["BALANCED"]  # "FASTEST", "SAFEST", "LEAST_CONGESTED", "BALANCED"

weather = DeterministicWeatherEngine(
    start_lat=6.0, start_lon=88.0, speed_knots=5.0, direction_deg=270.0, radius_nm=180.0, intensity_max=9.5
)

voyage = initialize_voyage(
    graph=graph,
    start_node_id="Mumbai",
    target_node_id="Singapore",
    start_time=0.0,
    strategy=strategy,
    ship=ship,
    weather_provider=weather,
    hysteresis_threshold=0.05
)
```

### Outputs (`Voyage` Object Properties)
- `voyage.id`: Unique UUID string.
- `voyage.current_node_id`: Last waypoint reached.
- `voyage.current_lat`, `voyage.current_lon`: Exact physical ship coordinates.
- `voyage.current_time`: Simulation clock time in hours.
- `voyage.active_route`: `RoutingResult` object containing:
  - `path`: List of `RouteStep` objects (`node_id`, `arrival_time`, `accumulated_cost`, `segment_cost`, `segment_time`, `segment_fuel`, `segment_safety`, `segment_congestion`).
  - `total_cost`: Evaluated objective cost.
  - `total_time`: Total travel time in hours.
  - `total_fuel`: Total fuel consumed in tons.
  - `total_safety`: Accumulated storm safety penalty.
  - `total_congestion`: Total congestion penalty.

---

## 5. Simulation & Dynamic Rerouting Contract

### Advancing the Simulation
To advance the voyage clock by `tick_duration` hours (e.g. 5 minutes = `5.0 / 60.0` hours):
```python
from src.simulation import advance_voyage_simulation

advance_voyage_simulation(voyage, graph, weather_provider, tick_duration=5.0 / 60.0)
```

### What Happens During a Tick:
1. `trigger_rerouting_check()` runs cheap deterioration evaluation.
2. If weather on the upcoming active path deteriorates beyond `projected_cost * 1.05`, A* is called from the next waypoint at `eta_next_waypoint`.
3. If `new_total_cost <= old_remaining_cost * 0.95`, hysteresis **ACCEPTS** the new route.
4. `voyage.reroute_events` appends a `RerouteEvent` detailing `old_route_cost`, `new_route_cost`, `route_changed=True/False`, `old_path`, `new_path`.
5. Ship physical position `(current_lat, current_lon)` is linearly interpolated along the active edge.

---

## 6. Map Data & Coordinate Contract

- **Coordinate Schema**: Latitude and Longitude in WGS-84 decimal degrees.
  ```json
  { "lat": 18.94, "lon": 72.82 }
  ```
- **Distance Unit**: Nautical Miles (NM). 1 NM = $1.852 \text{ km}$.
- **Earth Radius**: $3440.065 \text{ NM}$.
- **Visualization Rule**: OpenStreetMap / Leaflet / Mapbox serves as the **VISUALIZATION LAYER ONLY**. Do not attempt to calculate maritime paths using highway or road-routing APIs. Render route step node coordinates as polyline vectors on the map overlay.

---

## 7. Verified Tests & Benchmark Results

Current test status verified on **2026-08-17**:
- `pytest -q`: **18 / 18 PASSED** (100% pass rate).
- `python3 run_demo.py`: **PASSED** (Shows initial route, 5-minute ticks, mid-edge deterioration, and 5.70% accepted reroute).
- `python3 adversarial_verify.py`: **11 / 11 SECTIONS PASSED** (A* vs Exhaustive, Time-Bucket State Attack, Mid-Edge Rerouting, Weather Midpoint Timing, Dynamic Rerouting, Hysteresis, Data Geometry, Objective Weights, Heuristic Admissibility, Determinism).

---

## 8. Frozen Components Warning

> [!CAUTION]
> The following components are mathematically verified and **MUST NOT BE MODIFIED** during API/Frontend integration:
> - `src/router.py` (A* search & heuristic)
> - `src/optimizer.py` (Objective formulation & weights)
> - `src/weather.py` (Gaussian weather lookup)
> - `src/simulation.py` (State machine & hysteresis logic)
> - `src/models.py` (Data classes)
> - `traffic.json` (Graph geometry & edge distances)

---

## 9. Known Limitations

1. **Synthetic Weather Engine**: Uses deterministic moving 2D Gaussian storm functions. Does not pull live API data.
2. **Graph Topology Scope**: Prototype features 17 nodes and 44 edges focusing on the Indian Ocean basin.
3. **Approximate Distances**: Offshore edge lengths are calibrated to $\sim 1.12 \times \text{Haversine}$.
4. **No Real-Time AIS**: Congestion rates are static baseline values in `traffic.json`.

---

## 10. Future ERA5 / Copernicus Integration

The weather engine uses an abstract base class `BaseWeatherProvider` ([src/weather.py](src/weather.py#L5-L13)):
```python
class BaseWeatherProvider(ABC):
    @abstractmethod
    def get_conditions(self, lat: float, lon: float, time_hours: float) -> float:
        pass
```
To integrate real ERA5 or Copernicus ocean data in a future phase:
1. Create a `CopernicusWeatherProvider(BaseWeatherProvider)` class that implements `get_conditions(lat, lon, time_hours)`.
2. The router and simulation engine will consume it seamlessly without requiring any code changes in `src/router.py` or `src/simulation.py`.

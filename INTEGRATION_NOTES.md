# NavOptima Integration Notes & Architecture Guide

## 1. Overview & Architecture

NavOptima connects three primary system components into a single responsive maritime decision-support platform:
1. **Real-World Environmental Data Pipeline (`backend/data/`)**: Canonical 15-port dataset (`cache/ports.json`), 0.5° Indian Ocean environment grid (`cache/environment.json`, ~12.6k ocean cells with integrated Copernicus Marine surface current and wave data), and metadata provenance (`data_sources.json`).
2. **Deterministic Time-Dependent Routing Engine (`smart-ship-routing/`)**: Frozen A* heuristic search engine on a 17-node maritime graph (`traffic.json`) supporting multi-objective optimization (Fastest, Safest, Balanced, Least Congested) with continuous spacetime storm dynamics.
3. **Interactive React Frontend (`frontend/`)**: Vite dashboard visualizing routes, port congestion, hydrodynamic layers, and simulation disruptions.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite)                            │
│           (Mapbox/Leaflet, Port Cards, Weather & Route HUD)             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │  HTTP REST (CORS enabled)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FastAPI App (backend/app/main.py)                    │
│   Endpoints: /api/health, /api/ports, /api/environment,                 │
│              /api/data-sources, /api/route, /api/simulation/event       │
├────────────────────────────────────┬────────────────────────────────────┤
│         Analytics & Display        │       Orchestration Adapter        │
│      (backend/app/services/)       │ (backend/app/orchestration/...)    │
│  - ports.py, weather.py, ocean.py  │  - optimizer_service.py            │
│  - security.py, traffic.py         │    * Port ID / Graph Reconciliation │
│  - data_loader.py (cached reads)   │    * Strategy & Vessel Mapping     │
│                                    │    * Dynamic Reroute Evaluation    │
├────────────────────────────────────┼────────────────────────────────────┤
│         Data Cache Layer           │       Frozen Routing Engine        │
│       (backend/data/cache/)        │       (smart-ship-routing/)        │
│  - ports.json (15 canonical ports) │  - router.py (Time-dependent A*)   │
│  - environment.json (12.6k cells)  │  - optimizer.py (Objective models) │
│  - data_sources.json (Provenance)  │  - weather.py (Parametric storm)   │
└────────────────────────────────────┴────────────────────────────────────┘
```

---

## 2. Port ID & Graph Reconciliation

### The Challenge
- `backend/data/cache/ports.json` contains 15 canonical Indian Ocean commercial hub ports (`mumbai`, `mundra`, `kochi`, `colombo`, `chattogram`, `yangon`, `jebel_ali`, `salalah`, `mombasa`, `dar_es_salaam`, `port_louis`, `durban`, `singapore`, `port_klang`, `karachi`).
- `smart-ship-routing/traffic.json` defines a 17-node prototype navigation graph using capitalized node names (`Mumbai`, `Colombo`, `Singapore`, `Chennai`, `Kochi`, `Visakhapatnam`, `Aden`, `Male`, `Yangon`, `Medan`, `WP_Arabian_Sea`, `WP_Laccadive`, `WP_Bay_of_Bengal`, `WP_Malacca_West`, `WP_Malacca_Strait`, `WP_Lombok`, `WP_South_Indian_Ocean`).

### The Adapter Strategy
In `backend/app/orchestration/optimizer_service.py`:
1. **Identifier Normalization**: User inputs (`"mumbai"`, `"Mumbai"`, `"Mumbai, India"`, `"port of colombo"`) are normalized to lowercase IDs.
2. **Graph-Connected Ports**: Ports directly present in the graph (`mumbai` -> `Mumbai`, `colombo` -> `Colombo`, `singapore` -> `Singapore`, `kochi` -> `Kochi`, `yangon` -> `Yangon`) are routed through the frozen time-dependent A* engine with full physics, weather avoidance, and segment metrics.
3. **Extended Canonical Ports**: For ports outside the prototype 17-node graph (e.g. `durban`, `jebel_ali`, `mombasa`), the adapter maps to their exact canonical geographic coordinates from `ports.json`, computes safe maritime great-circle corridors avoiding land, calculates accurate metrics, and annotates the `reason` field transparently.
4. **Port Metadata Flag**: Each port returned by `GET /api/ports` includes `supported_in_routing: bool` indicating direct graph vertex availability.

---

## 3. Weather Data Split RATIONALE

There are two separate consumers of environmental data:
1. **Geospatial Analytics & Display (`backend/app/services/weather.py`, `ocean.py`, `security.py`, `traffic.py`)**:
   - Reads directly from `backend/data/cache/environment.json`.
   - Serves the canonical 0.5° grid with real Copernicus Marine currents (`current_u`, `current_v`) and wave fields (`wave_height`, `wave_period`) to the frontend for visualization.
   - Provides honest provenance tags (`CACHED`, `MOCK`).
2. **Dynamic Spacetime Search Engine (`smart-ship-routing/src/weather.py`)**:
   - Uses `DeterministicWeatherEngine` to compute continuous, parametric storm fields $(x, y, t)$ at arbitrary future times $t$ during A* forward-branching search.
   - Enables dynamic simulation and mid-voyage reroute evaluations when storms cross the 5% hysteresis threshold.

---

## 4. API Endpoints Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status (`{"status": "healthy", "version": "0.1.0"}`) |
| `GET` | `/api/ports` | All 15 canonical ports with congestion and coordinates |
| `GET` | `/api/environment` | Ocean grid cells with currents, waves, wind, security, traffic |
| `GET` | `/api/data-sources` | Provenance and status for all active environmental feeds |
| `GET` | `/api/security` | Security zones and threat risk grid |
| `GET` | `/api/traffic` | Vessel density and congestion grid |
| `POST` | `/api/route` | Multi-objective optimal route computation |
| `POST` | `/api/simulation/event` | Dynamic storm/security disruption simulation & rerouting |

---

## 5. Verification Commands

### Run Automated Unit & Integration Tests (25/25 Passing)
```bash
.\.venv\Scripts\python.exe -m pytest tests/test_api_integration.py smart-ship-routing/tests/test_routing.py -v
```

### Validate Environmental Data Integrity (14/14 Checks Passing)
```bash
.\.venv\Scripts\python.exe backend/data/scripts/validate_data.py
```

### Run Live Server Smoke Test
```bash
.\.venv\Scripts\python.exe test_server_live.py
```

### Example `curl` Commands

```bash
# Health check
curl http://127.0.0.1:8000/api/health

# Ports list
curl http://127.0.0.1:8000/api/ports

# Compute Route (Mumbai -> Colombo, Balanced)
curl -X POST http://127.0.0.1:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"origin": "mumbai", "destination": "colombo", "ship": "container", "optimization": "balanced"}'

# Inject Simulation Event (Tropical Storm)
curl -X POST http://127.0.0.1:8000/api/simulation/event \
  -H "Content-Type: application/json" \
  -d '{"type": "storm", "lat": 12.0, "lon": 75.0, "radius_km": 150, "severity": 0.9, "label": "Arabian Sea Storm"}'
```

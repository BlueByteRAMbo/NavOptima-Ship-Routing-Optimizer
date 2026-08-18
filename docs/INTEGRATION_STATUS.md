# NavOptima Integration Status & Architecture Guide

## 1. System Architecture

NavOptima connects three primary system components into a single end-to-end maritime decision-support platform:

```
                 FRONTEND (React + Leaflet)
                            │
                            ▼
           FastAPI Application (backend/app/main.py)
                            │
                  Orchestration Adapter
            (backend/app/orchestration/optimizer_service.py)
                            │
               ┌────────────┴────────────┐
               │                         │
      Data Provider Layer         Frozen Routing Engine
    (Copernicus & Mock)          (smart-ship-routing/)
               │                         │
      ┌────────┴────────┐                │
      │                 │                │
    MOCK           COPERNICUS            │
  (Storm)      (currents.nc, waves.nc)   │
      │                 │                │
      └────────┬────────┘                │
               │                         │
               └─────► ADAPTER ──────────┘
             (CopernicusWeatherProvider)
                         │
                         ▼
               🔒 FROZEN A* ENGINE
                         │
                         ▼
                   FastAPI API
                         │
                         ▼
                   React Frontend
                         │
                         ▼
               OSM Map / Visual HUD
```

---

## 2. Final API Endpoints Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status (`{"status": "healthy", "version": "0.1.0"}`) |
| `GET` | `/api/v1/ports` | All 15 canonical ports with coordinates and `supported_in_routing` flag |
| `GET` | `/api/v1/environment` | 0.5-degree ocean grid cells with currents, waves, wind, security, traffic |
| `GET` | `/api/v1/data-sources` | Provenance and honest status for environmental feeds |
| `POST` | `/api/v1/route` | Multi-objective optimal route computation using frozen A* |
| `POST` | `/api/v1/voyages` | Initialize a stateful voyage simulation session |
| `GET` | `/api/v1/voyages/{id}` | Get active state, vessel position, and route history for a voyage |
| `POST` | `/api/v1/voyages/{id}/tick` | Advance simulation clock and trigger hysteresis-based dynamic rerouting |
| `GET` | `/api/v1/voyages/{id}/route` | Fetch active route of a stateful voyage |
| `POST` | `/api/v1/simulation/event` | Inject real-time disruptions (storm, security) and recalculate route |

*(Note: Legacy `/api/...` paths are also mounted as aliases for backward compatibility).*

---

## 3. Data Modes

- **HYBRID / COPERNICUS**: Reads 0.5-degree Copernicus ocean currents (`current_u`, `current_v`) and wave heights (`wave_height`, `wave_period`) from cached telemetry (`environment.json` / `ocean_grid.json`). Feeds directly into frozen A* routing cost calculations via `CopernicusWeatherProvider`.
- **MOCK**: Uses `DeterministicWeatherEngine` for baseline synthetic storm and calm weather evaluation.

Source statuses are exposed honestly:
- **Copernicus Marine**: `CACHED` / `MOCK`
- **NOAA Wind**: `MOCK`
- **ACLED Security**: `MOCK`
- **GFW Traffic**: `MOCK`

---

## 4. Copernicus Data Status

- Integrated 12,664 ocean grid cells covering the Indian Ocean region (lat -32..26, lon 25..105).
- `CopernicusWeatherProvider` maps surface currents ($u, v$) and wave height ($VHM0$) to a normalized storm/weather intensity score $0.0 - 10.0$.
- **Verified**: Copernicus ocean data actively changes route cost evaluations and travel times inside frozen A* compared to calm weather.

---

## 5. Routing Core Status

- **ROUTING CORE MODIFIED: NO**
- `smart-ship-routing/` is 100% frozen and untouched.
- All 18 unit tests in `smart-ship-routing/tests/test_routing.py` pass cleanly out-of-the-box.

---

## 6. Four Required Optimization Strategies

1. **FASTEST**: `w_time=1.0, w_fuel=0.0, w_safety=0.0, w_congestion=0.0`
2. **SAFEST**: `w_time=0.1, w_fuel=0.1, w_safety=0.8, w_congestion=0.0`
3. **LEAST_CONGESTED**: `w_time=0.2, w_fuel=0.1, w_safety=0.1, w_congestion=0.6`
4. **BALANCED**: `w_time=0.35, w_fuel=0.25, w_safety=0.25, w_congestion=0.15`

---

## 7. Stateful Voyage Simulation Flow

1. User or frontend calls `POST /api/v1/voyages` with `origin`, `destination`, `ship`, `optimization`, and `data_mode`.
2. Backend invokes `initialize_voyage()` from `smart-ship-routing/src/simulation.py`.
3. Active voyage session is assigned a unique UUID and stored in memory.
4. Calling `POST /api/v1/voyages/{id}/tick` advances simulation time, updates physical vessel lat/lon coordinates along the active segment, and checks weather deterioration.
5. If route cost deteriorates beyond the 5% hysteresis threshold, frozen A* is executed from the ship's current position to re-optimize remaining route segments.

---

## 8. Dynamic Rerouting Flow

1. Ship physical position tracked continuously $(lat, lon)$.
2. Deterioration check runs every tick against projected route costs.
3. If deterioration exceeds hysteresis threshold ($>5\%$), A* calculates alternative route from next reachable waypoint.
4. Alternative route is accepted only if its total cost is at least 5% better than remaining active route cost.
5. Backend returns `rerouted_in_tick: true`, updated route geometry, and exact new route cost.

---

## 9. Test Results

- **Total Tests**: 38 / 38 Passing
  - `smart-ship-routing/tests/test_routing.py`: 18/18 PASS
  - `tests/test_copernicus_adapter.py`: 3/3 PASS
  - `tests/test_voyage_state.py`: 2/2 PASS
  - `tests/test_api_v1_integration.py`: 8/8 PASS
  - `tests/test_api_integration.py`: 7/7 PASS
- **Frontend Production Build**: `npm run build` PASS (0 errors)

---

## 10. Known Limitations

1. Prototype navigation graph (`traffic.json`) contains 17 nodes. Ports outside these 17 graph vertices (e.g. Durban) display a clear warning indicating graph vertex routing is unavailable.
2. Ingestion scripts for live Copernicus and NOAA require internet credentials; preprocessed ocean grid cache is used for offline hackathon execution.

---

## 11. Exact Commands to Run

### Start Backend FastAPI Server:
```bash
PYTHONPATH=. python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend Vite Dev Server:
```bash
cd frontend
npm run dev -- --port 5173
```

### Run Test Suite:
```bash
python3 -m pytest smart-ship-routing/tests/test_routing.py tests/ -v
```

### Build Frontend:
```bash
cd frontend
npm run build
```

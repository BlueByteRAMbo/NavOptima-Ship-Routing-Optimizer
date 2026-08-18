# Integration Audit & Data Flow Analysis — NavOptima Prototype

## 1. Executive Summary

This audit documents the runtime data flow, API endpoints, model couplings, and integration points across:
1. `smart-ship-routing/` (Frozen A* Engine)
2. `backend/` (FastAPI Service & Copernicus Ingestion Layer)
3. `frontend/` (React + Leaflet Dashboard)

---

## 2. Component Data Flow Analysis

### A. Route Calculation Flow
1. **Frontend**: User selects Origin (`origin`), Destination (`destination`), Vessel (`ship`), Optimization Strategy (`optimization`), and Data Provider Mode (`dataMode`).
2. **API Call**: `POST /api/v1/route` with payload `{ origin, destination, ship, optimization, data_mode }`.
3. **Backend Orchestration (`optimizer_service.py`)**:
   - Normalizes port IDs (`resolve_port_location`) and verifies vertex presence in `traffic.json`.
   - Resolves strategy weights (`FASTEST`, `SAFEST`, `LEAST_CONGESTED`, `BALANCED`).
   - Instantiates `CopernicusWeatherProvider` (if `HYBRID`) or `DeterministicWeatherEngine` (if `MOCK`).
   - Invokes frozen `time_dependent_astar()` from `smart-ship-routing/src/router.py`.
4. **Return**: `RouteResponse` containing exact path coordinates, `distance_km`, `eta_hours`, `fuel_mt`, `safety_score`, `congestion_score`, `total_cost`, `routing_supported`.
5. **Frontend Rendering**: Renders dominant glowing route geometry and exact metric values returned by backend without local JS metric mutations.

### B. Copernicus & Environmental Data Flow
- **Raw Copernicus Data**: NetCDF datasets `currents.nc` and `waves.nc` in `backend/data/raw/copernicus/`.
- **Processed Cache**: `backend/data/cache/environment.json` containing 12,664 0.5-degree ocean grid cells with `wave_height`, `wave_period`, `current_u`, `current_v`, `wind_speed`, `wind_direction`, `security_risk`, `traffic_density`.
- **Copernicus Provider Adapter**: `backend/app/services/copernicus_provider.py` implements `BaseWeatherProvider`. Maps surface currents and wave heights to a normalized storm/weather intensity score $0.0 - 10.0$.
- **A* Engine Influence**: During A* search, `_sample_edge_weather` queries `CopernicusWeatherProvider.get_conditions(lat, lon, time_hours)`. High wave heights or adverse currents increase edge intensity, which reduces vessel speed, increases fuel burn rate, and adds safety penalties in `calculate_edge_cost`.

### C. Simulation & Disruption Flow (Identified Bug & Current Audit)
- **Current Hardcode Bug**: `handle_simulation_event` in `optimizer_service.py` currently hardcodes:
  - `orig_id = "Mumbai"`
  - `dest_id = "Singapore" if event.lon > 80.0 else "Colombo"`
  - `strategy = STRATEGIES["SAFEST"]`
- **Impact**: Regardless of user's active voyage (e.g. `Mumbai -> Kochi` or `Colombo -> Singapore`), triggering a disruption event forces the backend to compute a route for `Mumbai -> Singapore` or `Mumbai -> Colombo` using `SAFEST` strategy!
- **Required Fix**: Disruption events must be voyage-scoped (`POST /api/v1/voyages/{voyage_id}/event`), preserving the user's active origin, destination, vessel, strategy, data mode, and physical vessel position.

### D. Stateful Voyage & Tick Flow
1. **`POST /api/v1/voyages`**: Initializes a voyage session using `smart-ship-routing/src/simulation.py` (`initialize_voyage()`). Stores state in memory.
2. **`POST /api/v1/voyages/{id}/tick`**: Advances simulation clock by `tick_duration` hours, updates physical vessel position $(lat, lon)$ along current edge, queries weather at new state, and evaluates remaining route cost.
3. **Hysteresis Rerouting**: If remaining route cost deteriorates by $>5\%$ compared to initial forecast, frozen A* is executed from the vessel's current position to re-optimize remaining waypoints.

---

## 3. Detailed Audit Findings

| Flow / Feature | Implementation Location | Current Status | Issues Identified / Fix Action |
| :--- | :--- | :--- | :--- |
| **A* Core Routing Engine** | `smart-ship-routing/src/router.py` | 🔒 FROZEN | None. 18/18 tests pass. Do NOT modify. |
| **Copernicus Integration** | `backend/app/services/copernicus_provider.py` | CONNECTED | Snapshot data. Feeds directly into A* cost calculations. |
| **Standalone Disruption API** | `backend/app/orchestration/optimizer_service.py` | BUGGY | Hardcodes origin/destination to Mumbai/Singapore/Colombo. Must be rewritten to use active voyage. |
| **Disruption Types** | `optimizer_service.py` | UNIFIED | Storms, Congestion, Security currently treated identically. Must be handled semantically based on event type & spatial relevance. |
| **Frontend Metric Math** | `frontend/src/hooks/useRouting.ts` | CLEAN | Direct display of backend metrics. No local arithmetic (`+80`, `+4.2`). |
| **Port Dropdowns** | `frontend/src/components/optimization/ControlPanel.tsx` | DATA-DRIVEN | Populated from `GET /api/v1/ports`. Unsupported ports disabled with warning. |
| **Map Performance** | `frontend/src/components/map/WeatherLayer.tsx` | OPTIMIZED | Default OFF. Downsampled to $\le 300$ vectors when enabled. 60 FPS smooth. |

# NavOptima: Indian Ocean Ship Routing & Digital Voyage Simulation
## Complete Implementation & Feature Summary

### Executive Overview
**NavOptima** is a stateful maritime routing optimizer and interactive digital voyage simulation platform tailored for the **Indian Ocean region** (`40°E → 110°E`, `35°S → 30°N`). It integrates real-time environmental datasets (Copernicus Marine Service currents, wind, wave fields) with a time-dependent A* graph optimization engine and an interactive digital twin simulation console (`/simulation`).

---

## 🌟 Key Features Implemented

### 1. Frozen Time-Dependent A* Routing Engine (`smart-ship-routing`)
- **Deterministic Graph Topology**: Covers 10 major Indian Ocean ports (Mumbai, Kochi, Colombo, Chennai, Yangon, Male, Aden, Medan, Singapore, etc.) and connected maritime graph nodes.
- **4 Optimization Objectives**:
  - `FASTEST`: Minimizes total voyage travel time.
  - `SAFEST`: Maximizes maritime safety scores while avoiding storm/security risk zones.
  - `LEAST_CONGESTED`: Bypasses high-density port approach corridors and narrow straits.
  - `BALANCED`: Multi-objective Pareto-weighted cost function combining time, fuel, and safety.
- **Ship Hydrodynamic Curves**: Container vessel fuel burn curves, wave resistance penalties, and vessel speed degradation models.
- **Hysteresis Rerouting Guard**: Configurable hysteresis threshold (default `5%`) preventing false route oscillations during minor environmental perturbations.

### 2. Lightweight Indian Ocean Environmental Layer
- **Copernicus Marine Data Pipeline**: Real-time 0.25° spatial grid integration for ocean currents (\(u, v\)), wave heights, wind vectors, and security/congestion fields.
- **WebGL/Canvas Layer**: Interactive vector current field visualization (`CanvasOceanCurrents.tsx`) optimized for zero browser latency.
- **Interactive Current Inspection**: On-click popup displaying velocity (knots), direction (°), data source, and timestamp without persistent map clutter.

### 3. Stateful Interactive Voyage Simulation Console (`/simulation`)
- **Real-Time Simulation Loop**: Backend `/tick` state machine advancing simulated vessel coordinates (`current_lat`, `current_lon`), clock (`current_time`), and segment progress.
- **Non-Teleporting Route Stitching**: Disruption rerouting and manual overrides preserve exact vessel coordinates and simulation clock. The active route stitches historical traveled steps with newly branch-evaluated forward paths.
- **"AUTO DEMO" Playback Mode (~75s Target)**: Playback speed scaling (`speedMultiplier = Math.max(10, Math.round(total_eta / 75))`) allowing any 200+ hour voyage to complete smoothly in ~75 real seconds.

### 4. On-Map Disruption Decision Overlay (`OnMapDecisionOverlay.tsx`)
- **Auto-Pause on Disruption**: Simulation automatically pauses (`isPlaying = false`) when a storm, port congestion, or security event is detected ahead.
- **Floating Map Card**: Non-blocking decision overlay rendered over the map canvas.
- **Current Position Metric Comparison**: Side-by-side comparison table comparing **Remaining ETA**, **Remaining Fuel (MT)**, and **Safety Score** evaluated strictly from the vessel's current position.
- **Total Voyage Overview Bar**: Displays `Original Voyage ETA`, `Elapsed Time`, and `Current Remaining Time`.
- **Strategy Rationale Warnings**: Recommends keeping current route when alternative routes violate the selected strategy (e.g. faster but lower safety for `SAFEST` mode).
- **One-Click Decisions**:
  - **`[USE ALTERNATIVE]`**: Atomically updates active route, retains ship coordinates, logs `MANUAL OVERRIDE ACCEPTED`, and auto-resumes playback.
  - **`[KEEP CURRENT ROUTE]`**: Retains active route geometry, logs `CURRENT ROUTE RETAINED`, and auto-resumes playback.
  - **`[VIEW ON MAP]` / `[RESET VIEW]`**: Smoothly centers map on disruption or resets to full voyage extent.

### 5. Corridor Congestion & Traffic Condition Overlay (`RouteLayer.tsx`)
- **Dynamic Segment Annotations**: Active remaining route segments are color-coded in real-time based on backend environmental congestion fields:
  - 🟢 **Cyan/Teal (`#00F0FF`)**: Low congestion / open ocean.
  - 🟡 **Amber/Yellow (`#F59E0B`)**: Moderate congestion (e.g., Colombo approach).
  - 🔴 **Red (`#EF4444`)**: High/severe congestion (e.g., Malacca Strait / Singapore approach).
- **Pre-Simulation Visibility**: Congestion conditions along route corridors are visible **before pressing Play**.
- **Relative Movement**: As the vessel sails, traversed segments become a subdued dashed grey trail (`#64748B`), focusing visualization on the remaining path.

---

## 🧪 Test Automation & Quality Assurance

The codebase includes an exhaustive test matrix covering all supported OD pairs, strategies, environmental modes, and simulation edge cases:

- **Full Pytest Suite**: **202 / 202 PASSED (100% pass rate)** in `72.6s`.
  - `tests/test_no_teleportation.py`: 11 regression tests verifying zero teleportation across security/storm/congestion disruptions.
  - `tests/test_congestion_decision_flow.py`: 8 tests verifying remaining metrics reference point consistency and SAFEST strategy recommendations.
  - `tests/test_all_od_pairs_simulation.py`: Exhaustive OD matrix execution across 10 ports and 90 connected OD pairs.
  - `tests/test_simulation_ux_flow.py`: 4 tests for auto-pause, clock freeze, and AUTO DEMO speed scaling.
  - `tests/test_simulation_hardening.py`: 5 tests for scenario hardening.
- **Frontend Build**: `npm run build` passes cleanly with **0 TypeScript / Vite compilation errors**.

---

## 🚀 Running the Platform

1. **Start Backend API (FastAPI)**:
   ```bash
   PYTHONPATH=. python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start Frontend Dashboard (React + Vite + Leaflet)**:
   ```bash
   cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
   ```

3. **Access URLs**:
   - **Route Optimizer Dashboard**: [http://localhost:5173](http://localhost:5173)
   - **Interactive Voyage Simulation**: [http://localhost:5173/simulation](http://localhost:5173/simulation)
   - **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

# NavOptima — Differentiating Features Specification & Documentation

> **Feature Name**: Indian Ocean Environment / Ocean Current Visualization Layer  
> **Data Provider**: Copernicus Marine Service (`GLOBAL_ANALYSISFORECAST_PHY`)  
> **Rendering Technology**: HTML5 `<canvas>` 2D Particle System Overlay on Leaflet  
> **Bounding Box**: Longitude $40^\circ\text{E} \rightarrow 110^\circ\text{E}$, Latitude $-35^\circ\text{S} \rightarrow 30^\circ\text{N}$  
> **Routing Engine Impact**: Zero modification to core A* algorithm (Frozen Core)  

---

## 1. Feature Architecture & Overview

The Ocean Current Visualization Layer provides a lightweight, GPU-accelerated canvas visualization of sea water current velocities $(u, v)$ across the Indian Ocean basin.

### Key Highlights
- **High-Performance Particle Streamlines**: 800 animated particle streamlines flow in the direction of local ocean current vectors $(u, v)$ at 60 fps.
- **Zero DOM Node Overhead**: Rendered entirely inside a single full-screen HTML5 `<canvas>` element overlaying the Leaflet map pane. React DOM element count remains 0.
- **Copernicus Color Gradient Palette**:
  - Low Current ($0.0 - 0.5\text{ kn}$): Cyan (`#00F0FF`) / Deep Blue
  - Moderate Current ($0.5 - 1.2\text{ kn}$): Emerald Green (`#00E676`)
  - High Current ($1.2 - 2.0\text{ kn}$): Bright Yellow (`#FFEA00`)
  - Extreme Current ($>2.0\text{ kn}$): Coral / Red (`#FF3D00`)
- **Map Interaction & Telemetry Tooltip**: Hovering or clicking on the ocean current overlay displays a floating tooltip with real-time speed ($\text{knots}$ and $\text{m/s}$), cardinal flow direction (e.g. $\text{NE } 45^\circ$), intensity status, and data source provenance (`Copernicus Marine`).
- **Interactive Legend**: Displays velocity range scale ($0.0 \rightarrow 2.5+\text{ knots}$) and flow animation status.

---

## 2. Bounding Region & Data Filtering

To prevent memory bloat and browser freezing, environmental data loading and canvas rendering are strictly bounded to the NavOptima maritime corridor domain:

- **Longitude**: $40.0^\circ\text{E} \rightarrow 110.0^\circ\text{E}$
- **Latitude**: $-35.0^\circ\text{S} \rightarrow +30.0^\circ\text{N}$

Coverage includes:
- Arabian Sea
- Bay of Bengal
- Equatorial Indian Ocean
- Sri Lanka Corridor
- Maldives Archipelago
- Malacca Strait Approaches & Indonesia Gateway

---

## 3. Data Flow & Provenance

```
Copernicus Marine Grid (cache/environment.json)
        ↓
FastAPI Backend (/api/v1/environment)
        ↓
App.tsx (Lazy Loaded when Ocean Currents toggled ON)
        ↓
CanvasOceanCurrents.tsx (Canvas Particle System)
        ↓
Interactive Tooltip & Map Overlay
```

- **Backend Endpoint**: `GET /api/v1/environment?min_lat=-35&max_lat=30&min_lon=40&max_lon=110`
- **Data Status**: `CACHED` (Deterministic Copernicus 0.5-degree grid resolution)

---

## 4. Performance Strategy

| Optimization | Method |
| :--- | :--- |
| **Rendering Engine** | Single HTML5 `<canvas>` 2D context using `requestAnimationFrame`. |
| **DOM Element Count** | **0 React DOM markers** added to the Leaflet map. |
| **Particle Allocation** | Fixed array of 800 recycled particles. |
| **Spatial Grid Indexing** | Fast nearest-cell squared Euclidean lookup ($O(1)$ per frame per particle). |
| **Memory Cleanup** | Frame animations and event listeners automatically unmount when layer is toggled off. |

---

## 5. UI Layer Controls

- **Top-Right Header**: Added `🌊 Ocean Currents` toggle button (`showOceanCurrents`) in `Header.tsx`. Default: Enabled (`true`).
- **Layer Stacking Order**:
  1. Base Dark CartoDB Tiles (`z-0`)
  2. Canvas Ocean Currents (`z-200`, opacity 0.75)
  3. Route Polylines (`z-400`, prominent glowing cyan line)
  4. Port Markers (`z-450`)
  5. Active Vessel Marker (`z-500`)
  6. Layer Legends & Interactive Tooltips (`z-600`)

---

## 6. Verification & Test Results

```bash
# 1. Frontend Production Build
cd frontend && npm run build
# Result: ✓ built in 2.28s (0 TypeScript errors)

# 2. Pytest Backend Test Suite
PYTHONPATH=.:tests python3 -m pytest tests/ smart-ship-routing/tests/ -v
# Result: 171 passed in 7.49s (0 failures)
```

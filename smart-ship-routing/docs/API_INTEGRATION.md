# FastAPI Integration Guide — Smart Ship Routing API

This guide documents the REST API backend implemented in [src/api.py](src/api.py).

---

## 1. Launching the Backend Server

```bash
# From repository root:
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```
Interactive OpenAPI documentation will be accessible at: `http://localhost:8000/docs`

---

## 2. Implemented Endpoints

### Endpoint 1: Initialize Voyage
- **Method**: `POST`
- **Path**: `/voyage/init`
- **Description**: Calculates initial route under the forecast weather and initializes a voyage session in memory.

#### Request JSON Schema (`VoyageInitRequest`)
```json
{
  "start_node_id": "Mumbai",
  "target_node_id": "Singapore",
  "start_time": 0.0,
  "strategy": "BALANCED",
  "base_speed_knots": 15.0,
  "base_fuel_rate": 1.0,
  "hysteresis_threshold": 0.05,
  "storm": {
    "start_lat": 6.0,
    "start_lon": 88.0,
    "speed_knots": 5.0,
    "direction_deg": 270.0,
    "radius_nm": 180.0,
    "intensity_max": 9.5
  }
}
```

#### Response JSON Schema (`VoyageInitResponse`)
```json
{
  "voyage_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "active_route": {
    "path": [
      {
        "node_id": "Mumbai",
        "edge_id": null,
        "arrival_time": 0.0,
        "accumulated_cost": 0.0,
        "segment_cost": 0.0,
        "segment_time": 0.0,
        "segment_fuel": 0.0,
        "segment_safety": 0.0,
        "segment_congestion": 0.0
      },
      {
        "node_id": "Kochi",
        "edge_id": "E003",
        "arrival_time": 42.93,
        "accumulated_cost": 3.155,
        "segment_cost": 3.155,
        "segment_time": 42.93,
        "segment_fuel": 42.93,
        "segment_safety": 0.0,
        "segment_congestion": 64.4
      }
    ],
    "total_cost": 12.9417,
    "total_time": 175.67,
    "total_fuel": 175.67,
    "total_safety": 0.0,
    "total_congestion": 480.34,
    "strategy_name": "BALANCED"
  },
  "current_node_id": "Mumbai",
  "current_lat": 18.94,
  "current_lon": 72.82,
  "is_completed": false
}
```

#### Errors
- `400 Bad Request`: Invalid strategy name or no valid path between origin and target.

---

### Endpoint 2: Advance Voyage Simulation Tick
- **Method**: `POST`
- **Path**: `/voyage/{voyage_id}/tick`
- **Description**: Advances simulation clock by `tick_duration` hours, updates interpolated ship position, samples actual weather, and executes mid-edge threshold deterioration rerouting checks.

#### Request JSON Schema (`TickRequest`)
```json
{
  "tick_duration": 0.08333
}
```
*(Note: `0.08333` hours = 5 minutes)*

#### Response JSON Schema (`TickResponse`)
```json
{
  "voyage_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "current_time": 0.08333,
  "current_node_id": "Mumbai",
  "current_lat": 18.92,
  "current_lon": 72.82,
  "is_completed": false,
  "active_route_nodes": [
    "Mumbai",
    "WP_Laccadive",
    "Colombo",
    "WP_Bay_of_Bengal",
    "WP_Malacca_West",
    "Medan",
    "WP_Malacca_Strait",
    "Singapore"
  ],
  "rerouted_in_tick": true,
  "new_route_cost": 17.196
}
```

#### Errors
- `404 Not Found`: `voyage_id` does not exist in memory.

---

### Endpoint 3: Inspect Current Voyage Route
- **Method**: `GET`
- **Path**: `/voyage/{voyage_id}/route`
- **Description**: Returns detailed `RoutingResult` object for the active route of the given voyage.

#### Response JSON Schema (`RoutingResult`)
```json
{
  "path": [ ... ],
  "total_cost": 17.1960,
  "total_time": 206.33,
  "total_fuel": 248.44,
  "total_safety": 6.01,
  "total_congestion": 452.20,
  "strategy_name": "BALANCED"
}
```

#### Errors
- `404 Not Found`: `voyage_id` does not exist in memory.

---

## 3. Intended Frontend ↔ Backend Integration Flow

```
[User Selects Parameters] -> POST /voyage/init -> [Store voyage_id, Render initial polyline]
                               │
               Loop every N seconds (or user click "Step")
                               │
                       POST /voyage/{id}/tick
                               │
          ┌────────────────────┴────────────────────┐
  rerouted_in_tick == false                 rerouted_in_tick == true
          │                                         │
  [Update marker (lat, lon)]             [Update marker + Redraw polyline]
```

---

## 4. Planned Endpoints (TODO — NOT IMPLEMENTED)

The following endpoints are planned for future web dashboard features:

- `GET /voyage/{voyage_id}/history` (TODO — NOT IMPLEMENTED): Retrieve complete time-series history log of ship position, speed, and weather intensity.
- `DELETE /voyage/{voyage_id}` (TODO — NOT IMPLEMENTED): Terminate and purge voyage session from memory.

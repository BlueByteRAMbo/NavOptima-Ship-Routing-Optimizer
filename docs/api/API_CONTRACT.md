# NavOptima API Contract Specification

## Base URL
`/api`

## Endpoints

### 1. Health Check
- **Endpoint**: `GET /api/health`
- **Description**: Verify backend service availability and status.
- **Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 2. Ports List
- **Endpoint**: `GET /api/ports`
- **Description**: Returns all 15 supported strategic port locations and metadata.
- **Response**: Array of Port objects.

### 3. Environment Grid
- **Endpoint**: `GET /api/environment`
- **Description**: Returns unified Indian Ocean EnvironmentCell data matching the schema.
- **Query Parameters**: `min_lat`, `max_lat`, `min_lon`, `max_lon`, `timestamp`

### 4. Security Risk
- **Endpoint**: `GET /api/security`
- **Description**: Returns security threat levels and conflict zone boundaries (ACLED integration).

### 5. Traffic Density
- **Endpoint**: `GET /api/traffic`
- **Description**: Returns maritime traffic congestion and AIS density layer data (GFW integration).

### 6. Data Sources
- **Endpoint**: `GET /api/data-sources`
- **Description**: Returns metadata and ingestion timestamps for all active data feeds.

### 7. Route Optimization
- **Endpoint**: `POST /api/route`
- **Description**: Computes optimal route given origin, destination, vessel profile, and objective weights.
- **Request Body**:
```json
{
  "origin_port": "Mumbai, India",
  "destination_port": "Singapore, Singapore",
  "departure_time": "2026-08-17T12:00:00Z",
  "ship_type": "Container",
  "optimization_preferences": {
    "fuel_weight": 0.4,
    "time_weight": 0.4,
    "safety_weight": 0.2
  }
}
```

### 8. Simulation Event
- **Endpoint**: `POST /api/simulation/event`
- **Description**: Injects real-time dynamic events (e.g. storm development, piracy warning, port closure) for simulation and dynamic route recalculation.

# NavOptima Data Sources & Pipeline

## Environmental Scope
- **Region**: Unified Indian Ocean Environment Grid
- **Coverage**: Indian Ocean basin connecting Middle East, South Asia, Southeast Asia, East Africa, and Southern Africa.

## 15 Strategic Hub Ports
1. Mumbai, India
2. Mundra, India
3. Kochi, India
4. Colombo, Sri Lanka
5. Chattogram, Bangladesh
6. Yangon / Thilawa, Myanmar
7. Jebel Ali, UAE
8. Salalah, Oman
9. Mombasa, Kenya
10. Dar es Salaam, Tanzania
11. Port Louis, Mauritius
12. Durban, South Africa
13. Singapore, Singapore
14. Port Klang, Malaysia
15. Karachi, Pakistan

## Data Feeds & Ingestion
- **NOAA**: Atmospheric weather, surface wind velocity and direction vectors.
- **Copernicus Marine Service**: Significant wave height, peak wave period, ocean surface current components ($u, v$).
- **ACLED**: Maritime security incidents, piracy tracking, conflict risk indices.
- **Global Fishing Watch (GFW)**: AIS vessel traffic patterns, shipping lane density.
- **OpenStreetMap / Bathymetry**: Base map and land-sea ocean boundary masks.

## Common EnvironmentCell Schema
```json
{
  "lat": 15.0,
  "lon": 70.0,
  "is_ocean": true,
  "wind_speed": 14.2,
  "wind_direction": 240,
  "wave_height": 2.1,
  "wave_period": 8.2,
  "current_u": 0.4,
  "current_v": 0.2,
  "security_risk": 0.1,
  "traffic_density": 0.3,
  "timestamp": "2026-08-17T00:00:00Z",
  "sources": ["NOAA", "Copernicus", "ACLED", "GFW"],
  "data_status": {
    "weather": "nominal",
    "ocean": "nominal",
    "security": "nominal",
    "traffic": "nominal"
  }
}
```

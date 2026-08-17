# NavOptima System Architecture

## Overview
NavOptima (PSS07 Smart Maritime Route Optimizer) is an advanced decision-support platform designed to calculate safe, fuel-efficient, and multi-objective maritime routes across the Indian Ocean.

## High-Level Architecture

```
+-------------------------------------------------------------+
|                     Frontend (Web UI)                       |
|   - Map Visualization (Leaflet/MapLibre/DeckGL)             |
|   - Optimization & Parameter Controls                      |
|   - Analytics & Comparison Dashboards                       |
|   - Simulation Controls & Event Triggers                    |
+------------------------------+------------------------------+
                               | REST / JSON
+------------------------------v------------------------------+
|                     FastAPI Backend                         |
|   - /api/ports           - /api/environment                 |
|   - /api/route           - /api/simulation/event            |
|   - /api/security        - /api/traffic                     |
+------------------------------+------------------------------+
                               |
+------------------------------v------------------------------+
|                  Orchestration & Routing                    |
|   - Indian Ocean Grid Builder (Spatial Representation)      |
|   - Cost Formulation (Weather, Waves, Currents, Risk)       |
|   - A* Multi-Objective Routing Engine                       |
+------------------------------+------------------------------+
                               |
+------------------------------v------------------------------+
|                   Data Pipeline & Cache                     |
|   - NOAA (Wind/Weather)        - Copernicus (Waves/Currents)|
|   - ACLED (Security Risk)      - GFW (Traffic Density)      |
|   - 15 Strategic Hub Ports     - Indian Ocean Unified Grid  |
+-------------------------------------------------------------+
```

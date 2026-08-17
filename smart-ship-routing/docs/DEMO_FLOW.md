# SIH Hackathon Demo Flow & Presentation Script

This document details the presentation sequence and execution steps for demonstrating the Smart Ship Routing Engine.

---

## 1. Demo Overview

- **Voyage Pair**: Mumbai → Singapore
- **Optimization Strategy**: `BALANCED` ($w_{time}=0.35, w_{fuel}=0.25, w_{safety}=0.25, w_{congestion}=0.15$)
- **Simulation Clock**: 5-minute ticks ($0.08333$ hours)
- **Key Highlight**: Live mid-edge weather deterioration detection, time-dependent A* re-planning, and 5% hysteresis threshold acceptance.

---

## 2. Step-by-Step Presentation Flow

### Step 1: Initial Voyage Planning (T = 0)
1. Presenter configures voyage: Origin = `Mumbai`, Destination = `Singapore`, Strategy = `BALANCED`.
2. Initial route is computed under the calm weather forecast.
3. System displays the initial planned path:
   ```text
   Mumbai -> Kochi -> Colombo -> WP_Bay_of_Bengal -> WP_Malacca_West -> Medan -> WP_Malacca_Strait -> Singapore
   ```
4. Initial Metrics:
   - **Distance**: $2635.0 \text{ NM}$
   - **ETA**: $175.67 \text{ hours}$ ($7.32 \text{ days}$)
   - **Fuel**: $175.67 \text{ tons}$
   - **Safety Penalty**: $0.00$
   - **Evaluated Cost**: $12.9417$

---

### Step 2: Continuous Ticked Simulation Starts
1. Presenter clicks "Start Simulation" or triggers 5-minute clock ticks.
2. Vessel departs Mumbai along the edge `Mumbai -> Kochi`.
3. Telemetry updates continuously:
   ```text
   T+05 min (0.08h) | Position: (18.92°N, 72.82°E) | Segment: Mumbai->next (1.2nm) | Weather: 0.00
   ```

---

### Step 3: Mid-Edge Weather Deterioration Detection
1. As actual moving storm conditions advance ($\text{start\_lat}=6.0^\circ\text{N}, \text{start\_lon}=88.0^\circ\text{E}, \text{speed}=5.0\text{kt West}, \text{radius}=180\text{nm}, \text{intensity}=9.5$), weather on the upcoming active corridor `Colombo -> WP_Bay_of_Bengal` deteriorates.
2. Cheap deterioration check detects remaining cost increase ($18.2346 > 17.1960 \times 1.05$).
3. Time-dependent A* is invoked from `WP_Laccadive` at `eta_start`.

---

### Step 4: A* Re-Planning & Hysteresis Adoption
1. A* computes optimal alternative path bypassing the storm:
   ```text
   Mumbai -> WP_Laccadive -> Colombo -> WP_Bay_of_Bengal -> WP_Malacca_West -> Medan -> WP_Malacca_Strait -> Singapore
   ```
2. Cost Comparison:
   - **Old Remaining Cost**: $18.2346$
   - **New Remaining Cost**: $17.1960$
   - **Cost Improvement**: $5.70\%$
   - **Threshold**: $5.0\%$
3. Hysteresis evaluates $5.70\% > 5.0\%$ $\rightarrow$ **✓ REROUTE ACCEPTED**.

---

### Step 5: Active Route Update
1. Active route updates seamlessly while vessel is mid-edge ($1.2 \text{ NM}$ out of Mumbai).
2. Updated Metrics:
   - **New Route**: `Mumbai -> WP_Laccadive -> Colombo -> WP_Bay_of_Bengal...`
   - **New Total Cost**: $17.1960$
   - **New ETA**: $206.33 \text{ hours}$
   - **New Fuel**: $248.44 \text{ tons}$
   - **Safety Penalty**: $6.01$ (Dramatically safer than attempting the storm corridor)

---

## 3. Running the Demo Command

To run the complete demonstration in CLI mode:

```bash
python3 run_demo.py
```

To run all automated verification tests:

```bash
pytest -q
```

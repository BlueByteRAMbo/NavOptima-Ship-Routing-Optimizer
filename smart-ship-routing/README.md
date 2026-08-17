# Smart Ship Routing Engine (SIH 2026 PSS07)

High-performance, time-dependent maritime routing and dynamic rerouting engine for vessel voyage optimization in the Indian Ocean region.

---

## 1. Features
- **Time-Dependent A***: Optimal maritime pathfinding considering moving Gaussian storm weather systems.
- **Pareto State Tracking**: Exact arrival-time state tracking `(g_cost, arrival_time)` to avoid lossy integer bucket state pruning.
- **Multi-Objective Optimization**: Supports `FASTEST`, `SAFEST`, `LEAST_CONGESTED`, and `BALANCED` cost functions.
- **Dynamic Rerouting**: Ticked simulation clock with continuous mid-edge position interpolation and 5% hysteresis barrier.
- **FastAPI REST API**: Endpoints for voyage initialization, simulation clock stepping, and route inspection.

---

## 2. Requirements & Setup

### Prerequisites
- **Python**: Version `3.10` or higher (tested on Python `3.13`).

### Installation
```bash
# 1. Clone the repository
git clone <REPOSITORY_URL>
cd smart-ship-routing

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 3. Running Verification & Demos

### Run Unit Tests
```bash
pytest -q
```
*(All 18 tests should pass in < 0.1s)*

### Run Presentation Demo
```bash
python3 run_demo.py
```
*(Executes 5-minute ticked simulation showing mid-edge weather deterioration and hysteresis adoption)*

### Run Adversarial Regression Suite
```bash
python3 adversarial_verify.py
```
*(Verifies A* vs Exhaustive search, time-bucket pruning, heuristic admissibility, determinism)*

### Start FastAPI Backend API
```bash
uvicorn src.api:app --reload --port 8000
```
*(Interactive API documentation available at http://localhost:8000/docs)*

---

## 4. Documentation & Developer Handoff

For new developers, frontend engineers, and AI agents taking over this repository:

- 📄 **[Developer Handoff Guide](docs/PROJECT_HANDOFF.md)**: Canonical handoff document detailing architecture, contracts, and frozen components.
- 🔌 **[API Integration Guide](docs/API_INTEGRATION.md)**: Complete request/response schemas for `/voyage/init`, `/tick`, `/route`.
- 🎬 **[Demo Flow Guide](docs/DEMO_FLOW.md)**: Hackathon presentation script and sequence.
- 📦 **[Git & GitHub Guide](docs/GITHUB_HANDOFF.md)**: Repository structure, commit conventions, and `.gitignore` rules.
- 📊 **[Implementation Status](docs/IMPLEMENTATION_STATUS.md)**: Test verification logs and project status.

---

## 5. License
Developed for SIH 2026 Problem Statement PSS07.

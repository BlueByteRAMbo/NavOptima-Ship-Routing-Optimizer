# Git & GitHub Repository Handoff Guide

This document defines repository structure conventions, `.gitignore` rules, and guidelines for pushing and maintaining this repository on GitHub.

---

## 1. Repository Structure

```
smart-ship-routing/
├── docs/
│   ├── PROJECT_HANDOFF.md       # Primary developer handoff document
│   ├── IMPLEMENTATION_STATUS.md # Routing core status and verification history
│   ├── API_INTEGRATION.md       # FastAPI endpoints documentation
│   ├── DEMO_FLOW.md             # Hackathon presentation script & sequence
│   └── GITHUB_HANDOFF.md        # Git conventions & handoff guidelines
├── src/
│   ├── __init__.py
│   ├── api.py                   # FastAPI backend server
│   ├── haversine.py             # Great-circle distance calculations
│   ├── models.py                # Pydantic graph, node, and edge schemas
│   ├── optimizer.py             # Objective functions, weights, and modifiers
│   ├── router.py                # Time-dependent A* engine (FROZEN)
│   ├── simulation.py            # Voyage simulation state machine (FROZEN)
│   └── weather.py               # Deterministic Gaussian weather engine (FROZEN)
├── tests/
│   └── test_routing.py          # 18 unit & integration tests (FROZEN)
├── traffic.json                 # Graph topology (17 nodes, 44 edges) (FROZEN)
├── adversarial_verify.py        # 11-section adversarial verifier
├── run_demo.py                  # Presentation demonstration script
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore patterns
└── README.md                    # Project README and quickstart
```

---

## 2. Files to Commit

- All files in `src/`, `tests/`, `docs/`.
- `traffic.json`, `adversarial_verify.py`, `run_demo.py`.
- `requirements.txt`, `README.md`, `.gitignore`.

---

## 3. Files MUST NOT Be Committed

The following files and directories must be excluded from Git tracking:

```gitignore
# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
.venv/
venv/
ENV/

# Test & IDE caches
.pytest_cache/
.coverage
htmlcov/
.idea/
.vscode/

# Node / Frontend (when added)
node_modules/
dist/
build/
.next/

# Environment files & logs
.env
*.log
.DS_Store
```

---

## 4. Portable Pathing Guarantee

> **CRITICAL**: No machine-specific absolute paths (e.g., `/Users/lavesh/...` or `C:\Users\...`) should exist in project code or scripts.

All scripts use relative paths anchored to `Path(__file__).resolve().parent` or `os.path.dirname(__file__)`.

---

## 5. Pushing to GitHub (Initial Handoff Commands)

```bash
# 1. Initialize git (if needed)
git init

# 2. Add files
git add .

# 3. Commit handoff baseline
git commit -m "feat: complete routing core verification & developer handoff documentation"

# 4. Set main branch and push
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```

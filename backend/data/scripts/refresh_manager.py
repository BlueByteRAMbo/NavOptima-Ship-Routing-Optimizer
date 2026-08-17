"""
refresh_manager.py
===================
Makes the data pipeline robust to periodic/real-time upstream updates,
WITHOUT changing the EnvironmentCell schema, ports schema, or any API
contract (rule: DO NOT silently change the shared schema).

What this adds:
  1. Per-source refresh intervals (configurable below).
  2. Staleness tracking in metadata/refresh_state.json -- lets the frontend's
     "Data Sources" panel show real staleness instead of a static label.
  3. ATOMIC writes: every rebuild writes to a .tmp file then os.replace()s
     it over the live cache file. FastAPI/backend readers never see a
     half-written environment.json mid-refresh -- this is the main
     "robust to dynamic updates" guarantee for a hackathon without a real
     job queue.
  4. Failure isolation: if one source's ingest script raises/fails, that
     source's data_status stays at its last-good value (CACHED/MOCK) and
     the grid rebuild still runs with whatever is available -- consistent
     with the project's "one API failure must not block the demo" rule.

This does NOT introduce a message queue, Kubernetes CronJob, or streaming
infra -- per "do not over-engineer" (section 32), a simple interval loop
(or a single `--once` invocation wired into cron/systemd-timer/GitHub
Actions schedule) is sufficient for a hackathon.

Usage:
    # one-shot refresh of everything (safe to call from cron/GitHub Actions)
    python refresh_manager.py --once

    # continuous loop, each source refreshed on its own interval
    python refresh_manager.py --loop

    # refresh a single source only
    python refresh_manager.py --once --source noaa
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
STATE_PATH = os.path.join(METADATA_DIR, "refresh_state.json")

# Refresh cadence per source. NOAA/Copernicus update multiple times a day
# upstream; ACLED/GFW update far less often; ports congestion is simulated
# so it's refreshed on the same cadence as the grid rebuild for demo motion.
SOURCES = {
    "noaa":       {"script": os.path.join(SCRIPT_DIR, "noaa_ingest.py"),       "interval_s": 6 * 3600,  "args": []},
    "copernicus": {"script": os.path.join(SCRIPT_DIR, "copernicus_ingest.py"),  "interval_s": 6 * 3600,  "args": []},
    "acled":      {"script": os.path.join(SCRIPT_DIR, "acled_ingest.py"),       "interval_s": 24 * 3600, "args": ["--mock"]},
    "gfw":        {"script": os.path.join(SCRIPT_DIR, "gfw_ingest.py"),         "interval_s": 24 * 3600, "args": ["--mock"]},
    "ports":      {"script": os.path.join(SCRIPT_DIR, "ports_ingest.py"),       "interval_s": 3600,      "args": []},
}

GRID_BUILD_SCRIPT = os.path.join(SCRIPT_DIR, "build_environment_grid.py")


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)  # atomic


def is_due(state, source):
    last = state.get(source, {}).get("last_success_at")
    if last is None:
        return True
    last_dt = datetime.fromisoformat(last)
    age_s = (datetime.now(timezone.utc) - last_dt).total_seconds()
    return age_s >= SOURCES[source]["interval_s"]


def run_source(source, state):
    cfg = SOURCES[source]
    now = datetime.now(timezone.utc).isoformat()
    try:
        subprocess.run(
            [sys.executable, cfg["script"], *cfg["args"]],
            check=True, capture_output=True, text=True, timeout=300,
        )
        state[source] = {
            "last_attempt_at": now,
            "last_success_at": now,
            "status": "ok",
        }
        print(f"[refresh] {source}: OK")
    except Exception as ex:
        prev = state.get(source, {})
        state[source] = {
            "last_attempt_at": now,
            "last_success_at": prev.get("last_success_at"),  # keep last-good timestamp
            "status": f"failed: {ex}",
        }
        print(f"[refresh] {source}: FAILED ({ex}) -- keeping last-good data, demo continues")
    return state


def atomic_rebuild_grid():
    """
    Rebuilds environment.json/.parquet. build_environment_grid.py itself
    writes to *.tmp files and os.replace()s them over the live cache files,
    so a reader (FastAPI) opening the cache mid-refresh always sees either
    the old complete file or the new complete file, never a partial write.
    """
    subprocess.run([sys.executable, GRID_BUILD_SCRIPT], check=True)
    print("[refresh] environment grid rebuilt (atomic)")


def refresh_all(only_source=None):
    state = load_state()
    sources = [only_source] if only_source else list(SOURCES.keys())
    changed = False
    for source in sources:
        if is_due(state, source):
            state = run_source(source, state)
            changed = True
        else:
            print(f"[refresh] {source}: not due yet")
    save_state(state)
    if changed:
        atomic_rebuild_grid()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--source", choices=list(SOURCES.keys()))
    parser.add_argument("--poll-interval", type=int, default=300,
                         help="seconds between due-checks in --loop mode")
    args = parser.parse_args()

    if args.loop:
        print("[refresh] entering continuous refresh loop "
              f"(poll every {args.poll_interval}s)")
        while True:
            refresh_all(args.source)
            time.sleep(args.poll_interval)
    else:
        refresh_all(args.source)


if __name__ == "__main__":
    main()

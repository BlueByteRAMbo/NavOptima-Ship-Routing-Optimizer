import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = r"c:\Users\LDCN7492\Desktop\Nav Optima SHip Routing\NavOptima-Ship-Routing-Optimizer"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.orchestration.optimizer_service import (
    create_voyage,
    handle_simulation_event,
    calculate_optimal_route,
)
from backend.app.models.route import VoyageCreateRequest, SimulationEvent, RouteRequest

# 1. Test Port Calculation on newly expanded ports
for pair in [("mundra", "singapore"), ("durban", "chattogram"), ("karachi", "port_klang")]:
    req = RouteRequest(origin=pair[0], destination=pair[1], ship="container", optimization="balanced")
    res = calculate_optimal_route(req)
    print(f"Port Route {pair[0]} -> {pair[1]}: distance={res.distance_km}km, eta={res.eta_hours}h, supported={res.routing_supported}, sec_advisories={len(res.security_advisories)}")
    assert res.routing_supported is True, f"Failed for {pair}"

# 2. Test Security Disruption on Mumbai -> Colombo voyage
v_req = VoyageCreateRequest(origin="mumbai", destination="colombo", ship="container", optimization="balanced")
v_res = create_voyage(v_req)
print(f"\nVoyage Created: {v_res.voyage_id}, initial safety: {v_res.active_route.safety_score}%")

# Fire security event near Mumbai -> Colombo route
sec_event = SimulationEvent(
    voyage_id=v_res.voyage_id,
    type="security",
    lat=14.0,
    lon=73.5,
    radius_km=150.0,
    severity=0.85,
    label="Piracy Skiff Incident",
)

sim_res = handle_simulation_event(sec_event)
print(f"\nSecurity Simulation Result:")
print(f"  decision: {sim_res.decision}")
print(f"  safety_before: {sim_res.safety_before}% -> safety_after: {sim_res.safety_after}% (change: {sim_res.safety_change} pts)")
print(f"  max_security_risk: {sim_res.max_security_risk}")
print(f"  security_advisories count: {len(sim_res.security_advisories)}")
for adv in sim_res.security_advisories:
    print(f"    - {adv}")
print(f"  reason: {sim_res.reason}")

assert sim_res.decision == "SECURITY_ALERT"
assert sim_res.safety_change < 0
assert sim_res.max_security_risk >= 0.85
assert len(sim_res.security_advisories) > 0

print("\nALL BACKEND VERIFICATIONS FOR BUG 2 & BUG 3 PASSED!")

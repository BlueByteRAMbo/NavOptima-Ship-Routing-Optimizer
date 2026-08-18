/**
 * NavOptima — Shared Frontend Constants & Test Fixtures
 * Contains static vessel profiles, optimization presets, and simulation triggers.
 */

import type {
  Port,
  Ship,
  OptimizationPreset,
  SimulationEvent,
  DataSource,
} from '../types/maritime';

/* ═══════════════════════════════════════════════
   Ships / Vessels
   ═══════════════════════════════════════════════ */

export const DEMO_SHIPS: Ship[] = [
  { id: 'container', name: 'Container Vessel', type: 'container', speed_knots: 18, fuel_rate_mt_per_hour: 2.1, icon: '🚢' },
  { id: 'bulk', name: 'Bulk Carrier', type: 'bulk', speed_knots: 14, fuel_rate_mt_per_hour: 1.6, icon: '🚧' },
  { id: 'tanker', name: 'Oil Tanker', type: 'tanker', speed_knots: 15, fuel_rate_mt_per_hour: 2.8, icon: '🛢️' },
  { id: 'lng', name: 'LNG Carrier', type: 'lng', speed_knots: 19, fuel_rate_mt_per_hour: 3.2, icon: '⛽' },
];

/* ═══════════════════════════════════════════════
   Optimization Presets (4 required strategies)
   ═══════════════════════════════════════════════ */

export const OPTIMIZATION_PRESETS: OptimizationPreset[] = [
  {
    id: 'FASTEST',
    label: 'Fastest',
    description: 'Minimize transit time',
    icon: 'Zap',
    weights: { time: 1.0, fuel: 0.0, safety: 0.0 },
  },
  {
    id: 'SAFEST',
    label: 'Safest',
    description: 'Prioritize route safety',
    icon: 'Shield',
    weights: { time: 0.1, fuel: 0.1, safety: 0.8 },
  },
  {
    id: 'LEAST_CONGESTED',
    label: 'Least Congested',
    description: 'Avoid congested waterways',
    icon: 'Building',
    weights: { time: 0.2, fuel: 0.1, safety: 0.1 },
  },
  {
    id: 'BALANCED',
    label: 'Balanced',
    description: 'Balanced optimization',
    icon: 'Scale',
    weights: { time: 0.35, fuel: 0.25, safety: 0.25 },
  },
];

/* ═══════════════════════════════════════════════
   Simulation Presets
   ═══════════════════════════════════════════════ */

export const SIMULATION_PRESETS: Record<string, SimulationEvent> = {
  storm: {
    type: 'storm',
    lat: 14.46,
    lon: 74.53,
    radius_km: 300,
    severity: 0.9,
    label: 'Tropical Storm — Arabian Sea (Mumbai–Kochi Corridor)',
  },
  port_congestion: {
    type: 'port_congestion',
    lat: 6.95,
    lon: 79.84,
    radius_km: 50,
    severity: 0.85,
    label: 'Port Congestion Event',
  },
  security: {
    type: 'security',
    lat: 5.5,
    lon: 100.0,
    radius_km: 200,
    severity: 0.75,
    label: 'Security Alert — Malacca Strait',
  },
};

/* ═══════════════════════════════════════════════
   Test Fixture Ports
   ═══════════════════════════════════════════════ */

export const TEST_FIXTURE_PORTS: Port[] = [
  { id: 'mumbai', name: 'Mumbai', country: 'India', lat: 18.95, lon: 72.95, type: 'seaport', congestion: 0.58, waiting_hours: 11.9, utilization: 0.56, supported_in_routing: true },
  { id: 'colombo', name: 'Colombo', country: 'Sri Lanka', lat: 6.95, lon: 79.84, type: 'seaport', congestion: 0.56, waiting_hours: 13.6, utilization: 0.56, supported_in_routing: true },
  { id: 'singapore', name: 'Singapore', country: 'Singapore', lat: 1.29, lon: 103.85, type: 'seaport', congestion: 0.92, waiting_hours: 29.8, utilization: 0.96, supported_in_routing: true },
  { id: 'kochi', name: 'Kochi', country: 'India', lat: 9.9312, lon: 76.2673, type: 'seaport', congestion: 0.43, waiting_hours: 9.3, utilization: 0.42, supported_in_routing: true },
  { id: 'yangon', name: 'Yangon / Thilawa', country: 'Myanmar', lat: 16.6167, lon: 96.25, type: 'seaport', congestion: 0.51, waiting_hours: 12.4, utilization: 0.52, supported_in_routing: true },
];

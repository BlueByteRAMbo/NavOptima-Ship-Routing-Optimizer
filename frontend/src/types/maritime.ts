/**
 * NavOptima — Maritime Data & Routing Types
 * Matches the API contracts from the project specification.
 */

/* ═══════════════════════════════════════════════
   Environment
   ═══════════════════════════════════════════════ */

export interface EnvironmentCell {
  lat: number;
  lon: number;
  wind_speed: number;
  wind_direction: number;
  wave_height: number;
  wave_period: number;
  current_u: number;
  current_v: number;
  security_risk: number;
  traffic_density: number;
}

/* ═══════════════════════════════════════════════
   Ports
   ═══════════════════════════════════════════════ */

export interface Port {
  id: string;
  name: string;
  country: string;
  lat: number;
  lon: number;
  type: string;
  congestion: number;
  waiting_hours: number;
  utilization: number;
}

/* ═══════════════════════════════════════════════
   Ships / Vessels
   ═══════════════════════════════════════════════ */

export interface Ship {
  id: string;
  name: string;
  type: string;
  speed_knots: number;
  fuel_rate_mt_per_hour: number;
  icon: string;
}

/* ═══════════════════════════════════════════════
   Optimization
   ═══════════════════════════════════════════════ */

export type OptimizationMode = 'fastest' | 'safest' | 'fuel_efficient' | 'balanced';

export interface OptimizationPreset {
  id: OptimizationMode;
  label: string;
  description: string;
  icon: string;
  weights: {
    time: number;
    fuel: number;
    safety: number;
  };
}

/* ═══════════════════════════════════════════════
   Route
   ═══════════════════════════════════════════════ */

export interface RouteRequest {
  origin: string;
  destination: string;
  ship: string;
  optimization: OptimizationMode;
}

export interface RouteResponse {
  coordinates: [number, number][];
  distance_km: number;
  eta_hours: number;
  fuel_mt: number;
  safety_score: number;
  reason: string;
}

/* ═══════════════════════════════════════════════
   Simulation
   ═══════════════════════════════════════════════ */

export type SimulationEventType = 'storm' | 'port_congestion' | 'security';

export interface SimulationEvent {
  type: SimulationEventType;
  lat: number;
  lon: number;
  radius_km: number;
  severity: number;
  label?: string;
}

export interface SimulationResponse {
  old_route: [number, number][];
  new_route: [number, number][];
  reason: string;
  eta_change_hours: number;
  fuel_change_mt: number;
  safety_change: number;
}

/* ═══════════════════════════════════════════════
   Data Sources
   ═══════════════════════════════════════════════ */

export interface DataSource {
  source: string;
  dataset: string;
  region: string;
  variables: string[];
  status: string;
  note: string;
}

/* ═══════════════════════════════════════════════
   Event Feed
   ═══════════════════════════════════════════════ */

export interface FeedEvent {
  id: string;
  timestamp: Date;
  type: 'route_calculated' | 'simulation_event' | 'reroute' | 'info' | 'warning' | 'error';
  title: string;
  description: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

/* ═══════════════════════════════════════════════
   Application State
   ═══════════════════════════════════════════════ */

export interface AppState {
  // Selections
  originPort: string;
  destinationPort: string;
  selectedShip: string;
  optimizationMode: OptimizationMode;

  // Route data
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;

  // Simulation
  activeSimulation: SimulationEvent | null;
  simulationResult: SimulationResponse | null;

  // UI state
  isCalculating: boolean;
  isSimulating: boolean;
  showWeatherLayer: boolean;
  showRiskLayer: boolean;
  showPortLabels: boolean;

  // Feed
  events: FeedEvent[];
}

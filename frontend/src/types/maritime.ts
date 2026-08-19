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
  supported_in_routing?: boolean;
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

export type OptimizationMode = 'FASTEST' | 'SAFEST' | 'LEAST_CONGESTED' | 'BALANCED' | 'fastest' | 'safest' | 'least_congested' | 'balanced';

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
  data_mode?: 'HYBRID' | 'MOCK';
}

export interface RouteResponse {
  coordinates: [number, number][];
  distance_km: number;
  eta_hours: number;
  fuel_mt: number;
  safety_score: number;
  congestion_score?: number;
  total_cost?: number;
  reason: string;
  strategy?: string;
  data_mode?: string;
  data_status?: string;
  routing_supported?: boolean;
  path_nodes?: string[];
  security_advisories?: string[];
  max_security_risk?: number;
  intersected_security_zones?: any[];
}

/* ═══════════════════════════════════════════════
   Simulation & Voyage Lifecycle
   ═══════════════════════════════════════════════ */

export type SimulationEventType = 'storm' | 'port_congestion' | 'security';

export interface SimulationEvent {
  voyage_id?: string;
  type: SimulationEventType;
  lat: number;
  lon: number;
  radius_km: number;
  severity: number;
  label?: string;
}

export interface SimulationResponse {
  voyage_id?: string;
  origin?: string;
  destination?: string;
  spatially_relevant?: boolean;
  old_route: [number, number][];
  new_route: [number, number][];
  reason: string;
  eta_change_hours: number;
  fuel_change_mt: number;
  safety_change: number;
  congestion_change?: number;
  rerouted?: boolean;
  active_route?: RouteResponse;

  // Structured Decision Log Fields (Phase 14 Section I)
  event_type?: string;
  timestamp?: number;
  severity?: number;
  eta_before?: number;
  eta_after?: number;
  fuel_before?: number;
  fuel_after?: number;
  safety_before?: number;
  safety_after?: number;
  cost_improvement_percent?: number;
  hysteresis_threshold_percent?: number;
  decision?: string;
  security_advisories?: string[];
  max_security_risk?: number;
  intersected_security_zones?: any[];
}

export interface VoyageCreateRequest {
  origin: string;
  destination: string;
  ship?: string;
  optimization?: OptimizationMode;
  data_mode?: 'HYBRID' | 'MOCK';
  hysteresis_threshold?: number;
}

export interface VoyageStateResponse {
  voyage_id: string;
  origin: string;
  destination: string;
  ship: string;
  strategy: string;
  data_mode: string;
  current_time: number;
  current_lat: number;
  current_lon: number;
  current_node_id: string;
  is_completed: boolean;
  active_route: RouteResponse;
  history?: any[];
  reroute_events?: any[];
}

export interface TickResponse {
  voyage_id: string;
  current_time: number;
  current_node_id: string;
  current_lat: number;
  current_lon: number;
  is_completed: boolean;
  active_route_nodes: string[];
  active_route: RouteResponse;
  rerouted_in_tick: boolean;
  new_route_cost?: number;
  reroute_event?: any;
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
  simulation_result?: SimulationResponse;
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
  dataMode: 'HYBRID' | 'MOCK';

  // Route data
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;

  // Voyage / Simulation state
  activeVoyage: VoyageStateResponse | null;
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

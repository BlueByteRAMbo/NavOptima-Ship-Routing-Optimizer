/**
 * Maritime Data & Routing Types (Placeholder)
 */

export interface EnvironmentCell {
  lat: number;
  lon: number;
  is_ocean: boolean;
  wind_speed: number;
  wind_direction: number;
  wave_height: number;
  wave_period: number;
  current_u: number;
  current_v: number;
  security_risk: number;
  traffic_density: number;
  timestamp: string;
  sources: string[];
  data_status: Record<string, unknown>;
}

export interface Port {
  id: string;
  name: string;
  country: string;
  lat: number;
  lon: number;
}

export interface RouteRequest {
  origin_port_id: string;
  destination_port_id: string;
  departure_time: string;
  vessel_id: string;
  weights?: {
    fuel?: number;
    time?: number;
    safety?: number;
  };
}

export interface RouteResponse {
  route_id: string;
  waypoints: Array<[number, number]>;
  total_distance_nm: number;
  estimated_time_hours: number;
  estimated_fuel_tonnes: number;
  risk_score: number;
}

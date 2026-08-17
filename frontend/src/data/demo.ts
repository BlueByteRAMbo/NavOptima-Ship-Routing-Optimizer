/**
 * NavOptima — Demo Data
 * Uses real port data from backend/data/cache/ports.json.
 * Provides complete demo datasets for standalone frontend operation.
 */

import type {
  Port,
  Ship,
  OptimizationPreset,
  RouteResponse,
  SimulationEvent,
  SimulationResponse,
  EnvironmentCell,
  DataSource,
} from '../types/maritime';

/* ═══════════════════════════════════════════════
   Ports (15 Indian Ocean ports — from backend)
   ═══════════════════════════════════════════════ */

export const DEMO_PORTS: Port[] = [
  { id: 'mumbai', name: 'Mumbai', country: 'India', lat: 18.95, lon: 72.95, type: 'seaport', congestion: 0.58, waiting_hours: 11.9, utilization: 0.56 },
  { id: 'mundra', name: 'Mundra', country: 'India', lat: 22.7395, lon: 69.7076, type: 'seaport', congestion: 0.34, waiting_hours: 11.8, utilization: 0.36 },
  { id: 'kochi', name: 'Kochi', country: 'India', lat: 9.9312, lon: 76.2673, type: 'seaport', congestion: 0.43, waiting_hours: 9.3, utilization: 0.42 },
  { id: 'colombo', name: 'Colombo', country: 'Sri Lanka', lat: 6.95, lon: 79.84, type: 'seaport', congestion: 0.56, waiting_hours: 13.6, utilization: 0.56 },
  { id: 'chattogram', name: 'Chattogram', country: 'Bangladesh', lat: 22.28, lon: 91.83, type: 'seaport', congestion: 0.51, waiting_hours: 12.2, utilization: 0.52 },
  { id: 'yangon', name: 'Yangon / Thilawa', country: 'Myanmar', lat: 16.6167, lon: 96.25, type: 'seaport', congestion: 0.51, waiting_hours: 12.4, utilization: 0.52 },
  { id: 'jebel_ali', name: 'Jebel Ali', country: 'UAE', lat: 25.0118, lon: 55.0618, type: 'seaport', congestion: 0.81, waiting_hours: 16.3, utilization: 0.84 },
  { id: 'salalah', name: 'Salalah', country: 'Oman', lat: 17.0151, lon: 54.0924, type: 'seaport', congestion: 0.44, waiting_hours: 11.8, utilization: 0.41 },
  { id: 'mombasa', name: 'Mombasa', country: 'Kenya', lat: -4.0435, lon: 39.6682, type: 'seaport', congestion: 0.64, waiting_hours: 17.1, utilization: 0.60 },
  { id: 'dar_es_salaam', name: 'Dar es Salaam', country: 'Tanzania', lat: -6.8235, lon: 39.2695, type: 'seaport', congestion: 0.42, waiting_hours: 15.5, utilization: 0.43 },
  { id: 'port_louis', name: 'Port Louis', country: 'Mauritius', lat: -20.1609, lon: 57.5012, type: 'seaport', congestion: 0.36, waiting_hours: 12.5, utilization: 0.36 },
  { id: 'durban', name: 'Durban', country: 'South Africa', lat: -29.8587, lon: 31.0218, type: 'seaport', congestion: 0.54, waiting_hours: 14.9, utilization: 0.55 },
  { id: 'singapore', name: 'Singapore', country: 'Singapore', lat: 1.29, lon: 103.85, type: 'seaport', congestion: 0.92, waiting_hours: 29.8, utilization: 0.96 },
  { id: 'port_klang', name: 'Port Klang', country: 'Malaysia', lat: 2.9979, lon: 101.3919, type: 'seaport', congestion: 0.72, waiting_hours: 24.5, utilization: 0.67 },
  { id: 'karachi', name: 'Karachi', country: 'Pakistan', lat: 24.8482, lon: 66.9931, type: 'seaport', congestion: 0.40, waiting_hours: 10.3, utilization: 0.36 },
];

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
   Optimization Presets
   ═══════════════════════════════════════════════ */

export const OPTIMIZATION_PRESETS: OptimizationPreset[] = [
  {
    id: 'fastest',
    label: 'Fastest',
    description: 'Minimize transit time',
    icon: 'Zap',
    weights: { time: 0.8, fuel: 0.1, safety: 0.1 },
  },
  {
    id: 'safest',
    label: 'Safest',
    description: 'Prioritize route safety',
    icon: 'Shield',
    weights: { time: 0.1, fuel: 0.1, safety: 0.8 },
  },
  {
    id: 'fuel_efficient',
    label: 'Fuel Efficient',
    description: 'Minimize fuel consumption',
    icon: 'Leaf',
    weights: { time: 0.1, fuel: 0.8, safety: 0.1 },
  },
  {
    id: 'balanced',
    label: 'Balanced',
    description: 'Balanced optimization',
    icon: 'Scale',
    weights: { time: 0.33, fuel: 0.34, safety: 0.33 },
  },
];

/* ═══════════════════════════════════════════════
   Demo Routes
   ═══════════════════════════════════════════════ */

export const DEMO_ROUTES: Record<string, Record<string, RouteResponse>> = {
  // Mumbai → Colombo routes by optimization
  'mumbai_colombo': {
    fastest: {
      coordinates: [
        [18.95, 72.95],
        [17.8, 73.2],
        [16.2, 73.8],
        [14.5, 74.5],
        [12.5, 75.5],
        [10.5, 76.8],
        [8.5, 78.5],
        [6.95, 79.84],
      ],
      distance_km: 1480,
      eta_hours: 38.5,
      fuel_mt: 80.9,
      safety_score: 82,
      reason: 'Direct coastal route minimizing transit time. Passes through moderate wave zones near the Malabar coast but maintains fastest heading.',
    },
    safest: {
      coordinates: [
        [18.95, 72.95],
        [17.5, 72.5],
        [15.5, 72.0],
        [13.5, 72.5],
        [11.5, 74.0],
        [9.5, 76.0],
        [7.8, 78.0],
        [6.95, 79.84],
      ],
      distance_km: 1680,
      eta_hours: 47.2,
      fuel_mt: 99.1,
      safety_score: 95,
      reason: 'Offshore route avoiding coastal hazards and high-traffic zones. Wider arc west of the Laccadive Sea provides buffer from security zones and rough weather.',
    },
    fuel_efficient: {
      coordinates: [
        [18.95, 72.95],
        [17.2, 73.5],
        [15.0, 74.2],
        [13.0, 75.0],
        [11.0, 76.5],
        [9.0, 78.0],
        [7.5, 79.0],
        [6.95, 79.84],
      ],
      distance_km: 1540,
      eta_hours: 43.8,
      fuel_mt: 74.2,
      safety_score: 85,
      reason: 'Optimized for favorable ocean currents along the Indian western shelf. Leverages southward Somali current for reduced fuel burn.',
    },
    balanced: {
      coordinates: [
        [18.95, 72.95],
        [17.5, 73.5],
        [15.0, 74.0],
        [12.5, 75.0],
        [10.0, 77.0],
        [6.95, 79.84],
      ],
      distance_km: 1540,
      eta_hours: 43.2,
      fuel_mt: 87.4,
      safety_score: 88,
      reason: 'Balanced optimization weighing time, fuel efficiency, and safety equally. Moderate coastal distance with favorable current utilization.',
    },
  },
  // Mumbai → Singapore
  'mumbai_singapore': {
    balanced: {
      coordinates: [
        [18.95, 72.95],
        [16.0, 74.0],
        [12.0, 76.0],
        [8.0, 78.5],
        [6.0, 80.5],
        [4.0, 85.0],
        [3.0, 90.0],
        [2.0, 95.0],
        [1.29, 103.85],
      ],
      distance_km: 4520,
      eta_hours: 126.0,
      fuel_mt: 264.6,
      safety_score: 78,
      reason: 'Balanced route via the Laccadive Sea and Strait of Malacca. Avoids the Bay of Bengal weather systems where possible.',
    },
    fastest: {
      coordinates: [
        [18.95, 72.95],
        [15.0, 74.5],
        [10.0, 78.0],
        [6.0, 82.0],
        [3.5, 90.0],
        [2.0, 97.0],
        [1.29, 103.85],
      ],
      distance_km: 4380,
      eta_hours: 118.0,
      fuel_mt: 247.8,
      safety_score: 72,
      reason: 'Direct great-circle approximation for fastest transit. Passes through moderate monsoon-affected zones.',
    },
    safest: {
      coordinates: [
        [18.95, 72.95],
        [16.0, 72.0],
        [12.0, 74.0],
        [8.0, 76.5],
        [5.0, 79.0],
        [3.0, 85.0],
        [2.5, 92.0],
        [2.0, 98.0],
        [1.29, 103.85],
      ],
      distance_km: 4680,
      eta_hours: 134.0,
      fuel_mt: 281.4,
      safety_score: 91,
      reason: 'Wide arc south avoiding cyclone corridors and piracy zones. Longer but significantly safer passage.',
    },
    fuel_efficient: {
      coordinates: [
        [18.95, 72.95],
        [15.5, 74.0],
        [11.0, 77.0],
        [7.0, 80.0],
        [4.0, 87.0],
        [2.5, 95.0],
        [1.29, 103.85],
      ],
      distance_km: 4450,
      eta_hours: 128.0,
      fuel_mt: 230.0,
      safety_score: 76,
      reason: 'Follows favorable equatorial currents to minimize fuel. Slight detour south for current assistance.',
    },
  },
  // Jebel Ali → Mombasa
  'jebel_ali_mombasa': {
    balanced: {
      coordinates: [
        [25.0118, 55.0618],
        [23.0, 57.0],
        [20.0, 58.0],
        [16.0, 55.0],
        [12.0, 50.0],
        [8.0, 47.0],
        [4.0, 43.0],
        [0.0, 41.0],
        [-4.0435, 39.6682],
      ],
      distance_km: 4150,
      eta_hours: 115.0,
      fuel_mt: 241.5,
      safety_score: 71,
      reason: 'Standard Gulf of Aden transit with security corridor routing. Moderate risk from the Bab el-Mandeb approach.',
    },
    fastest: {
      coordinates: [
        [25.0118, 55.0618],
        [22.0, 57.5],
        [18.0, 56.0],
        [13.0, 51.0],
        [8.0, 47.0],
        [2.0, 42.0],
        [-4.0435, 39.6682],
      ],
      distance_km: 4000,
      eta_hours: 108.0,
      fuel_mt: 226.8,
      safety_score: 65,
      reason: 'Direct route through the Gulf of Aden. Faster but higher exposure to security risk zones.',
    },
    safest: {
      coordinates: [
        [25.0118, 55.0618],
        [23.5, 58.0],
        [20.0, 62.0],
        [15.0, 60.0],
        [10.0, 55.0],
        [5.0, 48.0],
        [0.0, 43.0],
        [-4.0435, 39.6682],
      ],
      distance_km: 4600,
      eta_hours: 132.0,
      fuel_mt: 277.2,
      safety_score: 88,
      reason: 'Eastern detour avoiding the Gulf of Aden piracy corridor. Significantly longer but greatly reduced security exposure.',
    },
    fuel_efficient: {
      coordinates: [
        [25.0118, 55.0618],
        [22.5, 57.0],
        [19.0, 57.5],
        [14.5, 53.0],
        [9.0, 48.0],
        [3.0, 43.0],
        [-4.0435, 39.6682],
      ],
      distance_km: 4100,
      eta_hours: 118.0,
      fuel_mt: 215.0,
      safety_score: 68,
      reason: 'Leverages favorable Somali Current patterns for fuel savings along the East African coast.',
    },
  },
};

/* ═══════════════════════════════════════════════
   Simulation Presets & Responses
   ═══════════════════════════════════════════════ */

export const SIMULATION_PRESETS: Record<string, SimulationEvent> = {
  storm: {
    type: 'storm',
    lat: 12.0,
    lon: 75.0,
    radius_km: 150,
    severity: 0.9,
    label: 'Tropical Storm — Arabian Sea',
  },
  port_congestion: {
    type: 'port_congestion',
    lat: 6.95,
    lon: 79.84,
    radius_km: 50,
    severity: 0.85,
    label: 'Severe Congestion — Colombo Port',
  },
  security: {
    type: 'security',
    lat: 12.5,
    lon: 47.5,
    radius_km: 200,
    severity: 0.75,
    label: 'Security Alert — Gulf of Aden',
  },
};

export const DEMO_SIMULATION_RESPONSES: Record<string, SimulationResponse> = {
  storm: {
    old_route: [
      [18.95, 72.95],
      [17.5, 73.5],
      [15.0, 74.0],
      [12.5, 75.0],
      [10.0, 77.0],
      [6.95, 79.84],
    ],
    new_route: [
      [18.95, 72.95],
      [17.5, 72.5],
      [15.0, 71.5],
      [13.0, 71.0],
      [11.0, 73.0],
      [9.0, 76.0],
      [7.5, 78.5],
      [6.95, 79.84],
    ],
    reason: 'Severe tropical storm detected at 12.0°N, 75.0°E with 150km radius. Route diverted westward to avoid dangerous wave heights (>6m) and wind speeds (>45 kts). New route adds ~2.4h transit time but eliminates storm exposure.',
    eta_change_hours: 2.4,
    fuel_change_mt: 4.1,
    safety_change: 16,
  },
  port_congestion: {
    old_route: [
      [18.95, 72.95],
      [17.5, 73.5],
      [15.0, 74.0],
      [12.5, 75.0],
      [10.0, 77.0],
      [6.95, 79.84],
    ],
    new_route: [
      [18.95, 72.95],
      [17.5, 73.5],
      [15.0, 74.0],
      [12.5, 75.0],
      [10.0, 77.0],
      [9.9312, 76.2673],
    ],
    reason: 'Colombo port congestion surged to 95% capacity with 40+ hour wait times. Route redirected to Kochi as alternative destination. Kochi currently at 43% congestion with ~9h wait time.',
    eta_change_hours: -1.8,
    fuel_change_mt: -3.2,
    safety_change: 3,
  },
  security: {
    old_route: [
      [25.0118, 55.0618],
      [23.0, 57.0],
      [20.0, 58.0],
      [16.0, 55.0],
      [12.0, 50.0],
      [8.0, 47.0],
      [4.0, 43.0],
      [0.0, 41.0],
      [-4.0435, 39.6682],
    ],
    new_route: [
      [25.0118, 55.0618],
      [23.5, 58.0],
      [20.0, 62.0],
      [15.0, 60.0],
      [10.0, 55.0],
      [5.0, 48.0],
      [0.0, 43.0],
      [-4.0435, 39.6682],
    ],
    reason: 'Security incident reported in Gulf of Aden (12.5°N, 47.5°E) with 200km exclusion zone. Route diverted east via the Arabian Sea to maintain safe distance from threat area.',
    eta_change_hours: 8.5,
    fuel_change_mt: 18.2,
    safety_change: 22,
  },
};

/* ═══════════════════════════════════════════════
   Environment Grid (sample cells along routes)
   ═══════════════════════════════════════════════ */

export const DEMO_ENVIRONMENT: EnvironmentCell[] = [
  { lat: 18.0, lon: 73.0, wind_speed: 8.2, wind_direction: 225, wave_height: 1.2, wave_period: 6.5, current_u: 0.15, current_v: -0.08, security_risk: 0.05, traffic_density: 0.45 },
  { lat: 16.0, lon: 73.5, wind_speed: 10.5, wind_direction: 240, wave_height: 1.6, wave_period: 7.2, current_u: 0.20, current_v: -0.12, security_risk: 0.03, traffic_density: 0.30 },
  { lat: 14.0, lon: 74.0, wind_speed: 14.2, wind_direction: 240, wave_height: 2.1, wave_period: 8.2, current_u: 0.40, current_v: 0.20, security_risk: 0.10, traffic_density: 0.25 },
  { lat: 12.0, lon: 75.0, wind_speed: 16.8, wind_direction: 255, wave_height: 2.8, wave_period: 9.0, current_u: 0.35, current_v: 0.15, security_risk: 0.08, traffic_density: 0.20 },
  { lat: 10.0, lon: 76.5, wind_speed: 12.1, wind_direction: 210, wave_height: 1.9, wave_period: 7.8, current_u: 0.25, current_v: 0.10, security_risk: 0.04, traffic_density: 0.35 },
  { lat: 8.0, lon: 78.0, wind_speed: 9.4, wind_direction: 200, wave_height: 1.4, wave_period: 6.8, current_u: 0.18, current_v: 0.05, security_risk: 0.02, traffic_density: 0.40 },
  { lat: 6.0, lon: 80.0, wind_speed: 7.3, wind_direction: 190, wave_height: 1.0, wave_period: 6.0, current_u: 0.12, current_v: 0.08, security_risk: 0.02, traffic_density: 0.55 },
  // Additional cells for broader coverage
  { lat: 20.0, lon: 68.0, wind_speed: 11.0, wind_direction: 260, wave_height: 1.8, wave_period: 7.5, current_u: 0.30, current_v: -0.10, security_risk: 0.06, traffic_density: 0.15 },
  { lat: 15.0, lon: 55.0, wind_speed: 18.5, wind_direction: 280, wave_height: 3.2, wave_period: 10.0, current_u: 0.50, current_v: 0.25, security_risk: 0.35, traffic_density: 0.10 },
  { lat: 10.0, lon: 50.0, wind_speed: 20.1, wind_direction: 270, wave_height: 3.8, wave_period: 11.0, current_u: 0.55, current_v: 0.30, security_risk: 0.60, traffic_density: 0.08 },
  { lat: 5.0, lon: 45.0, wind_speed: 15.0, wind_direction: 250, wave_height: 2.5, wave_period: 8.5, current_u: 0.40, current_v: 0.20, security_risk: 0.45, traffic_density: 0.12 },
  { lat: 0.0, lon: 42.0, wind_speed: 12.5, wind_direction: 230, wave_height: 2.0, wave_period: 7.8, current_u: 0.30, current_v: 0.15, security_risk: 0.25, traffic_density: 0.18 },
  { lat: -5.0, lon: 40.0, wind_speed: 8.0, wind_direction: 180, wave_height: 1.3, wave_period: 6.2, current_u: 0.20, current_v: 0.10, security_risk: 0.15, traffic_density: 0.22 },
  { lat: 2.0, lon: 95.0, wind_speed: 6.5, wind_direction: 170, wave_height: 0.8, wave_period: 5.5, current_u: 0.10, current_v: 0.05, security_risk: 0.03, traffic_density: 0.65 },
  { lat: 1.0, lon: 103.0, wind_speed: 5.2, wind_direction: 160, wave_height: 0.6, wave_period: 5.0, current_u: 0.08, current_v: 0.03, security_risk: 0.02, traffic_density: 0.90 },
];

/* ═══════════════════════════════════════════════
   Security Risk Zones
   ═══════════════════════════════════════════════ */

export const DEMO_RISK_ZONES: SimulationEvent[] = [
  { type: 'security', lat: 12.5, lon: 47.5, radius_km: 200, severity: 0.55, label: 'Gulf of Aden — Piracy Risk Zone' },
  { type: 'security', lat: 2.0, lon: 104.0, radius_km: 80, severity: 0.25, label: 'Strait of Malacca — Traffic Congestion' },
];

/* ═══════════════════════════════════════════════
   Data Sources
   ═══════════════════════════════════════════════ */

export const DEMO_DATA_SOURCES: DataSource[] = [
  {
    source: 'NOAA',
    dataset: 'GFS 0.25deg (via NOMADS)',
    region: 'Indian Ocean [lat -32..26, lon 25..105]',
    variables: ['wind_speed (m/s)', 'wind_direction (deg)'],
    status: 'MOCK',
    note: 'Simulated wind field based on climatological patterns',
  },
  {
    source: 'Copernicus Marine',
    dataset: 'GLOBAL_ANALYSISFORECAST_PHY + WAV',
    region: 'Indian Ocean [lat -32..26, lon 25..105]',
    variables: ['current_u', 'current_v', 'wave_height', 'wave_period'],
    status: 'MOCK',
    note: 'Simulated ocean currents and wave data',
  },
  {
    source: 'ACLED',
    dataset: 'Conflict events (Indian Ocean)',
    region: 'Indian Ocean coastal',
    variables: ['event_type', 'severity', 'location'],
    status: 'MOCK',
    note: 'Demo security zone, not real ACLED data',
  },
  {
    source: 'Global Fishing Watch',
    dataset: '4Wings API v3 (AIS)',
    region: 'Indian Ocean',
    variables: ['traffic_density'],
    status: 'MOCK',
    note: 'Port-proximity decay model for vessel density',
  },
  {
    source: 'Ports (curated)',
    dataset: '15-port canonical dataset',
    region: '15 Indian Ocean ports',
    variables: ['congestion', 'waiting_hours'],
    status: 'MOCK',
    note: 'Coordinates from public references, congestion simulated',
  },
  {
    source: 'OpenStreetMap',
    dataset: 'Basemap tiles',
    region: 'Global',
    variables: [],
    status: 'LIVE',
    note: 'Standard OSM tile usage via CartoDB dark theme',
  },
];

/* ═══════════════════════════════════════════════
   Helper: Get demo route for any port pair
   ═══════════════════════════════════════════════ */

export function getDemoRoute(
  origin: string,
  destination: string,
  optimization: string
): RouteResponse {
  const key = `${origin}_${destination}`;
  const reverseKey = `${destination}_${origin}`;
  const routes = DEMO_ROUTES[key] || DEMO_ROUTES[reverseKey];

  if (routes) {
    const route = routes[optimization] || routes['balanced'];
    if (route) {
      // If reverse key matched, reverse the coordinates
      if (!DEMO_ROUTES[key] && DEMO_ROUTES[reverseKey]) {
        return { ...route, coordinates: [...route.coordinates].reverse() };
      }
      return route;
    }
  }

  // Generate a fallback route between any two ports
  const originPort = DEMO_PORTS.find((p) => p.id === origin);
  const destPort = DEMO_PORTS.find((p) => p.id === destination);
  if (!originPort || !destPort) {
    return DEMO_ROUTES['mumbai_colombo']['balanced'];
  }

  const midLat = (originPort.lat + destPort.lat) / 2;
  const midLon = (originPort.lon + destPort.lon) / 2;
  const latDiff = Math.abs(originPort.lat - destPort.lat);
  const lonDiff = Math.abs(originPort.lon - destPort.lon);
  const distKm = Math.sqrt(latDiff * latDiff + lonDiff * lonDiff) * 111;

  return {
    coordinates: [
      [originPort.lat, originPort.lon],
      [originPort.lat + (midLat - originPort.lat) * 0.4, originPort.lon + (midLon - originPort.lon) * 0.3],
      [midLat + (Math.random() - 0.5) * 2, midLon],
      [destPort.lat + (midLat - destPort.lat) * 0.4, destPort.lon + (midLon - destPort.lon) * 0.3],
      [destPort.lat, destPort.lon],
    ],
    distance_km: Math.round(distKm),
    eta_hours: Math.round((distKm / 30) * 10) / 10,
    fuel_mt: Math.round((distKm / 30) * 2.1 * 10) / 10,
    safety_score: 75 + Math.round(Math.random() * 20),
    reason: `${OPTIMIZATION_PRESETS.find((p) => p.id === optimization)?.label || 'Balanced'} optimization between ${originPort.name} and ${destPort.name}.`,
  };
}

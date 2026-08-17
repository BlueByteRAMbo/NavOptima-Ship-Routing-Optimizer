/**
 * NavOptima API Client Service
 * Tries FastAPI backend first, falls back to demo data if unavailable.
 */

import type {
  RouteRequest,
  RouteResponse,
  SimulationEvent,
  SimulationResponse,
  Port,
  EnvironmentCell,
  DataSource,
} from '../types/maritime';

import {
  DEMO_PORTS,
  DEMO_ENVIRONMENT,
  DEMO_DATA_SOURCES,
  DEMO_SIMULATION_RESPONSES,
  getDemoRoute,
} from '../data/demo';

const API_BASE = '/api';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json();
}

/* ═══════════════════════════════════════════════
   Route
   ═══════════════════════════════════════════════ */

export async function calculateRoute(req: RouteRequest): Promise<RouteResponse> {
  try {
    return await apiFetch<RouteResponse>('/route', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  } catch {
    // Fallback to demo data
    await simulateDelay(800);
    return getDemoRoute(req.origin, req.destination, req.optimization);
  }
}

/* ═══════════════════════════════════════════════
   Simulation
   ═══════════════════════════════════════════════ */

export async function simulateEvent(event: SimulationEvent): Promise<SimulationResponse> {
  try {
    return await apiFetch<SimulationResponse>('/simulation/event', {
      method: 'POST',
      body: JSON.stringify(event),
    });
  } catch {
    await simulateDelay(1200);
    const response = DEMO_SIMULATION_RESPONSES[event.type];
    if (response) return response;
    // Generic fallback
    return {
      old_route: [],
      new_route: [],
      reason: `${event.type} event detected. Route recalculated.`,
      eta_change_hours: 1.5,
      fuel_change_mt: 3.0,
      safety_change: 10,
    };
  }
}

/* ═══════════════════════════════════════════════
   Ports
   ═══════════════════════════════════════════════ */

export async function getPorts(): Promise<Port[]> {
  try {
    return await apiFetch<Port[]>('/ports');
  } catch {
    return DEMO_PORTS;
  }
}

/* ═══════════════════════════════════════════════
   Environment
   ═══════════════════════════════════════════════ */

export async function getEnvironment(limit: number = 1500): Promise<EnvironmentCell[]> {
  try {
    const query = limit > 0 ? `?limit=${limit}` : '';
    return await apiFetch<EnvironmentCell[]>(`/environment${query}`);
  } catch {
    return DEMO_ENVIRONMENT;
  }
}

/* ═══════════════════════════════════════════════
   Data Sources
   ═══════════════════════════════════════════════ */

export async function getDataSources(): Promise<DataSource[]> {
  try {
    return await apiFetch<DataSource[]>('/data-sources');
  } catch {
    return DEMO_DATA_SOURCES;
  }
}

/* ═══════════════════════════════════════════════
   Health Check
   ═══════════════════════════════════════════════ */

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

/* ═══════════════════════════════════════════════
   Helpers
   ═══════════════════════════════════════════════ */

function simulateDelay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

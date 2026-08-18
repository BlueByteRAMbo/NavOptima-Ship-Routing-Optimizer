/**
 * NavOptima API Client Service
 * Authoritative client communicating directly with FastAPI backend.
 * NO SILENT FALLBACKS TO MOCK DEMO DATA.
 */

import type {
  RouteRequest,
  RouteResponse,
  SimulationEvent,
  SimulationResponse,
  Port,
  EnvironmentCell,
  DataSource,
  VoyageCreateRequest,
  VoyageStateResponse,
  TickResponse,
} from '../types/maritime';

const API_BASE = '/api/v1';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let detail = '';
    try {
      const errJson = await res.json();
      detail = errJson.detail || errJson.message || '';
    } catch {
      detail = res.statusText;
    }
    throw new Error(`API error ${res.status}: ${detail || res.statusText}`);
  }
  return res.json();
}

/* ═══════════════════════════════════════════════
   Route
   ═══════════════════════════════════════════════ */

export async function calculateRoute(req: RouteRequest): Promise<RouteResponse> {
  return await apiFetch<RouteResponse>('/route', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/* ═══════════════════════════════════════════════
   Stateful Voyage Lifecycle
   ═══════════════════════════════════════════════ */

export async function initVoyage(req: VoyageCreateRequest): Promise<VoyageStateResponse> {
  return await apiFetch<VoyageStateResponse>('/voyages', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getVoyage(voyageId: string): Promise<VoyageStateResponse> {
  return await apiFetch<VoyageStateResponse>(`/voyages/${voyageId}`);
}

export async function tickVoyage(voyageId: string, tickDuration: number = 1.0): Promise<TickResponse> {
  return await apiFetch<TickResponse>(`/voyages/${voyageId}/tick`, {
    method: 'POST',
    body: JSON.stringify({ tick_duration: tickDuration }),
  });
}

export async function getVoyageRoute(voyageId: string): Promise<RouteResponse> {
  return await apiFetch<RouteResponse>(`/voyages/${voyageId}/route`);
}

/* ═══════════════════════════════════════════════
   Simulation Disruptions
   ═══════════════════════════════════════════════ */

export async function simulateEvent(event: SimulationEvent, voyageId?: string): Promise<SimulationResponse> {
  const path = voyageId ? `/voyages/${voyageId}/event` : '/simulation/event';
  return await apiFetch<SimulationResponse>(path, {
    method: 'POST',
    body: JSON.stringify({ ...event, voyage_id: voyageId }),
  });
}

/* ═══════════════════════════════════════════════
   Ports
   ═══════════════════════════════════════════════ */

export async function getPorts(): Promise<Port[]> {
  return await apiFetch<Port[]>('/ports');
}

/* ═══════════════════════════════════════════════
   Environment
   ═══════════════════════════════════════════════ */

export async function getEnvironment(): Promise<EnvironmentCell[]> {
  return await apiFetch<EnvironmentCell[]>('/environment');
}

/* ═══════════════════════════════════════════════
   Data Sources
   ═══════════════════════════════════════════════ */

export async function getDataSources(): Promise<DataSource[]> {
  return await apiFetch<DataSource[]>('/data-sources');
}

/* ═══════════════════════════════════════════════
   Health Check
   ═══════════════════════════════════════════════ */

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

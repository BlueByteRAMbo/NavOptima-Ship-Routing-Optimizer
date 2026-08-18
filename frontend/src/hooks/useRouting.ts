/**
 * useRouting — Route calculation and stateful voyage simulation hook
 * Direct backend integration with NO fake metric calculations.
 */

import { useState, useCallback } from 'react';
import type {
  RouteResponse,
  SimulationEvent,
  SimulationResponse,
  OptimizationMode,
  FeedEvent,
  VoyageStateResponse,
} from '../types/maritime';
import { calculateRoute, simulateEvent, initVoyage, tickVoyage as apiTickVoyage } from '../services/api';

interface UseRoutingReturn {
  // State
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
  simulationResult: SimulationResponse | null;
  activeSimulation: SimulationEvent | null;
  activeVoyage: VoyageStateResponse | null;
  dataMode: 'HYBRID' | 'MOCK';
  isCalculating: boolean;
  isSimulating: boolean;
  events: FeedEvent[];

  // Actions
  setDataMode: (mode: 'HYBRID' | 'MOCK') => void;
  computeRoute: (origin: string, destination: string, ship: string, optimization: OptimizationMode, dataMode?: 'HYBRID' | 'MOCK') => Promise<void>;
  triggerSimulation: (event: SimulationEvent) => Promise<void>;
  startVoyageSimulation: (origin: string, destination: string, ship: string, optimization: OptimizationMode) => Promise<void>;
  advanceVoyageTick: (tickHours?: number) => Promise<void>;
  clearSimulation: () => void;
  clearRoute: () => void;
  clearEvents: () => void;
  setActiveVoyage: React.Dispatch<React.SetStateAction<VoyageStateResponse | null>>;
  setCurrentRoute: React.Dispatch<React.SetStateAction<RouteResponse | null>>;
}

let eventCounter = 0;

function createEvent(
  type: FeedEvent['type'],
  title: string,
  description: string,
  severity?: FeedEvent['severity'],
  simulation_result?: SimulationResponse
): FeedEvent {
  return {
    id: `evt-${++eventCounter}`,
    timestamp: new Date(),
    type,
    title,
    description,
    severity,
    simulation_result,
  };
}

export function useRouting(): UseRoutingReturn {
  const [currentRoute, setCurrentRoute] = useState<RouteResponse | null>(null);
  const [previousRoute, setPreviousRoute] = useState<RouteResponse | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [activeSimulation, setActiveSimulation] = useState<SimulationEvent | null>(null);
  const [activeVoyage, setActiveVoyage] = useState<VoyageStateResponse | null>(null);
  const [dataMode, setDataMode] = useState<'HYBRID' | 'MOCK'>('HYBRID');
  const [isCalculating, setIsCalculating] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [events, setEvents] = useState<FeedEvent[]>([
    createEvent('info', 'System Online', 'NavOptima time-dependent A* engine ready. Select ports to compute routes.'),
  ]);

  const addEvent = useCallback((event: FeedEvent) => {
    setEvents((prev) => [event, ...prev].slice(0, 50));
  }, []);

  const computeRoute = useCallback(
    async (origin: string, destination: string, ship: string, optimization: OptimizationMode, overrideMode?: 'HYBRID' | 'MOCK') => {
      const mode = overrideMode || dataMode;
      setIsCalculating(true);
      addEvent(createEvent('info', 'Calculating Route', `Computing ${optimization} route: ${origin} → ${destination} (${mode} mode)`));

      try {
        setSimulationResult(null);
        setActiveSimulation(null);
        setPreviousRoute(null);

        // 1. Calculate optimal route
        const route = await calculateRoute({ origin, destination, ship, optimization, data_mode: mode });

        if (!route.routing_supported) {
          setCurrentRoute(route);
          setActiveVoyage(null);
          addEvent(createEvent('warning', 'Unsupported Port', route.reason, 'high'));
          return;
        }

        setCurrentRoute(route);

        // 2. Automatically create stateful voyage for simulation binding
        try {
          const voyageState = await initVoyage({
            origin,
            destination,
            ship,
            optimization,
            data_mode: mode,
          });
          setActiveVoyage(voyageState);
        } catch {
          // Voyage state creation fallback
        }

        addEvent(
          createEvent(
            'route_calculated',
            'Route Calculated',
            `${route.distance_km} km | ETA ${route.eta_hours}h | Fuel ${route.fuel_mt} MT | Safety ${route.safety_score}%`
          )
        );
      } catch (err: any) {
        addEvent(createEvent('error', 'Route Error', `Failed to calculate route: ${err.message || err}`, 'high'));
      } finally {
        setIsCalculating(false);
      }
    },
    [addEvent, dataMode]
  );

  const startVoyageSimulation = useCallback(
    async (origin: string, destination: string, ship: string, optimization: OptimizationMode) => {
      setIsCalculating(true);
      addEvent(createEvent('info', 'Initializing Voyage', `Starting stateful voyage from ${origin} to ${destination} (${dataMode} mode)`));

      try {
        const voyageState = await initVoyage({
          origin,
          destination,
          ship,
          optimization,
          data_mode: dataMode,
        });

        setActiveVoyage(voyageState);
        setCurrentRoute(voyageState.active_route);
        addEvent(
          createEvent(
            'info',
            'Voyage Initialized',
            `Voyage ID: ${voyageState.voyage_id.substring(0, 8)}... | Position: (${voyageState.current_lat.toFixed(2)}°, ${voyageState.current_lon.toFixed(2)}°)`
          )
        );
      } catch (err: any) {
        addEvent(createEvent('error', 'Voyage Init Error', `Failed to initialize voyage: ${err.message || err}`, 'high'));
      } finally {
        setIsCalculating(false);
      }
    },
    [addEvent, dataMode]
  );

  const advanceVoyageTick = useCallback(
    async (tickHours: number = 1.0) => {
      if (!activeVoyage) return;
      setIsSimulating(true);

      try {
        const tickRes = await apiTickVoyage(activeVoyage.voyage_id, tickHours);
        
        setActiveVoyage((prev) => prev ? {
          ...prev,
          current_time: tickRes.current_time,
          current_lat: tickRes.current_lat,
          current_lon: tickRes.current_lon,
          current_node_id: tickRes.current_node_id,
          is_completed: tickRes.is_completed,
          active_route: tickRes.active_route,
        } : null);

        setCurrentRoute(tickRes.active_route);

        if (tickRes.rerouted_in_tick) {
          addEvent(
            createEvent(
              'reroute',
              'Dynamic Reroute Triggered',
              `Weather deterioration exceeded hysteresis threshold. Route updated. New cost: ${tickRes.new_route_cost?.toFixed(2)}`,
              'high'
            )
          );
        } else {
          addEvent(
            createEvent(
              'info',
              'Simulation Advanced',
              `t = ${tickRes.current_time.toFixed(1)}h | Ship at (${tickRes.current_lat.toFixed(2)}°, ${tickRes.current_lon.toFixed(2)}°)`
            )
          );
        }
      } catch (err: any) {
        addEvent(createEvent('error', 'Tick Error', `Failed to advance voyage: ${err.message || err}`, 'high'));
      } finally {
        setIsSimulating(false);
      }
    },
    [activeVoyage, addEvent]
  );

  const triggerSimulation = useCallback(
    async (event: SimulationEvent) => {
      setIsSimulating(true);
      setActiveSimulation(event);
      addEvent(
        createEvent(
          'simulation_event',
          `${event.type.replace('_', ' ').toUpperCase()} Disruption`,
          event.label || `${event.type} at ${event.lat}°, ${event.lon}°`,
          event.severity > 0.7 ? 'critical' : 'high'
        )
      );

      try {
        const result = await simulateEvent(event, activeVoyage?.voyage_id);
        setSimulationResult(result);

        if (currentRoute) {
          setPreviousRoute(currentRoute);
        }

        // Authoritative backend route replacement without frontend metric arithmetic
        if (result.active_route) {
          setCurrentRoute(result.active_route);
        } else if (result.new_route.length > 0) {
          setCurrentRoute((prev) => prev ? {
            ...prev,
            coordinates: result.new_route,
            reason: result.reason,
          } : null);
        }

        const eventTitle = result.decision === 'REROUTE' ? '🚢 ROUTE REROUTED'
          : result.decision === 'PORT_CONGESTION_UPDATED' ? '⚓ PORT CONGESTION UPDATED'
          : result.decision === 'SPATIALLY_IRRELEVANT' ? '🌤️ SPATIALLY IRRELEVANT'
          : result.decision === 'EVENT_BEHIND_VESSEL' ? '⏳ EVENT BEHIND VESSEL'
          : result.decision === 'ROUTE_RETAINED' ? '🛡️ ROUTE RETAINED'
          : '⚡ DISRUPTION EVALUATED';

        addEvent(createEvent('reroute', eventTitle, result.reason, 'high', result));
      } catch (err: any) {
        addEvent(createEvent('error', 'Simulation Error', `Failed to simulate: ${err.message || err}`, 'high'));
      } finally {
        setIsSimulating(false);
      }
    },
    [activeVoyage, addEvent, currentRoute]
  );

  const clearSimulation = useCallback(() => {
    setSimulationResult(null);
    setActiveSimulation(null);
    setPreviousRoute(null);
    addEvent(createEvent('info', 'Simulation Overlay Cleared', 'Active simulation overlay cleared. Authoritative voyage route maintained.'));
  }, [addEvent]);

  const clearEvents = useCallback(() => {
    setEvents([
      createEvent('info', 'System Online', 'NavOptima time-dependent A* engine ready. Timeline log reset.'),
    ]);
  }, []);

  const clearRoute = useCallback(() => {
    setCurrentRoute(null);
    setPreviousRoute(null);
    setSimulationResult(null);
    setActiveSimulation(null);
    setActiveVoyage(null);
  }, []);

  return {
    currentRoute,
    previousRoute,
    simulationResult,
    activeSimulation,
    activeVoyage,
    dataMode,
    isCalculating,
    isSimulating,
    events,
    setDataMode,
    computeRoute,
    triggerSimulation,
    startVoyageSimulation,
    advanceVoyageTick,
    clearSimulation,
    clearRoute,
    clearEvents,
    setActiveVoyage,
    setCurrentRoute,
  };
}

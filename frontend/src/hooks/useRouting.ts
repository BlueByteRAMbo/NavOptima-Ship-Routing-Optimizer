/**
 * useRouting — Route calculation and simulation state management
 */

import { useState, useCallback } from 'react';
import type {
  RouteResponse,
  SimulationEvent,
  SimulationResponse,
  OptimizationMode,
  FeedEvent,
} from '../types/maritime';
import { calculateRoute, simulateEvent } from '../services/api';

interface UseRoutingReturn {
  // State
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
  simulationResult: SimulationResponse | null;
  activeSimulation: SimulationEvent | null;
  isCalculating: boolean;
  isSimulating: boolean;
  events: FeedEvent[];

  // Actions
  computeRoute: (origin: string, destination: string, ship: string, optimization: OptimizationMode) => Promise<void>;
  triggerSimulation: (event: SimulationEvent) => Promise<void>;
  clearSimulation: () => void;
  clearRoute: () => void;
}

let eventCounter = 0;

function createEvent(
  type: FeedEvent['type'],
  title: string,
  description: string,
  severity?: FeedEvent['severity']
): FeedEvent {
  return {
    id: `evt-${++eventCounter}`,
    timestamp: new Date(),
    type,
    title,
    description,
    severity,
  };
}

export function useRouting(): UseRoutingReturn {
  const [currentRoute, setCurrentRoute] = useState<RouteResponse | null>(null);
  const [previousRoute, setPreviousRoute] = useState<RouteResponse | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [activeSimulation, setActiveSimulation] = useState<SimulationEvent | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [events, setEvents] = useState<FeedEvent[]>([
    createEvent('info', 'System Online', 'NavOptima routing engine initialized. Select origin and destination ports to begin.'),
  ]);

  const addEvent = useCallback((event: FeedEvent) => {
    setEvents((prev) => [event, ...prev].slice(0, 50));
  }, []);

  const computeRoute = useCallback(
    async (origin: string, destination: string, ship: string, optimization: OptimizationMode) => {
      setIsCalculating(true);
      addEvent(createEvent('info', 'Calculating Route', `Computing ${optimization} route: ${origin} → ${destination} (${ship})`));

      try {
        // Clear previous simulation when computing a new route
        setSimulationResult(null);
        setActiveSimulation(null);
        setPreviousRoute(null);

        const route = await calculateRoute({ origin, destination, ship, optimization });
        setCurrentRoute(route);
        addEvent(
          createEvent(
            'route_calculated',
            'Route Calculated',
            `${route.distance_km} km | ETA ${route.eta_hours}h | Fuel ${route.fuel_mt} MT | Safety ${route.safety_score}%`
          )
        );
      } catch (err) {
        addEvent(createEvent('error', 'Route Error', `Failed to calculate route: ${err}`, 'high'));
      } finally {
        setIsCalculating(false);
      }
    },
    [addEvent]
  );

  const triggerSimulation = useCallback(
    async (event: SimulationEvent) => {
      setIsSimulating(true);
      setActiveSimulation(event);
      addEvent(
        createEvent(
          'simulation_event',
          `${event.type.replace('_', ' ').toUpperCase()} Event`,
          event.label || `${event.type} at ${event.lat}°, ${event.lon}° (severity: ${(event.severity * 100).toFixed(0)}%)`,
          event.severity > 0.7 ? 'critical' : event.severity > 0.4 ? 'high' : 'medium'
        )
      );

      try {
        const result = await simulateEvent(event);
        setSimulationResult(result);

        // Store old route as previous, set new route as current
        if (currentRoute) {
          setPreviousRoute(currentRoute);
        }
        setCurrentRoute({
          coordinates: result.new_route,
          distance_km: (currentRoute?.distance_km || 0) + (result.fuel_change_mt > 0 ? 80 : -40),
          eta_hours: (currentRoute?.eta_hours || 0) + result.eta_change_hours,
          fuel_mt: (currentRoute?.fuel_mt || 0) + result.fuel_change_mt,
          safety_score: (currentRoute?.safety_score || 80) + result.safety_change,
          reason: result.reason,
        });

        addEvent(
          createEvent(
            'reroute',
            'Route Recalculated',
            result.reason,
            'high'
          )
        );
      } catch (err) {
        addEvent(createEvent('error', 'Simulation Error', `Failed to simulate: ${err}`, 'high'));
      } finally {
        setIsSimulating(false);
      }
    },
    [addEvent, currentRoute]
  );

  const clearSimulation = useCallback(() => {
    if (previousRoute) {
      setCurrentRoute(previousRoute);
      setPreviousRoute(null);
    }
    setSimulationResult(null);
    setActiveSimulation(null);
    addEvent(createEvent('info', 'Simulation Cleared', 'Simulation event cleared. Route restored to original path.'));
  }, [previousRoute, addEvent]);

  const clearRoute = useCallback(() => {
    setCurrentRoute(null);
    setPreviousRoute(null);
    setSimulationResult(null);
    setActiveSimulation(null);
  }, []);

  return {
    currentRoute,
    previousRoute,
    simulationResult,
    activeSimulation,
    isCalculating,
    isSimulating,
    events,
    computeRoute,
    triggerSimulation,
    clearSimulation,
    clearRoute,
  };
}

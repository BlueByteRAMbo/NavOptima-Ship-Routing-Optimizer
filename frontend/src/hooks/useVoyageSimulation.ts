import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { simulateEvent, tickVoyage, initVoyage } from '../services/api';
import type {
  SimulationEvent,
  SimulationResponse,
  RouteResponse,
} from '../types/maritime';

export interface VoyageLogEntry {
  id: string;
  timeHours: number;
  timestamp: string;
  title: string;
  description: string;
  type: 'info' | 'disruption' | 'decision' | 'override' | 'completed';
  result?: SimulationResponse;
}

export function useVoyageSimulation() {
  const {
    currentRoute,
    activeVoyage,
    setActiveVoyage,
    setCurrentRoute,
    dataMode,
  } = useApp();

  const [isPlaying, setIsPlaying] = useState(false);
  // speedMultiplier can be a number (1, 2, 5, 10, 25, 50) or 'AUTO' (~90s demo target)
  const [speedMultiplier, setSpeedMultiplier] = useState<number | 'AUTO'>('AUTO');
  const [alternativeRoute, setAlternativeRoute] = useState<RouteResponse | null>(null);
  const [viewingAlternative, setViewingAlternative] = useState(false);
  const [activeDisruption, setActiveDisruption] = useState<SimulationResponse | null>(null);
  const [eventLog, setEventLog] = useState<VoyageLogEntry[]>([]);
  const [isProcessingDisruption, setIsProcessingDisruption] = useState(false);

  const timerRef = useRef<number | null>(null);

  // Initialize event log on voyage load
  useEffect(() => {
    if (activeVoyage) {
      setEventLog([
        {
          id: 'init-1',
          timeHours: activeVoyage.current_time || 0.0,
          timestamp: new Date().toLocaleTimeString(),
          title: '🚢 Voyage Initialized',
          description: `Stateful voyage initialized for ${activeVoyage.origin.toUpperCase()} → ${activeVoyage.destination.toUpperCase()} using ${activeVoyage.strategy} strategy (${activeVoyage.data_mode} mode). Position: (${activeVoyage.current_lat.toFixed(2)}°, ${activeVoyage.current_lon.toFixed(2)}°).`,
          type: 'info',
        },
      ]);
    }
  }, [activeVoyage?.voyage_id]);

  // Handle Play/Pause timer loop with precise ~90 real-second playback duration
  useEffect(() => {
    if (!isPlaying || !activeVoyage || activeVoyage.is_completed) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const totalEtaHours = currentRoute?.eta_hours || activeVoyage.active_route?.eta_hours || 180.0;
    
    // Calculate tickDurationHours & intervalMs based on playback speed mode
    let intervalMs = 150;
    let tickDurationHours = 1.0;

    if (speedMultiplier === 'AUTO') {
      // Target exactly ~90 real-world seconds for 0% -> 100% voyage completion
      // 90 seconds @ 150ms interval = 600 total ticks
      intervalMs = 150;
      tickDurationHours = Math.max(0.1, totalEtaHours / 600.0);
    } else {
      const mult = typeof speedMultiplier === 'number' ? speedMultiplier : 10;
      if (mult <= 2) {
        intervalMs = 300;
        tickDurationHours = mult * 0.3;
      } else if (mult <= 5) {
        intervalMs = 200;
        tickDurationHours = mult * 0.2;
      } else if (mult <= 10) {
        intervalMs = 150;
        tickDurationHours = mult * 0.15;
      } else if (mult <= 25) {
        intervalMs = 100;
        tickDurationHours = mult * 0.1;
      } else {
        intervalMs = 80;
        tickDurationHours = mult * 0.08;
      }
    }

    timerRef.current = window.setInterval(async () => {
      try {
        const tickRes = await tickVoyage(activeVoyage.voyage_id, tickDurationHours);
        
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

        if (tickRes.is_completed) {
          const destCoords = tickRes.active_route?.coordinates?.[tickRes.active_route.coordinates.length - 1];
          const distToDestKm = destCoords
            ? Math.hypot(tickRes.current_lat - destCoords[0], tickRes.current_lon - destCoords[1]) * 111.0
            : 0;

          if (distToDestKm <= 60.0) {
            setIsPlaying(false);
            setEventLog((prev) => [
              {
                id: `log-${Date.now()}`,
                timeHours: tickRes.current_time,
                timestamp: new Date().toLocaleTimeString(),
                title: '🏁 Destination Reached',
                description: `Vessel safely arrived at destination (${tickRes.current_lat.toFixed(2)}°, ${tickRes.current_lon.toFixed(2)}°). Total voyage time: ${tickRes.current_time.toFixed(1)}h.`,
                type: 'completed',
              },
              ...prev,
            ]);
          }
        }
      } catch (err) {
        setIsPlaying(false);
      }
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, activeVoyage?.voyage_id, speedMultiplier, currentRoute?.eta_hours, setActiveVoyage, setCurrentRoute]);

  // Restart Voyage to start position
  const restartVoyage = useCallback(async () => {
    if (!activeVoyage) return;
    setIsPlaying(false);
    try {
      const newState = await initVoyage({
        origin: activeVoyage.origin,
        destination: activeVoyage.destination,
        ship: activeVoyage.ship,
        optimization: activeVoyage.strategy as any,
        data_mode: dataMode,
      });
      setActiveVoyage(newState);
      setCurrentRoute(newState.active_route);
      setAlternativeRoute(null);
      setViewingAlternative(false);
      setActiveDisruption(null);
      setEventLog([
        {
          id: `log-${Date.now()}`,
          timeHours: 0.0,
          timestamp: new Date().toLocaleTimeString(),
          title: '🔄 Voyage Restarted',
          description: `Voyage reset to origin (${newState.origin.toUpperCase()}). Simulation clock set to t=0.0h.`,
          type: 'info',
        },
      ]);
    } catch (err) {
      console.error('Failed to restart voyage:', err);
    }
  }, [activeVoyage, dataMode, setActiveVoyage, setCurrentRoute]);

  // Trigger Disruption Ahead & Auto-Pause for Decision
  const triggerDisruptionAhead = useCallback(async (type: 'storm' | 'port_congestion' | 'security') => {
    if (!activeVoyage) return;
    setIsProcessingDisruption(true);

    const routeCoords = activeVoyage.active_route.coordinates;
    const currentLat = activeVoyage.current_lat;
    const currentLon = activeVoyage.current_lon;

    let minIdx = 0;
    let minSqDist = Infinity;
    for (let i = 0; i < routeCoords.length; i++) {
      const [lat, lon] = routeCoords[i];
      const sq = (lat - currentLat) ** 2 + (lon - currentLon) ** 2;
      if (sq < minSqDist) {
        minSqDist = sq;
        minIdx = i;
      }
    }

    const targetIdx = Math.min(routeCoords.length - 1, minIdx + Math.max(1, Math.floor((routeCoords.length - minIdx) * 0.4)));
    const [disruptionLat, disruptionLon] = routeCoords[targetIdx];

    const labelMap = {
      storm: 'Severe Tropical Storm Ahead',
      port_congestion: 'Port Congestion Event Ahead',
      security: 'Maritime Security Threat Ahead',
    };

    const eventPayload: SimulationEvent = {
      voyage_id: activeVoyage.voyage_id,
      type,
      lat: disruptionLat,
      lon: disruptionLon,
      radius_km: type === 'port_congestion' ? 50 : 250,
      severity: 0.85,
      label: labelMap[type],
    };

    try {
      const result = await simulateEvent(eventPayload, activeVoyage.voyage_id);
      setActiveDisruption(result);

      // Auto-pause playback to allow user decision on map overlay
      setIsPlaying(false);

      if (result.active_route) {
        setCurrentRoute(result.active_route);
        setActiveVoyage((prev) => prev ? { ...prev, active_route: result.active_route! } : null);
      }

      if (result.new_route && result.new_route.length > 0 && result.decision !== 'REROUTE') {
        setAlternativeRoute({
          coordinates: result.new_route,
          distance_km: result.active_route?.distance_km || 0,
          eta_hours: (result.eta_after || 0) - (result.eta_change_hours || 0),
          fuel_mt: (result.fuel_after || 0) - (result.fuel_change_mt || 0),
          safety_score: Math.max(1.0, (result.safety_after || 0) - 1.2),
          reason: 'Evaluated alternative route (faster but lower safety score)',
        });
      } else {
        setAlternativeRoute(null);
      }

      setEventLog((prev) => [
        {
          id: `log-${Date.now()}`,
          timeHours: activeVoyage.current_time,
          timestamp: new Date().toLocaleTimeString(),
          title: `⚠️ DISRUPTION DETECTED — SIMULATION PAUSED`,
          description: `${labelMap[type].toUpperCase()} detected. Voyage paused for decision. Reason: ${result.reason}`,
          type: 'disruption',
          result,
        },
        ...prev,
      ]);
    } catch (err: any) {
      console.error('Disruption simulation error:', err);
    } finally {
      setIsProcessingDisruption(false);
    }
  }, [activeVoyage, setCurrentRoute, setActiveVoyage]);

  // Manual Override: Accept Alternative Route & Auto-Resume
  const acceptAlternativeRoute = useCallback(() => {
    if (!alternativeRoute || !activeVoyage) return;

    setCurrentRoute(alternativeRoute);
    setActiveVoyage((prev) => prev ? { ...prev, active_route: alternativeRoute } : null);
    setViewingAlternative(false);
    setAlternativeRoute(null);
    setActiveDisruption(null);

    setEventLog((prev) => [
      {
        id: `log-${Date.now()}`,
        timeHours: activeVoyage.current_time,
        timestamp: new Date().toLocaleTimeString(),
        title: '🔀 MANUAL OVERRIDE ACCEPTED',
        description: `Alternative route selected by user. Active route updated. Voyage continuing from current position (${activeVoyage.current_lat.toFixed(2)}°, ${activeVoyage.current_lon.toFixed(2)}°).`,
        type: 'override',
      },
      ...prev,
    ]);

    // Automatically resume voyage playback
    setIsPlaying(true);
  }, [alternativeRoute, activeVoyage, setCurrentRoute, setActiveVoyage]);

  // Keep Current Route & Auto-Resume
  const keepCurrentRoute = useCallback(() => {
    if (!activeVoyage) return;

    setViewingAlternative(false);
    setAlternativeRoute(null);
    setActiveDisruption(null);

    setEventLog((prev) => [
      {
        id: `log-${Date.now()}`,
        timeHours: activeVoyage.current_time,
        timestamp: new Date().toLocaleTimeString(),
        title: '🛡️ CURRENT ROUTE RETAINED',
        description: `User selected to keep current route geometry. Voyage continuing towards destination.`,
        type: 'info',
      },
      ...prev,
    ]);

    // Automatically resume voyage playback
    setIsPlaying(true);
  }, [activeVoyage]);

  // Progress metrics calculation
  const progressMetrics = useMemo(() => {
    if (!currentRoute || !activeVoyage) {
      return { progressPercent: 0, distanceTraveledKm: 0, distanceRemainingKm: 0 };
    }

    const totalDist = currentRoute.distance_km || 1000;
    const totalEta = currentRoute.eta_hours || 100;
    const timeRatio = Math.min(1.0, activeVoyage.current_time / totalEta);
    const progressPercent = Math.min(100, Math.round(timeRatio * 100));
    const distanceTraveledKm = Math.round(totalDist * timeRatio);
    const distanceRemainingKm = Math.max(0, Math.round(totalDist - distanceTraveledKm));

    return { progressPercent, distanceTraveledKm, distanceRemainingKm };
  }, [currentRoute, activeVoyage]);

  return {
    isPlaying,
    setIsPlaying,
    speedMultiplier,
    setSpeedMultiplier,
    effectiveSpeed: speedMultiplier === 'AUTO' ? 10 : speedMultiplier,
    alternativeRoute,
    viewingAlternative,
    setViewingAlternative,
    activeDisruption,
    eventLog,
    isProcessingDisruption,
    restartVoyage,
    triggerDisruptionAhead,
    acceptAlternativeRoute,
    keepCurrentRoute,
    progressMetrics,
  };
}

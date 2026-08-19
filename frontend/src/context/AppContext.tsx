import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouting } from '../hooks/useRouting';
import { getPorts, getEnvironment, getDataSources, getSecurity } from '../services/api';
import type {
  Port,
  EnvironmentCell,
  DataSource,
  RouteResponse,
  SimulationEvent,
  SimulationResponse,
  VoyageStateResponse,
  OptimizationMode,
  FeedEvent,
} from '../types/maritime';

interface AppContextType {
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
  ports: Port[];
  environment: EnvironmentCell[];
  dataSources: DataSource[];
  riskZones: SimulationEvent[];
  loadError: string | null;
  showWeatherLayer: boolean;
  showRiskLayer: boolean;
  showOceanCurrents: boolean;

  // Setters & Actions
  setDataMode: (mode: 'HYBRID' | 'MOCK') => void;
  computeRoute: (origin: string, destination: string, ship: string, optimization: OptimizationMode, overrideMode?: 'HYBRID' | 'MOCK') => Promise<void>;
  triggerSimulation: (event: SimulationEvent) => Promise<void>;
  startVoyageSimulation: (origin: string, destination: string, ship: string, optimization: OptimizationMode) => Promise<void>;
  advanceVoyageTick: (tickHours?: number) => Promise<void>;
  clearSimulation: () => void;
  clearRoute: () => void;
  clearEvents: () => void;
  setShowWeatherLayer: (val: boolean) => void;
  setShowRiskLayer: (val: boolean) => void;
  setShowOceanCurrents: (val: boolean) => void;
  setActiveVoyage: React.Dispatch<React.SetStateAction<VoyageStateResponse | null>>;
  setCurrentRoute: React.Dispatch<React.SetStateAction<RouteResponse | null>>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [showWeatherLayer, setShowWeatherLayer] = useState(false);
  const [showRiskLayer, setShowRiskLayer] = useState(false);
  const [showOceanCurrents, setShowOceanCurrents] = useState(true);

  const [ports, setPorts] = useState<Port[]>([]);
  const [environment, setEnvironment] = useState<EnvironmentCell[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [riskZones, setRiskZones] = useState<SimulationEvent[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const routing = useRouting();

  useEffect(() => {
    let isMounted = true;
    async function loadBackendData() {
      try {
        const [fetchedPorts, fetchedSources] = await Promise.all([
          getPorts(),
          getDataSources(),
        ]);
        if (isMounted) {
          setPorts(fetchedPorts);
          setDataSources(fetchedSources);
        }
      } catch (err: any) {
        if (isMounted) {
          setLoadError(err.message || 'Failed to connect to NavOptima backend API.');
        }
      }
    }
    loadBackendData();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    if ((showWeatherLayer || showOceanCurrents) && environment.length === 0) {
      getEnvironment()
        .then((fetchedEnv) => {
          if (isMounted) setEnvironment(fetchedEnv);
        })
        .catch(() => {});
    }
    return () => {
      isMounted = false;
    };
  }, [showWeatherLayer, showOceanCurrents, environment.length]);

  useEffect(() => {
    let isMounted = true;
    if (showRiskLayer && riskZones.length === 0) {
      getSecurity()
        .then((sec) => {
          if (isMounted && sec?.zones) {
            const mappedZones: SimulationEvent[] = sec.zones.map((z) => ({
              type: 'security',
              lat: z.center_lat,
              lon: z.center_lon,
              radius_km: z.radius_km,
              severity: z.risk_level * 10,
              label: z.name,
            }));
            setRiskZones(mappedZones);
          }
        })
        .catch(() => {});
    }
    return () => {
      isMounted = false;
    };
  }, [showRiskLayer, riskZones.length]);

  return (
    <AppContext.Provider
      value={{
        ...routing,
        ports,
        environment,
        dataSources,
        riskZones,
        loadError,
        showWeatherLayer,
        showRiskLayer,
        showOceanCurrents,
        setShowWeatherLayer,
        setShowRiskLayer,
        setShowOceanCurrents,
        setActiveVoyage: routing.setActiveVoyage,
        setCurrentRoute: routing.setCurrentRoute,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

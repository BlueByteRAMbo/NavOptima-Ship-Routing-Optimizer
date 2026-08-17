import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { ControlPanel } from './components/optimization/ControlPanel';
import MaritimeMap from './components/map/MaritimeMap';
import AnalyticsPanel from './components/analytics/AnalyticsPanel';
import { EventFeed } from './components/simulation/EventFeed';
import { useRouting } from './hooks/useRouting';

import type { Port, EnvironmentCell, DataSource } from './types/maritime';
import { getPorts, getEnvironment, getDataSources, healthCheck } from './services/api';
import { DEMO_PORTS, DEMO_ENVIRONMENT, DEMO_DATA_SOURCES, DEMO_RISK_ZONES } from './data/demo';

const App: React.FC = () => {
  const [showWeatherLayer, setShowWeatherLayer] = useState(true);
  const [showRiskLayer, setShowRiskLayer] = useState(true);

  // Live state with demo defaults
  const [ports, setPorts] = useState<Port[]>(DEMO_PORTS);
  const [environment, setEnvironment] = useState<EnvironmentCell[]>(DEMO_ENVIRONMENT);
  const [dataSources, setDataSources] = useState<DataSource[]>(DEMO_DATA_SOURCES);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  const {
    currentRoute,
    previousRoute,
    isCalculating,
    activeSimulation,
    isSimulating,
    simulationResult,
    events,
    computeRoute,
    triggerSimulation,
    clearSimulation
  } = useRouting();

  // Load live data from FastAPI backend
  useEffect(() => {
    let isMounted = true;

    async function checkAndFetch() {
      try {
        const isOnline = await healthCheck();
        if (!isMounted) return;
        setIsBackendConnected(isOnline);

        if (isOnline) {
          const [livePorts, liveEnv, liveSources] = await Promise.all([
            getPorts(),
            getEnvironment(1500),
            getDataSources(),
          ]);
          if (!isMounted) return;
          if (livePorts && livePorts.length > 0) setPorts(livePorts);
          if (liveEnv && liveEnv.length > 0) setEnvironment(liveEnv);
          if (liveSources && liveSources.length > 0) setDataSources(liveSources);
        }
      } catch (err) {
        console.warn('Backend unavailable, operating in demo mode:', err);
      }
    }

    checkAndFetch();
    const interval = setInterval(async () => {
      const isOnline = await healthCheck();
      if (isMounted) setIsBackendConnected(isOnline);
    }, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#06131F] text-slate-200 font-sans">
      <Header
        showWeatherLayer={showWeatherLayer}
        showRiskLayer={showRiskLayer}
        onToggleWeather={() => setShowWeatherLayer(!showWeatherLayer)}
        onToggleRisk={() => setShowRiskLayer(!showRiskLayer)}
        isBackendConnected={isBackendConnected}
      />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Panel - Control */}
        <div className="w-80 flex-shrink-0 z-10 border-r border-[#1D3A4C] bg-[#06131F]/90 backdrop-blur-md overflow-y-auto">
          <ControlPanel
            ports={ports}
            onCalculateRoute={computeRoute}
            isCalculating={isCalculating}
            currentRoute={currentRoute}
            onTriggerSimulation={triggerSimulation}
            isSimulating={isSimulating}
            activeSimulation={activeSimulation}
            onClearSimulation={clearSimulation}
          />
        </div>

        {/* Center - Map */}
        <div className="flex-1 relative z-0 h-full w-full">
          <MaritimeMap
            currentRoute={currentRoute}
            previousRoute={previousRoute}
            ports={ports}
            environment={environment}
            activeSimulation={activeSimulation}
            riskZones={DEMO_RISK_ZONES}
            showWeatherLayer={showWeatherLayer}
            showRiskLayer={showRiskLayer}
          />
        </div>

        {/* Right Panel - Analytics */}
        <div className="w-96 flex-shrink-0 z-10 border-l border-[#1D3A4C] bg-[#06131F]/90 backdrop-blur-md overflow-y-auto">
          <AnalyticsPanel
            currentRoute={currentRoute}
            previousRoute={previousRoute}
            simulationResult={simulationResult}
            ports={ports}
            environment={environment}
            dataSources={dataSources}
          />
        </div>
      </div>

      {/* Bottom - Event Feed */}
      <div className="h-32 flex-shrink-0 z-20 border-t border-[#1D3A4C] bg-[#0A1B29]">
        <EventFeed events={events} />
      </div>
    </div>
  );
};

export default App;

import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { ControlPanel } from './components/optimization/ControlPanel';
import MaritimeMap from './components/map/MaritimeMap';
import AnalyticsPanel from './components/analytics/AnalyticsPanel';
import { EventFeed } from './components/simulation/EventFeed';
import { useRouting } from './hooks/useRouting';

import { DEMO_PORTS, DEMO_ENVIRONMENT, DEMO_DATA_SOURCES, DEMO_RISK_ZONES } from './data/demo';

const App: React.FC = () => {
  const [showWeatherLayer, setShowWeatherLayer] = useState(true);
  const [showRiskLayer, setShowRiskLayer] = useState(true);

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

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#06131F] text-slate-200 font-sans">
      <Header
        showWeatherLayer={showWeatherLayer}
        showRiskLayer={showRiskLayer}
        onToggleWeather={() => setShowWeatherLayer(!showWeatherLayer)}
        onToggleRisk={() => setShowRiskLayer(!showRiskLayer)}
      />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Panel - Control */}
        <div className="w-80 flex-shrink-0 z-10 border-r border-[#1D3A4C] bg-[#06131F]/90 backdrop-blur-md overflow-y-auto">
          <ControlPanel
            ports={DEMO_PORTS}
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
            ports={DEMO_PORTS}
            environment={DEMO_ENVIRONMENT}
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
            ports={DEMO_PORTS}
            environment={DEMO_ENVIRONMENT}
            dataSources={DEMO_DATA_SOURCES}
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

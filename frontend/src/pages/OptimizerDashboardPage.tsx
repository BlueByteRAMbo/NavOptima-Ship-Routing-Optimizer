import React from 'react';
import { ControlPanel } from '../components/optimization/ControlPanel';
import MaritimeMap from '../components/map/MaritimeMap';
import AnalyticsPanel from '../components/analytics/AnalyticsPanel';
import { EventFeed } from '../components/simulation/EventFeed';
import { useApp } from '../context/AppContext';

export const OptimizerDashboardPage: React.FC = () => {
  const {
    ports,
    environment,
    dataSources,
    riskZones,
    loadError,
    showWeatherLayer,
    showRiskLayer,
    showOceanCurrents,
    currentRoute,
    previousRoute,
    activeVoyage,
    simulationResult,
    activeSimulation,
    dataMode,
    isCalculating,
    isSimulating,
    events,
    setDataMode,
    computeRoute,
    triggerSimulation,
    clearSimulation,
    clearEvents,
  } = useApp();

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {loadError && (
        <div className="bg-red-900/80 border-b border-red-500 text-red-100 text-xs px-4 py-2 flex items-center justify-between z-50">
          <span>⚠️ {loadError} Ensure backend FastAPI server is running on http://localhost:8000.</span>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Panel - Control */}
        <div className="w-80 flex-shrink-0 z-10 border-r border-[#1D3A4C] bg-[#06131F]/90 backdrop-blur-md overflow-y-auto">
          <ControlPanel
            ports={ports}
            onCalculateRoute={computeRoute}
            isCalculating={isCalculating}
            currentRoute={currentRoute}
            dataMode={dataMode}
            onDataModeChange={setDataMode}
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
            activeVoyage={activeVoyage}
            ports={ports}
            environment={environment}
            activeSimulation={activeSimulation}
            riskZones={riskZones}
            showWeatherLayer={showWeatherLayer}
            showRiskLayer={showRiskLayer}
            showOceanCurrents={showOceanCurrents}
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

      {/* Bottom - Simulation Timeline / Event Feed */}
      <div className="h-[160px] flex-shrink-0 z-20 border-t border-[#1D3A4C] bg-[#06131F]">
        <EventFeed events={events} onClearEvents={clearEvents} />
      </div>
    </div>
  );
};

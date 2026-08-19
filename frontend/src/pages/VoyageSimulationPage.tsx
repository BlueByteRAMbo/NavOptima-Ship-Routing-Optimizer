import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Compass, PlayCircle, Navigation } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useVoyageSimulation } from '../hooks/useVoyageSimulation';
import MaritimeMap from '../components/map/MaritimeMap';
import { VoyageControls } from '../components/simulation/VoyageControls';
import { DecisionPanel } from '../components/simulation/DecisionPanel';
import { SimulationEventLog } from '../components/simulation/SimulationEventLog';

export const VoyageSimulationPage: React.FC = () => {
  const {
    currentRoute,
    previousRoute,
    activeVoyage,
    ports,
    environment,
    riskZones,
    activeSimulation,
    showWeatherLayer,
    showRiskLayer,
    showOceanCurrents,
  } = useApp();

  const {
    isPlaying,
    setIsPlaying,
    speedMultiplier,
    setSpeedMultiplier,
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
  } = useVoyageSimulation();

  const [focusCoords, setFocusCoords] = useState<[number, number] | null>(null);

  const handleFocusMap = (lat: number, lon: number) => {
    setFocusCoords([lat, lon]);
  };

  const handleResetView = () => {
    setFocusCoords(null);
  };

  // Empty State: If no route or voyage has been calculated
  if (!currentRoute && !activeVoyage) {
    return (
      <div className="flex flex-col items-center justify-center h-full w-full bg-[#06131F] text-slate-200 p-6 space-y-4">
        <div className="bg-[#0A1B29] border border-[#1D3A4C] p-8 rounded-2xl max-w-md text-center space-y-4 shadow-2xl">
          <div className="w-16 h-16 bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 rounded-full flex items-center justify-center mx-auto">
            <PlayCircle className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-white">No Active Voyage Loaded</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calculate an optimal route on the Route Optimizer dashboard first to start the digital voyage simulation.
            </p>
          </div>

          <Link
            to="/"
            className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition-colors shadow-lg shadow-cyan-950/40 inline-flex"
          >
            <Compass className="w-4 h-4" />
            <span>Go to Route Optimizer</span>
          </Link>
        </div>
      </div>
    );
  }

  // Generic origin & destination names
  const originName = (activeVoyage?.origin || 'ACTIVE VOYAGE').toUpperCase();
  const destName = (activeVoyage?.destination || 'DESTINATION').toUpperCase();
  const strategyName = (activeVoyage?.strategy || 'BALANCED').toUpperCase();
  const modeName = activeVoyage?.data_mode || 'HYBRID';

  const mapCurrentRoute = currentRoute;
  const mapPreviousRoute = viewingAlternative ? alternativeRoute : previousRoute;

  return (
    <div className="flex flex-1 overflow-hidden relative w-full h-full bg-[#06131F]">
      {/* Center - Interactive Simulation Map */}
      <div className="flex-1 relative z-0 h-full w-full">
        <MaritimeMap
          currentRoute={mapCurrentRoute}
          previousRoute={mapPreviousRoute}
          activeVoyage={activeVoyage}
          ports={ports}
          environment={environment}
          activeSimulation={activeSimulation}
          riskZones={riskZones}
          showWeatherLayer={showWeatherLayer}
          showRiskLayer={showRiskLayer}
          showOceanCurrents={showOceanCurrents}
          focusCoords={focusCoords}
          activeDisruption={activeDisruption}
          alternativeRoute={alternativeRoute}
          onAcceptAlternative={acceptAlternativeRoute}
          onKeepCurrent={keepCurrentRoute}
          onFocusMap={handleFocusMap}
          onResetView={handleResetView}
        />

        {/* Floating Bottom-Right Banner: Origin → Destination (below overlay, above legend) */}
        <div className="absolute bottom-4 right-4 z-[400] bg-[#0A1B29]/95 backdrop-blur-md border border-[#1D3A4C] p-2.5 rounded-xl shadow-2xl flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2">
            <Navigation className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">
              {originName} → {destName}
            </span>
          </div>
          <div className="flex items-center gap-2 border-l border-[#1D3A4C] pl-2 text-slate-400 font-mono text-[10px]">
            <span>Strategy: <strong className="text-cyan-400 uppercase">{strategyName}</strong></span>
            <span>Mode: <strong className="text-amber-400 font-bold">{modeName}</strong></span>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Simulation Control Console & Decision Analysis */}
      <div className="w-[440px] flex-shrink-0 z-10 border-l border-[#1D3A4C] bg-[#06131F]/95 backdrop-blur-md overflow-y-auto p-4 space-y-4">
        {/* Playback Controls & Telemetry */}
        <VoyageControls
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying(!isPlaying)}
          onRestart={restartVoyage}
          speedMultiplier={speedMultiplier}
          onSpeedChange={setSpeedMultiplier}
          activeVoyage={activeVoyage}
          currentRoute={currentRoute}
          progressPercent={progressMetrics.progressPercent}
          distanceTraveledKm={progressMetrics.distanceTraveledKm}
          distanceRemainingKm={progressMetrics.distanceRemainingKm}
        />

        {/* Disruption Detection & Decision Engine Panel */}
        <DecisionPanel
          activeDisruption={activeDisruption}
          alternativeRoute={alternativeRoute}
          currentRoute={currentRoute}
          activeVoyage={activeVoyage}
          viewingAlternative={viewingAlternative}
          onToggleViewAlternative={() => setViewingAlternative(!viewingAlternative)}
          onAcceptAlternative={acceptAlternativeRoute}
          onTriggerDisruption={triggerDisruptionAhead}
          onFocusMap={(lat, lon) => setFocusCoords([lat, lon])}
          isProcessing={isProcessingDisruption}
        />

        {/* Dedicated Voyage Event Timeline Log */}
        <SimulationEventLog eventLog={eventLog} />
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { RouteResponse, Port, OptimizationMode, SimulationEvent } from '../../types/maritime';
import { DEMO_SHIPS, OPTIMIZATION_PRESETS, SIMULATION_PRESETS } from '../../data/demo';
import { Loader2, Zap, Scale, Building, ShieldAlert, CloudLightning, Trash2, Database, AlertCircle } from 'lucide-react';

interface ControlPanelProps {
  ports: Port[];
  onCalculateRoute: (origin: string, destination: string, ship: string, optimization: OptimizationMode, dataMode?: 'HYBRID' | 'MOCK') => void;
  isCalculating: boolean;
  currentRoute: RouteResponse | null;
  dataMode: 'HYBRID' | 'MOCK';
  onDataModeChange: (mode: 'HYBRID' | 'MOCK') => void;
  onTriggerSimulation: (event: SimulationEvent) => void;
  isSimulating: boolean;
  activeSimulation: SimulationEvent | null;
  onClearSimulation: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  ports,
  onCalculateRoute,
  isCalculating,
  currentRoute,
  dataMode,
  onDataModeChange,
  onTriggerSimulation,
  isSimulating,
  activeSimulation,
  onClearSimulation,
}) => {
  const [origin, setOrigin] = useState<string>('mumbai');
  const [destination, setDestination] = useState<string>('singapore');
  const [ship, setShip] = useState<string>('container');
  const [optimization, setOptimization] = useState<OptimizationMode>('BALANCED');

  const sortedPorts = [...ports].sort((a, b) => a.name.localeCompare(b.name));

  const originPortObj = ports.find((p) => p.id === origin);
  const destPortObj = ports.find((p) => p.id === destination);

  const isRoutingSupported =
    (originPortObj?.supported_in_routing ?? true) &&
    (destPortObj?.supported_in_routing ?? true) &&
    origin !== destination;

  const handleCalculate = () => {
    if (!isRoutingSupported) return;
    onCalculateRoute(origin, destination, ship, optimization, dataMode);
  };

  const getOptIcon = (id: string) => {
    switch (id.toUpperCase()) {
      case 'FASTEST':
        return <Zap className="w-5 h-5" />;
      case 'LEAST_CONGESTED':
        return <Building className="w-5 h-5" />;
      case 'BALANCED':
        return <Scale className="w-5 h-5" />;
      case 'SAFEST':
        return <ShieldAlert className="w-5 h-5" />;
      default:
        return <Scale className="w-5 h-5" />;
    }
  };

  return (
    <div className="glass-panel-solid w-80 h-full flex flex-col overflow-y-auto border-r border-maritime-border">
      <div className="p-4 flex-1 space-y-6">
        {/* DATA MODE TOGGLE */}
        <div className="space-y-2">
          <h3 className="section-label flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-maritime-cyan" /> DATA PROVIDER MODE
          </h3>
          <div className="grid grid-cols-2 gap-2 p-1 bg-maritime-panel rounded-lg border border-maritime-border">
            <button
              onClick={() => onDataModeChange('HYBRID')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                dataMode === 'HYBRID'
                  ? 'bg-maritime-cyan text-black shadow'
                  : 'text-maritime-muted hover:text-white'
              }`}
            >
              Copernicus (HYBRID)
            </button>
            <button
              onClick={() => onDataModeChange('MOCK')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                dataMode === 'MOCK'
                  ? 'bg-maritime-cyan text-black shadow'
                  : 'text-maritime-muted hover:text-white'
              }`}
            >
              Mock Engine
            </button>
          </div>
        </div>

        {/* ROUTE CONFIGURATION */}
        <div className="space-y-4">
          <h3 className="section-label">ROUTE CONFIGURATION</h3>

          <div className="space-y-2">
            <label className="text-xs text-maritime-muted-dim">Origin Port</label>
            <select
              className="select-maritime w-full"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            >
              {sortedPorts.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}, {p.country} {p.supported_in_routing === false ? '(Graph Unavail)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs text-maritime-muted-dim">Destination Port</label>
            <select
              className="select-maritime w-full"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            >
              {sortedPorts.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}, {p.country} {p.supported_in_routing === false ? '(Graph Unavail)' : ''}
                </option>
              ))}
            </select>
          </div>

          {!isRoutingSupported && (
            <div className="flex items-start gap-2 p-2.5 rounded bg-red-950/40 border border-red-500/40 text-red-300 text-xs">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>Selected port(s) not supported in graph vertex routing. Select supported ports (e.g. Mumbai, Colombo, Singapore, Kochi).</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs text-maritime-muted-dim">Vessel Profile</label>
            <select
              className="select-maritime w-full"
              value={ship}
              onChange={(e) => setShip(e.target.value)}
            >
              {DEMO_SHIPS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.speed_knots} kts)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* OPTIMIZATION OBJECTIVE */}
        <div className="space-y-3">
          <h3 className="section-label">OPTIMIZATION OBJECTIVE</h3>
          <div className="grid grid-cols-2 gap-2">
            {OPTIMIZATION_PRESETS.map((preset) => {
              const isActive = optimization.toUpperCase() === preset.id;
              return (
                <div
                  key={preset.id}
                  onClick={() => setOptimization(preset.id as OptimizationMode)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                    isActive
                      ? 'border-maritime-cyan shadow-glow bg-maritime-panel-secondary'
                      : 'border-maritime-border hover:border-maritime-muted bg-maritime-panel'
                  }`}
                >
                  <div className={`mb-2 flex items-center ${isActive ? 'text-maritime-cyan' : 'text-maritime-muted'}`}>
                    {getOptIcon(preset.id)}
                  </div>
                  <div className={`text-xs font-semibold font-title ${isActive ? 'text-white' : 'text-maritime-muted'}`}>
                    {preset.label}
                  </div>
                  <div className="text-[10px] text-maritime-muted-dim mt-1 leading-tight">
                    {preset.description}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ACTION */}
        <button
          className="btn-primary w-full flex justify-center items-center py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleCalculate}
          disabled={isCalculating || !isRoutingSupported}
        >
          {isCalculating ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Calculate Route'}
        </button>

        <div className="divider my-4"></div>

        {/* SIMULATION */}
        <div className="space-y-3 pb-4">
          <div className="flex justify-between items-center">
            <h3 className="section-label">SIMULATION DISRUPTIONS</h3>
            {activeSimulation && (
              <button
                onClick={onClearSimulation}
                className="btn-ghost text-maritime-danger hover:text-red-400 text-xs flex items-center gap-1 p-1 h-auto"
              >
                <Trash2 className="w-3 h-3" /> Clear
              </button>
            )}
          </div>

          <div className="space-y-2">
            <button
              className="btn-danger w-full flex items-center gap-2 justify-center text-sm py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentRoute || isSimulating || activeSimulation?.type === 'storm'}
              onClick={() => onTriggerSimulation(SIMULATION_PRESETS.storm)}
            >
              <CloudLightning className="w-4 h-4" /> Tropical Storm Event
            </button>
            <button
              className="btn-warning w-full flex items-center gap-2 justify-center text-sm py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentRoute || isSimulating || activeSimulation?.type === 'port_congestion'}
              onClick={() => onTriggerSimulation(SIMULATION_PRESETS.port_congestion)}
            >
              <Building className="w-4 h-4" /> Port Congestion
            </button>
            <button
              className="btn-danger w-full flex items-center gap-2 justify-center text-sm py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!currentRoute || isSimulating || activeSimulation?.type === 'security'}
              onClick={() => onTriggerSimulation(SIMULATION_PRESETS.security)}
            >
              <ShieldAlert className="w-4 h-4" /> Security Threat Alert
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

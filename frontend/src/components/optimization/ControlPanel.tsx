import React, { useState } from 'react';
import { RouteResponse, Port, OptimizationMode, SimulationEvent } from '../../types/maritime';
import { DEMO_SHIPS, OPTIMIZATION_PRESETS, SIMULATION_PRESETS } from '../../data/demo';
import { Loader2, Zap, Scale, Leaf, ShieldAlert, CloudLightning, Building, Trash2 } from 'lucide-react';

interface ControlPanelProps {
  ports: Port[];
  onCalculateRoute: (origin: string, destination: string, ship: string, optimization: OptimizationMode) => void;
  isCalculating: boolean;
  currentRoute: RouteResponse | null;
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
  onTriggerSimulation,
  isSimulating,
  activeSimulation,
  onClearSimulation,
}) => {
  const [origin, setOrigin] = useState<string>('INBOM'); // Mumbai default
  const [destination, setDestination] = useState<string>('LKCMB'); // Colombo default
  const [ship, setShip] = useState<string>('CONT-01'); // Container default
  const [optimization, setOptimization] = useState<OptimizationMode>('balanced');

  const sortedPorts = [...ports].sort((a, b) => a.name.localeCompare(b.name));

  const handleCalculate = () => {
    onCalculateRoute(origin, destination, ship, optimization);
  };

  const getOptIcon = (id: string) => {
    switch (id) {
      case 'time': return <Zap className="w-5 h-5" />;
      case 'fuel': return <Leaf className="w-5 h-5" />;
      case 'balanced': return <Scale className="w-5 h-5" />;
      case 'safety': return <ShieldAlert className="w-5 h-5" />;
      default: return <Scale className="w-5 h-5" />;
    }
  };

  return (
    <div className="glass-panel-solid w-80 h-full flex flex-col overflow-y-auto border-r border-maritime-border">
      <div className="p-4 flex-1 space-y-6">
        
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
              {sortedPorts.map(p => (
                <option key={p.id} value={p.id}>{p.name}, {p.country}</option>
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
              {sortedPorts.map(p => (
                <option key={p.id} value={p.id}>{p.name}, {p.country}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs text-maritime-muted-dim">Vessel Profile</label>
            <select 
              className="select-maritime w-full"
              value={ship}
              onChange={(e) => setShip(e.target.value)}
            >
              {DEMO_SHIPS.map(s => (
                <option key={s.id} value={s.id}>{s.name} ({s.speed_knots} kts)</option>
              ))}
            </select>
          </div>
        </div>

        {/* OPTIMIZATION OBJECTIVE */}
        <div className="space-y-3">
          <h3 className="section-label">OPTIMIZATION OBJECTIVE</h3>
          <div className="grid grid-cols-2 gap-2">
            {OPTIMIZATION_PRESETS.map((preset) => (
              <div 
                key={preset.id}
                onClick={() => setOptimization(preset.id as OptimizationMode)}
                className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                  optimization === preset.id 
                    ? 'border-maritime-cyan shadow-glow bg-maritime-panel-secondary' 
                    : 'border-maritime-border hover:border-maritime-muted bg-maritime-panel'
                }`}
              >
                <div className={`mb-2 flex items-center ${optimization === preset.id ? 'text-maritime-cyan' : 'text-maritime-muted'}`}>
                  {getOptIcon(preset.id)}
                </div>
                <div className={`text-xs font-semibold font-title ${optimization === preset.id ? 'text-white' : 'text-maritime-muted'}`}>
                  {preset.label}
                </div>
                <div className="text-[10px] text-maritime-muted-dim mt-1 leading-tight">
                  {preset.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ACTION */}
        <button 
          className="btn-primary w-full flex justify-center items-center py-3"
          onClick={handleCalculate}
          disabled={isCalculating}
        >
          {isCalculating ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Calculate Route'}
        </button>

        <div className="divider my-4"></div>

        {/* SIMULATION */}
        <div className="space-y-3 pb-4">
          <div className="flex justify-between items-center">
            <h3 className="section-label">SIMULATION</h3>
            {activeSimulation && (
              <button onClick={onClearSimulation} className="btn-ghost text-maritime-danger hover:text-red-400 text-xs flex items-center gap-1 p-1 h-auto">
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
              <CloudLightning className="w-4 h-4" /> Simulate Storm
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
              <ShieldAlert className="w-4 h-4" /> Security Event
            </button>
          </div>
        </div>
        
      </div>
    </div>
  );
};

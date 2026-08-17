import React from 'react';
import { SimulationEvent } from '../../types/maritime';
import { Loader2, AlertTriangle, ShieldAlert, CloudLightning } from 'lucide-react';

interface SimulationPanelProps {
  activeSimulation: SimulationEvent | null;
  isSimulating: boolean;
}

export const SimulationPanel: React.FC<SimulationPanelProps> = ({ activeSimulation, isSimulating }) => {
  if (isSimulating) {
    return (
      <div className="glass-panel p-3 border border-maritime-warning flex items-center gap-3 animate-pulse-slow w-full max-w-sm">
        <Loader2 className="w-5 h-5 text-maritime-warning animate-spin" />
        <span className="text-sm font-semibold text-maritime-warning tracking-widest">RECALCULATING...</span>
      </div>
    );
  }

  if (activeSimulation) {
    let Icon = AlertTriangle;
    let badgeClass = "badge-warning";
    
    if (activeSimulation.type === 'storm') {
      Icon = CloudLightning;
      badgeClass = "badge-danger";
    } else if (activeSimulation.type === 'security') {
      Icon = ShieldAlert;
      badgeClass = "badge-danger";
    }

    return (
      <div className="glass-panel p-3 border border-maritime-border flex items-center gap-3 w-full max-w-sm">
        <Icon className={`w-5 h-5 ${badgeClass.includes('danger') ? 'text-maritime-danger' : 'text-maritime-warning'}`} />
        <div className="flex flex-col flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-white">{activeSimulation.label || activeSimulation.type}</span>
            <span className={badgeClass}>{activeSimulation.severity.toFixed(2)}</span>
          </div>
          <span className="text-xs text-maritime-muted">
            Lat: {activeSimulation.lat.toFixed(2)}, Lng: {activeSimulation.lon.toFixed(2)} - {activeSimulation.radius_km} km impact
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-panel p-3 border border-maritime-border flex items-center justify-center w-full max-w-sm">
      <span className="text-sm text-maritime-muted-dim">No active simulation</span>
    </div>
  );
};

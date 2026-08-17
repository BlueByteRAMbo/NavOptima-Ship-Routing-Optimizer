import React from 'react';
import { Ruler, Clock, Fuel, ShieldCheck } from 'lucide-react';
import { RouteResponse } from '../../types/maritime';

interface RouteStatsProps {
  route: RouteResponse | null;
}

const RouteStats: React.FC<RouteStatsProps> = ({ route }) => {
  if (!route) return null;

  const getSafetyColor = (score: number) => {
    if (score >= 85) return 'text-maritime-success';
    if (score >= 70) return 'text-maritime-cyan';
    return 'text-maritime-warning';
  };

  return (
    <div className="flex flex-col space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="stat-card glass-panel flex items-center p-3 rounded-lg border border-maritime-border">
          <div className="p-2 bg-maritime-panel-secondary rounded mr-3">
            <Ruler className="w-5 h-5 text-maritime-cyan" />
          </div>
          <div className="flex flex-col">
            <span className="stat-label text-xs text-maritime-muted">Distance</span>
            <div>
              <span className="stat-value text-lg text-white font-semibold">{route.distance_km.toFixed(1)}</span>
              <span className="stat-unit text-xs ml-1 text-maritime-muted">km</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel flex items-center p-3 rounded-lg border border-maritime-border">
          <div className="p-2 bg-maritime-panel-secondary rounded mr-3">
            <Clock className="w-5 h-5 text-maritime-cyan" />
          </div>
          <div className="flex flex-col">
            <span className="stat-label text-xs text-maritime-muted">ETA</span>
            <div>
              <span className="stat-value text-lg text-white font-semibold">{route.eta_hours.toFixed(1)}</span>
              <span className="stat-unit text-xs ml-1 text-maritime-muted">h</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel flex items-center p-3 rounded-lg border border-maritime-border">
          <div className="p-2 bg-maritime-panel-secondary rounded mr-3">
            <Fuel className="w-5 h-5 text-maritime-cyan" />
          </div>
          <div className="flex flex-col">
            <span className="stat-label text-xs text-maritime-muted">Fuel</span>
            <div>
              <span className="stat-value text-lg text-white font-semibold">{route.fuel_mt.toFixed(1)}</span>
              <span className="stat-unit text-xs ml-1 text-maritime-muted">MT</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel flex items-center p-3 rounded-lg border border-maritime-border">
          <div className="p-2 bg-maritime-panel-secondary rounded mr-3">
            <ShieldCheck className={`w-5 h-5 ${getSafetyColor(route.safety_score).replace('text-', 'bg-transparent text-')}`} />
          </div>
          <div className="flex flex-col">
            <span className="stat-label text-xs text-maritime-muted">Safety</span>
            <div>
              <span className={`stat-value text-lg font-semibold ${getSafetyColor(route.safety_score)}`}>{route.safety_score.toFixed(0)}</span>
              <span className="stat-unit text-xs ml-1 text-maritime-muted">%</span>
            </div>
          </div>
        </div>
      </div>
      {route.reason && (
        <div className="text-xs text-maritime-muted-dim italic mt-2 p-2 bg-maritime-panel-secondary rounded border border-maritime-border">
          {route.reason}
        </div>
      )}
    </div>
  );
};

export default RouteStats;

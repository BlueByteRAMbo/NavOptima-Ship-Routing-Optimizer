import React from 'react';
import { EnvironmentCell, RouteResponse } from '../../types/maritime';
import { Wind, Waves, Navigation, AlertTriangle } from 'lucide-react';

interface WeatherSummaryProps {
  environment: EnvironmentCell[];
  route: RouteResponse | null;
}

const WeatherSummary: React.FC<WeatherSummaryProps> = ({ environment, route }) => {
  if (!route || environment.length === 0) {
    return <div className="text-xs text-maritime-muted">No route or environment data available.</div>;
  }

  // Simplified: compute averages/max from the environment grid
  const avgWind = environment.reduce((sum, cell) => sum + cell.wind_speed, 0) / environment.length;
  const maxWave = Math.max(...environment.map(cell => cell.wave_height));
  const avgCurrent = environment.reduce((sum, cell) => sum + Math.sqrt(Math.pow(cell.current_u, 2) + Math.pow(cell.current_v, 2)), 0) / environment.length;
  const avgSecurity = environment.reduce((sum, cell) => sum + cell.security_risk, 0) / environment.length;

  const getRiskColor = (risk: number) => {
    if (risk > 0.7) return 'bg-maritime-danger';
    if (risk > 0.4) return 'bg-maritime-warning';
    return 'bg-maritime-success';
  };

  const getWaveColor = (wave: number) => {
    if (wave > 5) return 'bg-maritime-danger';
    if (wave > 2.5) return 'bg-maritime-warning';
    return 'bg-maritime-cyan';
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="flex items-center space-x-3 bg-maritime-panel-secondary p-2 rounded border border-maritime-border">
        <Wind className="w-5 h-5 text-maritime-muted" />
        <div className="flex flex-col">
          <span className="text-[10px] text-maritime-muted uppercase tracking-wider">Avg Wind</span>
          <div className="flex items-center">
            <span className="text-sm text-white font-medium">{avgWind.toFixed(1)}</span>
            <span className="text-[10px] text-maritime-muted ml-1">knots</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3 bg-maritime-panel-secondary p-2 rounded border border-maritime-border">
        <Waves className="w-5 h-5 text-maritime-muted" />
        <div className="flex flex-col w-full">
          <span className="text-[10px] text-maritime-muted uppercase tracking-wider">Max Wave</span>
          <div className="flex items-center">
            <span className="text-sm text-white font-medium">{maxWave.toFixed(1)}</span>
            <span className="text-[10px] text-maritime-muted ml-1">m</span>
          </div>
          <div className="w-full bg-maritime-panel h-1 mt-1 rounded overflow-hidden">
            <div className={`h-full ${getWaveColor(maxWave)}`} style={{ width: `${Math.min(100, (maxWave / 8) * 100)}%` }}></div>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3 bg-maritime-panel-secondary p-2 rounded border border-maritime-border">
        <Navigation className="w-5 h-5 text-maritime-muted" />
        <div className="flex flex-col">
          <span className="text-[10px] text-maritime-muted uppercase tracking-wider">Avg Current</span>
          <div className="flex items-center">
            <span className="text-sm text-white font-medium">{avgCurrent.toFixed(2)}</span>
            <span className="text-[10px] text-maritime-muted ml-1">m/s</span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3 bg-maritime-panel-secondary p-2 rounded border border-maritime-border">
        <AlertTriangle className="w-5 h-5 text-maritime-muted" />
        <div className="flex flex-col w-full">
          <span className="text-[10px] text-maritime-muted uppercase tracking-wider">Security Risk</span>
          <div className="flex items-center justify-between w-full">
            <span className="text-sm text-white font-medium">{(avgSecurity * 100).toFixed(0)}</span>
            <span className="text-[10px] text-maritime-muted ml-1">%</span>
          </div>
          <div className="w-full bg-maritime-panel h-1 mt-1 rounded overflow-hidden">
            <div className={`h-full ${getRiskColor(avgSecurity)}`} style={{ width: `${avgSecurity * 100}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherSummary;

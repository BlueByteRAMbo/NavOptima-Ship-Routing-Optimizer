import React from 'react';
import { RouteResponse, SimulationResponse } from '../../types/maritime';
import { ArrowUp, ArrowDown, TrendingUp } from 'lucide-react';

interface RouteComparisonProps {
  simulationResult: SimulationResponse | null;
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
}

const RouteComparison: React.FC<RouteComparisonProps> = ({
  simulationResult,
  currentRoute,
  previousRoute
}) => {
  if (!simulationResult || !currentRoute || !previousRoute) return null;

  const etaDiff = currentRoute.eta_hours - previousRoute.eta_hours;
  const fuelDiff = currentRoute.fuel_mt - previousRoute.fuel_mt;
  const safetyDiff = currentRoute.safety_score - previousRoute.safety_score;

  const renderDiff = (diff: number, unit: string, invertColors = false) => {
    const isPositive = diff > 0;
    const isNeutral = Math.abs(diff) < 0.01;
    
    // For ETA and Fuel, lower is better. For safety, higher is better.
    const isGood = invertColors ? isPositive : !isPositive;
    
    const colorClass = isNeutral ? 'text-maritime-muted' : (isGood ? 'text-maritime-success' : 'text-maritime-danger');
    const Icon = isNeutral ? TrendingUp : (isPositive ? ArrowUp : ArrowDown);

    return (
      <div className={`flex items-center text-sm font-semibold ${colorClass}`}>
        {!isNeutral && <Icon className="w-4 h-4 mr-1" />}
        {diff > 0 ? '+' : ''}{diff.toFixed(1)} {unit}
      </div>
    );
  };

  return (
    <div className="flex flex-col space-y-3 animate-slide-up bg-maritime-panel-secondary p-3 rounded-lg border border-maritime-border">
      <div className="text-sm text-maritime-cyan font-semibold mb-2">Simulation Result</div>
      
      <div className="grid grid-cols-3 gap-2 divide-x divide-maritime-border text-center">
        <div className="flex flex-col items-center">
          <span className="text-xs text-maritime-muted mb-1">ETA Change</span>
          {renderDiff(etaDiff, 'h')}
        </div>
        <div className="flex flex-col items-center">
          <span className="text-xs text-maritime-muted mb-1">Fuel Change</span>
          {renderDiff(fuelDiff, 'MT')}
        </div>
        <div className="flex flex-col items-center">
          <span className="text-xs text-maritime-muted mb-1">Safety Change</span>
          {renderDiff(safetyDiff, 'pts', true)}
        </div>
      </div>

      {simulationResult.reason && (
        <div className="text-xs text-maritime-muted mt-3">
          <span className="text-white font-medium">Reasoning: </span>
          {simulationResult.reason}
        </div>
      )}
    </div>
  );
};

export default RouteComparison;

import React, { useState, useEffect } from 'react';
import { Navigation, CloudLightning, ShieldAlert, Clock } from 'lucide-react';

interface HeaderProps {
  showWeatherLayer: boolean;
  showRiskLayer: boolean;
  onToggleWeather: () => void;
  onToggleRisk: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  showWeatherLayer,
  showRiskLayer,
  onToggleWeather,
  onToggleRisk,
}) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="w-full h-[56px] bg-maritime-panel border-b border-maritime-border flex items-center justify-between px-4 z-50">
      <div className="flex items-center gap-2">
        <Navigation className="w-6 h-6 text-maritime-cyan" />
        <div className="flex flex-col">
          <span className="font-semibold text-white text-xl leading-tight font-title tracking-wide">
            <span className="text-maritime-cyan">Nav</span>Optima
          </span>
          <span className="text-xs text-maritime-muted leading-none">Ship Routing Optimizer</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="badge-warning">DEMO MODE</span>
        <div className="flex items-center gap-1 text-maritime-cyan-dim text-sm font-mono">
          <Clock className="w-4 h-4" />
          {time.toISOString().replace('T', ' ').substring(0, 19)} UTC
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onToggleWeather}
          className={`btn-ghost text-sm flex items-center gap-2 ${showWeatherLayer ? 'text-maritime-cyan' : 'text-maritime-muted'}`}
        >
          <CloudLightning className="w-4 h-4" />
          Weather Layer
        </button>
        <button
          onClick={onToggleRisk}
          className={`btn-ghost text-sm flex items-center gap-2 ${showRiskLayer ? 'text-maritime-danger' : 'text-maritime-muted'}`}
        >
          <ShieldAlert className="w-4 h-4" />
          Risk Layer
        </button>
      </div>
    </header>
  );
};

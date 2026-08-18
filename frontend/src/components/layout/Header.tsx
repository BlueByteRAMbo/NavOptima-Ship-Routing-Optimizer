import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Navigation, CloudLightning, ShieldAlert, Clock, Waves, Compass, PlayCircle } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface HeaderProps {
  showWeatherLayer: boolean;
  showRiskLayer: boolean;
  showOceanCurrents: boolean;
  onToggleWeather: () => void;
  onToggleRisk: () => void;
  onToggleOceanCurrents: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  showWeatherLayer,
  showRiskLayer,
  showOceanCurrents,
  onToggleWeather,
  onToggleRisk,
  onToggleOceanCurrents,
}) => {
  const [time, setTime] = useState(new Date());
  const location = useLocation();
  const { currentRoute, activeVoyage } = useApp();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const isOptimizer = location.pathname === '/';
  const isSimulation = location.pathname === '/simulation';

  return (
    <header className="w-full h-[56px] bg-[#0A1B29] border-b border-[#1D3A4C] flex items-center justify-between px-4 z-50">
      {/* Brand Logo & Navigation Links */}
      <div className="flex items-center gap-6">
        <Link to="/" className="flex items-center gap-2 group">
          <Navigation className="w-6 h-6 text-cyan-400 group-hover:rotate-12 transition-transform" />
          <div className="flex flex-col">
            <span className="font-semibold text-white text-xl leading-tight tracking-wide">
              <span className="text-cyan-400">Nav</span>Optima
            </span>
            <span className="text-[10px] text-slate-400 leading-none">Ship Routing Optimizer</span>
          </div>
        </Link>

        {/* Primary Page Navigation Tabs */}
        <div className="flex items-center gap-1 bg-[#06131F] p-1 rounded-lg border border-[#1D3A4C]">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isOptimizer
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Route Optimizer</span>
          </Link>

          <Link
            to="/simulation"
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all relative ${
              isSimulation
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <PlayCircle className="w-3.5 h-3.5" />
            <span>Voyage Simulation</span>
            {(currentRoute || activeVoyage) && (
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping absolute top-1 right-1"></span>
            )}
          </Link>
        </div>
      </div>

      {/* Clock & Status */}
      <div className="hidden md:flex items-center gap-4">
        <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 text-[10px] font-bold rounded">
          DEMO MODE
        </span>
        <div className="flex items-center gap-1.5 text-cyan-400 text-xs font-mono">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          {time.toISOString().replace('T', ' ').substring(0, 19)} UTC
        </div>
      </div>

      {/* Layer Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleOceanCurrents}
          className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border ${
            showOceanCurrents
              ? 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10'
              : 'text-slate-400 border-[#1D3A4C] hover:text-white'
          }`}
        >
          <Waves className="w-3.5 h-3.5" />
          <span>Ocean Currents</span>
        </button>

        <button
          onClick={onToggleWeather}
          className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border ${
            showWeatherLayer
              ? 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10'
              : 'text-slate-400 border-[#1D3A4C] hover:text-white'
          }`}
        >
          <CloudLightning className="w-3.5 h-3.5" />
          <span>Weather Layer</span>
        </button>

        <button
          onClick={onToggleRisk}
          className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border ${
            showRiskLayer
              ? 'text-red-400 border-red-500/40 bg-red-500/10'
              : 'text-slate-400 border-[#1D3A4C] hover:text-white'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Risk Layer</span>
        </button>
      </div>
    </header>
  );
};

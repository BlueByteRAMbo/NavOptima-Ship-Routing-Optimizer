import React from 'react';
import { Play, Pause, RotateCcw, FastForward, Clock, Compass, Shield, Fuel, MapPin } from 'lucide-react';
import type { VoyageStateResponse, RouteResponse } from '../../types/maritime';

interface VoyageControlsProps {
  isPlaying: boolean;
  onTogglePlay: () => void;
  onRestart: () => void;
  speedMultiplier: number | 'AUTO';
  onSpeedChange: (speed: number | 'AUTO') => void;
  activeVoyage: VoyageStateResponse | null;
  currentRoute: RouteResponse | null;
  progressPercent: number;
  distanceTraveledKm: number;
  distanceRemainingKm: number;
}

export const VoyageControls: React.FC<VoyageControlsProps> = ({
  isPlaying,
  onTogglePlay,
  onRestart,
  speedMultiplier,
  onSpeedChange,
  activeVoyage,
  currentRoute,
  progressPercent,
  distanceTraveledKm,
  distanceRemainingKm,
}) => {
  const speeds: (number | 'AUTO')[] = ['AUTO', 1, 5, 10, 25, 50];

  const formatHoursToHHMM = (hours: number) => {
    const hh = Math.floor(hours);
    const mm = Math.floor((hours - hh) * 60);
    return `${hh.toString().padStart(2, '0')}:${mm.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-[#0A1B29] border border-[#1D3A4C] rounded-xl p-4 space-y-4 shadow-xl text-slate-200">
      {/* Header & Playback Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1D3A4C] pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={onTogglePlay}
            disabled={!activeVoyage || activeVoyage.is_completed}
            className={`px-4 py-2 rounded-lg font-bold text-xs flex items-center gap-2 transition-all shadow-md ${
              isPlaying
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950'
                : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 disabled:opacity-50'
            }`}
          >
            {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{isPlaying ? 'PAUSE VOYAGE' : 'PLAY SIMULATION'}</span>
          </button>

          <button
            onClick={onRestart}
            disabled={!activeVoyage}
            className="px-3 py-2 bg-[#06131F] hover:bg-slate-800 text-slate-300 border border-[#1D3A4C] rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            title="Restart Voyage to Start Position"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Restart</span>
          </button>
        </div>

        {/* Speed Multiplier Bar */}
        <div className="flex items-center gap-1 bg-[#06131F] p-1 rounded-lg border border-[#1D3A4C]">
          <span className="text-[10px] font-bold text-slate-400 uppercase px-1.5 flex items-center gap-1">
            <FastForward className="w-3 h-3 text-cyan-400" /> SPEED:
          </span>
          {speeds.map((s) => (
            <button
              key={s}
              onClick={() => onSpeedChange(s)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all ${
                speedMultiplier === s
                  ? 'bg-cyan-400 text-slate-950 font-extrabold shadow'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
              title={s === 'AUTO' ? 'Auto Demo Mode (~75s playback)' : `${s}x Speed`}
            >
              {s === 'AUTO' ? 'DEMO (~75s)' : `${s}x`}
            </button>
          ))}
        </div>
      </div>

      {/* Voyage Progress Timeline Slider Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-mono">
          <span className="text-slate-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-cyan-400" /> Simulated Time:
            <strong className="text-white ml-1">
              {formatHoursToHHMM(activeVoyage?.current_time || 0)}h
            </strong> / {currentRoute?.eta_hours?.toFixed(1) || '--'}h
          </span>
          <span className="text-cyan-400 font-bold font-mono">
            {progressPercent}% Complete
          </span>
        </div>

        {/* Progress Bar Container */}
        <div className="relative w-full h-3 bg-[#06131F] rounded-full border border-[#1D3A4C] overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-300 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Real-time Telemetry Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-xs">
        <div className="bg-[#06131F] p-2.5 rounded-lg border border-[#1D3A4C]">
          <span className="text-[10px] text-slate-400 block uppercase flex items-center gap-1">
            <MapPin className="w-3 h-3 text-cyan-400" /> Vessel Coords
          </span>
          <span className="font-bold text-white text-xs mt-0.5 block">
            {activeVoyage ? `${activeVoyage.current_lat.toFixed(2)}°, ${activeVoyage.current_lon.toFixed(2)}°` : '--'}
          </span>
        </div>

        <div className="bg-[#06131F] p-2.5 rounded-lg border border-[#1D3A4C]">
          <span className="text-[10px] text-slate-400 block uppercase flex items-center gap-1">
            <Compass className="w-3 h-3 text-cyan-400" /> Distance
          </span>
          <span className="font-bold text-white text-xs mt-0.5 block truncate">
            {distanceTraveledKm} km / {distanceRemainingKm} km rem.
          </span>
        </div>

        <div className="bg-[#06131F] p-2.5 rounded-lg border border-[#1D3A4C]">
          <span className="text-[10px] text-slate-400 block uppercase flex items-center gap-1">
            <Fuel className="w-3 h-3 text-amber-400" /> Est. Fuel
          </span>
          <span className="font-bold text-white text-xs mt-0.5 block">
            {currentRoute?.fuel_mt?.toFixed(1) || '--'} MT
          </span>
        </div>

        <div className="bg-[#06131F] p-2.5 rounded-lg border border-[#1D3A4C]">
          <span className="text-[10px] text-slate-400 block uppercase flex items-center gap-1">
            <Shield className="w-3 h-3 text-emerald-400" /> Safety Score
          </span>
          <span className="font-bold text-emerald-400 text-xs mt-0.5 block">
            {currentRoute?.safety_score?.toFixed(1) || '--'} / 100
          </span>
        </div>
      </div>
    </div>
  );
};

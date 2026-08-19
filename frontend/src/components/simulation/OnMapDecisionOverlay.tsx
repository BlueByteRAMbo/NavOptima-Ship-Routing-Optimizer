import React from 'react';
import { AlertTriangle, CheckCircle2, Shield, Fuel, Clock, Crosshair, ArrowRight, Maximize2, Info } from 'lucide-react';
import type { SimulationResponse, RouteResponse, VoyageStateResponse } from '../../types/maritime';

interface OnMapDecisionOverlayProps {
  activeDisruption: SimulationResponse | null;
  alternativeRoute: RouteResponse | null;
  currentRoute: RouteResponse | null;
  activeVoyage: VoyageStateResponse | null;
  onAcceptAlternative: () => void;
  onKeepCurrent: () => void;
  onFocusMap?: (lat: number, lon: number) => void;
  onResetView?: () => void;
}

export const OnMapDecisionOverlay: React.FC<OnMapDecisionOverlayProps> = ({
  activeDisruption,
  alternativeRoute,
  currentRoute,
  activeVoyage,
  onAcceptAlternative,
  onKeepCurrent,
  onFocusMap,
  onResetView,
}) => {
  if (!activeDisruption) return null;

  const coords = (activeDisruption.new_route && activeDisruption.new_route.length > 0)
    ? activeDisruption.new_route
    : (activeDisruption.old_route && activeDisruption.old_route.length > 0)
    ? activeDisruption.old_route
    : null;
  const midPoint = coords ? coords[Math.floor(coords.length / 2)] : null;

  // Authoritative Remaining ETA and Fuel from Current Vessel Position
  const totalOriginalEta = currentRoute?.eta_hours || activeVoyage?.active_route?.eta_hours || 0;
  const elapsedTime = activeVoyage?.current_time || 0;
  
  // Current route remaining metrics from current position
  const currentRemainingEta = activeDisruption.eta_before ?? Math.max(0, totalOriginalEta - elapsedTime);
  const currentRemainingFuel = activeDisruption.fuel_before ?? currentRoute?.fuel_mt ?? 0;
  const currentSafetyScore = activeDisruption.safety_before ?? currentRoute?.safety_score ?? 0;

  // Alternative route remaining metrics from current position
  const altRemainingEta = activeDisruption.eta_after ?? alternativeRoute?.eta_hours ?? 0;
  const altRemainingFuel = activeDisruption.fuel_after ?? alternativeRoute?.fuel_mt ?? 0;
  const altSafetyScore = activeDisruption.safety_after ?? alternativeRoute?.safety_score ?? 0;

  const etaDelta = activeDisruption.eta_change_hours || (altRemainingEta - currentRemainingEta);
  const isAlternativeBetter = (activeDisruption.decision === 'REROUTE' || (alternativeRoute && etaDelta < -0.5));
  const isSafetyViolated = (activeVoyage?.strategy === 'SAFEST' || activeVoyage?.strategy === 'safest') && (altSafetyScore < currentSafetyScore - 5);

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] w-[94%] max-w-lg bg-[#0A1B29]/95 backdrop-blur-md border-2 border-amber-500/60 rounded-2xl p-4 shadow-2xl space-y-3 text-slate-200 animate-in fade-in zoom-in-95 duration-200">
      {/* Header Badge */}
      <div className="flex items-center justify-between border-b border-[#1D3A4C] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/50 flex items-center justify-center text-amber-400 animate-pulse">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wide flex items-center gap-1.5">
              ⚠️ CONGESTION / DISRUPTION AHEAD — PAUSED
            </h3>
            <span className="text-[10px] text-slate-400 font-mono block">
              {activeDisruption.event_type?.toUpperCase().replace('_', ' ')} DETECTED AHEAD
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {onFocusMap && midPoint && midPoint.length >= 2 && (
            <button
              onClick={() => onFocusMap(midPoint[0], midPoint[1])}
              className="px-2 py-1 bg-[#06131F] hover:bg-slate-800 text-cyan-400 border border-cyan-500/40 rounded text-[10px] font-bold flex items-center gap-1 transition-colors"
              title="Focus Map on Disruption"
            >
              <Crosshair className="w-3 h-3" />
              <span>VIEW ON MAP</span>
            </button>
          )}

          {onResetView && (
            <button
              onClick={onResetView}
              className="p-1 bg-[#06131F] hover:bg-slate-800 text-slate-300 border border-[#1D3A4C] rounded text-[10px] font-semibold transition-colors"
              title="Reset Voyage View"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Total Voyage Overview Bar (Clearly Separates Total vs Remaining) */}
      <div className="bg-[#06131F] px-3 py-1.5 rounded-lg border border-[#1D3A4C] flex justify-between items-center text-[10px] font-mono text-slate-400">
        <span>Original Voyage: <strong className="text-white">{totalOriginalEta.toFixed(1)}h</strong></span>
        <span>Elapsed: <strong className="text-cyan-400">{elapsedTime.toFixed(1)}h</strong></span>
        <span>Current Rem.: <strong className="text-amber-400">{currentRemainingEta.toFixed(1)}h</strong></span>
      </div>

      {/* Disruption Impact Rationale */}
      <div className="bg-[#06131F] p-2.5 rounded-lg border border-[#1D3A4C] space-y-1">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400 font-mono flex items-center gap-1">
            <Info className="w-3 h-3 text-cyan-400" /> Backend Rationale:
          </span>
          <span className={`px-2 py-0.5 text-[9px] font-bold rounded uppercase border ${
            activeDisruption.decision === 'REROUTE'
              ? 'bg-red-500/20 text-red-400 border-red-500/40'
              : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
          }`}>
            {activeDisruption.decision}
          </span>
        </div>
        <p className="text-[11px] font-mono text-slate-200 leading-relaxed">
          {activeDisruption.reason}
        </p>
        {isSafetyViolated && (
          <p className="text-[10px] font-mono text-amber-400 italic border-t border-[#1D3A4C] pt-1 mt-1">
            ⚠️ NavOptima Recommendation: KEEP CURRENT ROUTE (Alternative is faster but violates SAFEST strategy).
          </p>
        )}
      </div>

      {/* Side-by-Side Route Metrics Comparison Table (Calculated from CURRENT POSITION) */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        {/* Current Route Remaining */}
        <div className="bg-[#06131F] p-2.5 rounded-lg border border-cyan-500/40 space-y-1">
          <div className="text-[9px] font-bold text-cyan-400 uppercase tracking-wider flex items-center justify-between border-b border-[#1D3A4C] pb-0.5">
            <span>CURRENT ROUTE</span>
            <span className="text-slate-400">REMAINING</span>
          </div>
          <div className="space-y-0.5 text-[10px]">
            <div className="flex justify-between">
              <span className="text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3 text-cyan-400"/> Rem. ETA:</span>
              <strong className="text-white">{currentRemainingEta.toFixed(1)}h {etaDelta > 0 ? `(+${etaDelta.toFixed(1)}h)` : ''}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 flex items-center gap-1"><Fuel className="w-3 h-3 text-amber-400"/> Rem. Fuel:</span>
              <strong className="text-white">{currentRemainingFuel.toFixed(1)} MT</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 flex items-center gap-1"><Shield className="w-3 h-3 text-emerald-400"/> Safety:</span>
              <strong className="text-emerald-400">{currentSafetyScore.toFixed(1)}</strong>
            </div>
          </div>
        </div>

        {/* Alternative Route Remaining (From Current Position) */}
        <div className="bg-[#06131F] p-2.5 rounded-lg border border-amber-500/50 space-y-1">
          <div className="text-[9px] font-bold text-amber-400 uppercase tracking-wider flex items-center justify-between border-b border-[#1D3A4C] pb-0.5">
            <span>ALTERNATIVE ROUTE</span>
            <span className="text-amber-400 font-bold">FROM SHIP</span>
          </div>
          {alternativeRoute || activeDisruption.decision === 'REROUTE' ? (
            <div className="space-y-0.5 text-[10px]">
              <div className="flex justify-between">
                <span className="text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3 text-cyan-400"/> Rem. ETA:</span>
                <strong className={altRemainingEta < currentRemainingEta ? 'text-emerald-400' : 'text-amber-400'}>
                  {altRemainingEta.toFixed(1)}h {altRemainingEta > currentRemainingEta ? `(+${(altRemainingEta - currentRemainingEta).toFixed(1)}h)` : ''}
                </strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 flex items-center gap-1"><Fuel className="w-3 h-3 text-amber-400"/> Rem. Fuel:</span>
                <strong className="text-white">{altRemainingFuel.toFixed(1)} MT</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 flex items-center gap-1"><Shield className="w-3 h-3 text-emerald-400"/> Safety:</span>
                <strong className={altSafetyScore >= currentSafetyScore ? 'text-emerald-400' : 'text-amber-400'}>
                  {altSafetyScore.toFixed(1)}
                </strong>
              </div>
            </div>
          ) : (
            <div className="text-[10px] text-slate-400 italic pt-1 leading-tight">
              No alternative route provides cost improvement beyond hysteresis.
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2 pt-0.5">
        {(alternativeRoute || isAlternativeBetter) && (
          <button
            onClick={onAcceptAlternative}
            className="flex-1 py-2 px-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 transition-all shadow-md shadow-emerald-950/40"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>USE ALTERNATIVE</span>
          </button>
        )}

        <button
          onClick={onKeepCurrent}
          className={`py-2 px-3 bg-[#06131F] hover:bg-slate-800 text-slate-200 font-bold text-xs border border-[#1D3A4C] rounded-lg flex items-center justify-center gap-1.5 transition-all ${
            !(alternativeRoute || isAlternativeBetter) ? 'flex-1 bg-cyan-600 hover:bg-cyan-500 text-white' : ''
          }`}
        >
          <span>KEEP CURRENT ROUTE</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

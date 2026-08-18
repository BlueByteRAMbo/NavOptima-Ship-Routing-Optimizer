import React from 'react';
import { AlertTriangle, ShieldAlert, Anchor, Eye, CheckCircle2, CloudLightning } from 'lucide-react';
import type { SimulationResponse, RouteResponse, VoyageStateResponse } from '../../types/maritime';

interface DecisionPanelProps {
  activeDisruption: SimulationResponse | null;
  alternativeRoute: RouteResponse | null;
  currentRoute: RouteResponse | null;
  activeVoyage?: VoyageStateResponse | null;
  viewingAlternative: boolean;
  onToggleViewAlternative: () => void;
  onAcceptAlternative: () => void;
  onTriggerDisruption: (type: 'storm' | 'port_congestion' | 'security') => void;
  onFocusMap?: (lat: number, lon: number) => void;
  isProcessing: boolean;
}

export const DecisionPanel: React.FC<DecisionPanelProps> = ({
  activeDisruption,
  alternativeRoute,
  currentRoute,
  activeVoyage,
  viewingAlternative,
  onToggleViewAlternative,
  onAcceptAlternative,
  onTriggerDisruption,
  onFocusMap,
  isProcessing,
}) => {
  const totalOriginalEta = currentRoute?.eta_hours || activeVoyage?.active_route?.eta_hours || 0;
  const elapsedTime = activeVoyage?.current_time || 0;
  
  const currentRemainingEta = activeDisruption?.eta_before ?? Math.max(0, totalOriginalEta - elapsedTime);
  const currentRemainingFuel = activeDisruption?.fuel_before ?? currentRoute?.fuel_mt ?? 0;
  const currentSafetyScore = activeDisruption?.safety_before ?? currentRoute?.safety_score ?? 0;

  const altRemainingEta = activeDisruption?.eta_after ?? alternativeRoute?.eta_hours ?? 0;
  const altRemainingFuel = activeDisruption?.fuel_after ?? alternativeRoute?.fuel_mt ?? 0;
  const altSafetyScore = activeDisruption?.safety_after ?? alternativeRoute?.safety_score ?? 0;

  return (
    <div className="bg-[#0A1B29] border border-[#1D3A4C] rounded-xl p-4 space-y-4 shadow-xl text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1D3A4C] pb-2">
        <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Disruption & Route Decision Engine
        </h3>
        <span className="text-[10px] text-slate-400 font-mono">Backend Authoritative</span>
      </div>

      {/* Disruption Trigger Buttons */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
          Inject Disruption Ahead of Vessel:
        </span>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => onTriggerDisruption('storm')}
            disabled={isProcessing}
            className="px-2.5 py-1.5 bg-[#06131F] hover:bg-amber-950/40 text-amber-400 border border-amber-500/40 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <CloudLightning className="w-3.5 h-3.5" />
            <span>Storm</span>
          </button>

          <button
            onClick={() => onTriggerDisruption('port_congestion')}
            disabled={isProcessing}
            className="px-2.5 py-1.5 bg-[#06131F] hover:bg-amber-950/40 text-amber-400 border border-amber-500/40 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Anchor className="w-3.5 h-3.5" />
            <span>Congestion</span>
          </button>

          <button
            onClick={() => onTriggerDisruption('security')}
            disabled={isProcessing}
            className="px-2.5 py-1.5 bg-[#06131F] hover:bg-red-950/40 text-red-400 border border-red-500/40 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Security</span>
          </button>
        </div>
      </div>

      {/* Active Disruption Banner & Decision Analysis */}
      {activeDisruption ? (
        <div className="space-y-3 pt-1">
          <div className="bg-amber-500/10 border border-amber-500/40 p-3 rounded-lg text-xs space-y-2">
            <div className="flex items-center justify-between font-bold text-amber-400">
              <span className="flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                ⚠️ DISRUPTION DETECTED
              </span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 uppercase font-mono">
                  Sev: {activeDisruption.severity?.toFixed(2) || '0.85'}
                </span>
                {activeDisruption.new_route && activeDisruption.new_route.length > 0 && onFocusMap && (
                  <button
                    onClick={() => {
                      const coords = activeDisruption.new_route;
                      const mid = coords[Math.floor(coords.length / 2)];
                      if (mid) onFocusMap(mid[0], mid[1]);
                    }}
                    className="px-2 py-0.5 bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-400 border border-cyan-500/40 rounded text-[10px] font-bold flex items-center gap-1 transition-colors"
                  >
                    <Eye className="w-3 h-3" />
                    <span>VIEW ON MAP</span>
                  </button>
                )}
              </div>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Disruption identified ahead on active corridor. Remaining metrics calculated from current vessel position.
            </p>
          </div>

          {/* Decision Status Badge */}
          <div className="bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                NAVOPTIMA DECISION
              </span>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded border uppercase ${
                activeDisruption.decision === 'REROUTE'
                  ? 'bg-red-500/20 text-red-400 border-red-500/40'
                  : activeDisruption.decision === 'ROUTE_RETAINED'
                  ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
                  : 'bg-slate-700/60 text-slate-300 border-slate-600'
              }`}>
                {activeDisruption.decision || 'EVALUATED'}
              </span>
            </div>

            <p className="text-xs font-mono text-slate-300 bg-[#0A1B29] p-2.5 rounded border border-[#1D3A4C] leading-relaxed">
              {activeDisruption.reason}
            </p>
          </div>

          {/* Alternative Route Comparison & What-If Actions */}
          {alternativeRoute && (
            <div className="bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C] space-y-3">
              <h4 className="text-[11px] font-bold text-amber-400 uppercase tracking-wider flex items-center justify-between">
                <span>"What If I Take The Alternative?"</span>
                <span className="text-[9px] text-slate-400 font-mono">From Current Ship Pos</span>
              </h4>

              {/* Metrics Side-by-Side Comparison Table */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="bg-[#0A1B29] p-2 rounded border border-cyan-500/30">
                  <span className="text-[9px] font-bold text-cyan-400 block uppercase mb-1">
                    CURRENT (REMAINING)
                  </span>
                  <div className="space-y-0.5 text-[11px]">
                    <div>Rem. ETA: <span className="font-bold text-white">{currentRemainingEta.toFixed(1)}h</span></div>
                    <div>Rem. Fuel: <span className="font-bold text-white">{currentRemainingFuel.toFixed(1)} MT</span></div>
                    <div>Safety: <span className="font-bold text-emerald-400">{currentSafetyScore.toFixed(1)}</span></div>
                  </div>
                </div>

                <div className="bg-[#0A1B29] p-2 rounded border border-amber-500/30">
                  <span className="text-[9px] font-bold text-amber-400 block uppercase mb-1">
                    EVALUATED ALTERNATIVE
                  </span>
                  <div className="space-y-0.5 text-[11px]">
                    <div>Rem. ETA: <span className="font-bold text-white">{altRemainingEta.toFixed(1)}h</span></div>
                    <div>Rem. Fuel: <span className="font-bold text-white">{altRemainingFuel.toFixed(1)} MT</span></div>
                    <div>Safety: <span className="font-bold text-amber-400">{altSafetyScore.toFixed(1)}</span></div>
                  </div>
                </div>
              </div>

              {/* Action Buttons: View Alternative & Take This Route */}
              <div className="flex gap-2 pt-1">
                <button
                  onClick={onToggleViewAlternative}
                  className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all border ${
                    viewingAlternative
                      ? 'bg-amber-500/20 text-amber-400 border-amber-500/50'
                      : 'bg-[#0A1B29] text-slate-300 border-[#1D3A4C] hover:text-white'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>{viewingAlternative ? 'Hide Alternative' : 'View Alternative'}</span>
                </button>

                <button
                  onClick={onAcceptAlternative}
                  className="flex-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 transition-colors shadow-md"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Take This Route</span>
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-[#06131F] p-4 rounded-lg border border-[#1D3A4C] text-xs text-slate-400 italic text-center">
          No disruption detected ahead. Vessel is sailing smoothly on the optimal route. Use buttons above to inject realistic disruptions.
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import { History, ChevronDown, ChevronUp, AlertTriangle, ShieldCheck, PlayCircle, CheckCircle2 } from 'lucide-react';
import type { VoyageLogEntry } from '../../hooks/useVoyageSimulation';

interface SimulationEventLogProps {
  eventLog: VoyageLogEntry[];
}

export const SimulationEventLog: React.FC<SimulationEventLogProps> = ({ eventLog }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getLogIcon = (type: VoyageLogEntry['type']) => {
    switch (type) {
      case 'disruption': return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'decision': return <ShieldCheck className="w-4 h-4 text-cyan-400" />;
      case 'override': return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'info':
      default: return <PlayCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="bg-[#0A1B29] border border-[#1D3A4C] rounded-xl p-4 space-y-3 shadow-xl text-slate-200">
      <div className="flex items-center justify-between border-b border-[#1D3A4C] pb-2">
        <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-1.5">
          <History className="w-4 h-4 text-cyan-400" />
          Dedicated Voyage Event Log
        </h3>
        <span className="text-[10px] bg-[#06131F] text-cyan-400 px-2 py-0.5 rounded border border-[#1D3A4C] font-mono">
          {eventLog.length} LOGS
        </span>
      </div>

      <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
        {eventLog.length === 0 ? (
          <div className="text-xs text-slate-500 italic text-center py-4">
            No voyage events recorded yet.
          </div>
        ) : (
          eventLog.map((log) => {
            const isExpanded = expandedId === log.id;
            const res = log.result;

            return (
              <div
                key={log.id}
                onClick={() => setExpandedId(isExpanded ? null : log.id)}
                className="bg-[#06131F] border border-[#1D3A4C] rounded-lg p-2.5 space-y-1.5 cursor-pointer hover:border-cyan-500/40 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    {getLogIcon(log.type)}
                    <span className="font-bold text-xs text-white truncate">
                      {log.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-[10px] text-slate-400 font-mono">
                      {log.timestamp}
                    </span>
                    {log.result && (
                      isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                </div>

                <p className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed">
                  {log.description}
                </p>

                {/* Expanded Decision Analysis Details */}
                {isExpanded && res && (
                  <div className="pt-2 border-t border-[#1D3A4C] space-y-2 text-[10px] font-mono">
                    <div className="grid grid-cols-3 gap-1 bg-[#0A1B29] p-2 rounded text-center">
                      <div>
                        <span className="text-slate-400 block">ETA BEFORE → AFTER</span>
                        <span className="font-bold text-white">{res.eta_before?.toFixed(1)}h → {res.eta_after?.toFixed(1)}h</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">FUEL BEFORE → AFTER</span>
                        <span className="font-bold text-white">{res.fuel_before?.toFixed(1)} → {res.fuel_after?.toFixed(1)} MT</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">SAFETY SCORE</span>
                        <span className="font-bold text-emerald-400">{res.safety_before?.toFixed(1)} → {res.safety_after?.toFixed(1)}</span>
                      </div>
                    </div>

                    <div className="bg-[#0A1B29] p-2 rounded text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {res.reason}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

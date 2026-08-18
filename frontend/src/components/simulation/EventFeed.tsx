import React, { useState, useEffect, useRef } from 'react';
import { FeedEvent, SimulationResponse } from '../../types/maritime';
import { Route, AlertTriangle, Info, AlertCircle, ShieldAlert, Anchor, Wind, Clock, Fuel, Shield, X, Trash2, ChevronRight } from 'lucide-react';

interface EventFeedProps {
  events: FeedEvent[];
  onClearEvents?: () => void;
}

export const EventFeed: React.FC<EventFeedProps> = ({ events, onClearEvents }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [selectedEvent, setSelectedEvent] = useState<FeedEvent | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = 0; // Newest items on the left
    }
  }, [events]);

  const getEventIcon = (event: FeedEvent) => {
    const res = event.simulation_result;
    if (res) {
      if (res.decision === 'REROUTE') return <AlertCircle className="w-4 h-4 text-red-400" />;
      if (res.decision === 'PORT_CONGESTION_UPDATED') return <Anchor className="w-4 h-4 text-amber-400" />;
      if (res.decision === 'ROUTE_RETAINED') return <ShieldAlert className="w-4 h-4 text-cyan-400" />;
      if (res.decision === 'SPATIALLY_IRRELEVANT') return <Wind className="w-4 h-4 text-slate-400" />;
      if (res.decision === 'EVENT_BEHIND_VESSEL') return <Clock className="w-4 h-4 text-slate-400" />;
    }
    switch (event.type) {
      case 'route_calculated': return <Route className="w-4 h-4 text-cyan-400" />;
      case 'simulation_event': return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'reroute': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'info':
      default: return <Info className="w-4 h-4 text-slate-400" />;
    }
  };

  const getDecisionBadge = (res?: SimulationResponse) => {
    if (!res || !res.decision) return null;
    let colorClass = 'bg-slate-700/60 text-slate-300 border-slate-600';
    let label = res.decision;

    if (res.decision === 'REROUTE') {
      colorClass = 'bg-red-500/20 text-red-400 border-red-500/50';
      label = '🚢 REROUTED';
    } else if (res.decision === 'PORT_CONGESTION_UPDATED') {
      colorClass = 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      label = '⚓ CONGESTION';
    } else if (res.decision === 'ROUTE_RETAINED') {
      colorClass = 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50';
      label = '🛡 ROUTE RETAINED';
    } else if (res.decision === 'SPATIALLY_IRRELEVANT') {
      colorClass = 'bg-slate-800/80 text-slate-400 border-slate-700';
      label = '○ IRRELEVANT';
    } else if (res.decision === 'EVENT_BEHIND_VESSEL') {
      colorClass = 'bg-slate-800/80 text-slate-400 border-slate-700';
      label = '⏳ BEHIND VESSEL';
    }

    return (
      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border tracking-wider uppercase ${colorClass}`}>
        {label}
      </span>
    );
  };

  const getFormattedTime = (timestamp: Date) => {
    const d = new Date(timestamp);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <>
      {/* Simulation Timeline Container (Max height 160px) */}
      <div className="h-[160px] w-full bg-[#06131F]/95 border-t border-[#1D3A4C] flex flex-col px-4 py-2 overflow-hidden z-40">
        
        {/* Timeline Header Bar */}
        <div className="flex items-center justify-between mb-2 px-1 flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-widest flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              SIMULATION TIMELINE
            </span>
            <span className="px-1.5 py-0.5 bg-[#0D2436] text-[#00F0FF] border border-[#1D3A4C] text-[10px] font-bold rounded">
              {events.length} EVENTS
            </span>
          </div>

          {onClearEvents && events.length > 0 && (
            <button
              onClick={onClearEvents}
              className="text-[10px] text-slate-400 hover:text-red-400 flex items-center gap-1 transition-colors px-2 py-0.5 rounded bg-[#0A1B29] border border-[#1D3A4C]"
            >
              <Trash2 className="w-3 h-3" />
              <span>Clear Log</span>
            </button>
          )}
        </div>

        {/* Compact Cards Horizontal Carousel */}
        <div 
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto h-full items-center custom-scrollbar w-full pb-1"
          style={{ scrollBehavior: 'smooth' }}
        >
          {events.length === 0 ? (
            <div className="text-xs text-slate-500 italic flex w-full justify-center py-4">
              No simulation events recorded
            </div>
          ) : (
            events.map((event, idx) => {
              const res = event.simulation_result;
              const hasImpact = res && (res.eta_change_hours !== 0 || res.fuel_change_mt !== 0 || res.safety_change !== 0);

              return (
                <div 
                  key={event.id} 
                  onClick={() => setSelectedEvent(event)}
                  className={`bg-[#0A1B29]/90 backdrop-blur-md min-w-[270px] max-w-[290px] h-[115px] p-2.5 flex flex-col justify-between flex-shrink-0 border rounded-lg cursor-pointer transition-all hover:border-cyan-500/60 hover:bg-[#0D2436] ${
                    idx === 0 
                      ? 'border-cyan-400/80 shadow-md shadow-cyan-950/40 ring-1 ring-cyan-500/30' 
                      : 'border-[#1D3A4C]'
                  }`}
                >
                  {/* Primary Row: Title, Decision Badge, Time */}
                  <div className="flex items-center justify-between gap-1">
                    <div className="flex items-center gap-1.5 min-w-0">
                      {getEventIcon(event)}
                      <span className="font-bold text-[11px] text-white truncate" title={event.title}>
                        {event.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {getDecisionBadge(res)}
                      <span className="text-[9px] text-slate-400 font-mono">
                        {getFormattedTime(event.timestamp)}
                      </span>
                    </div>
                  </div>

                  {/* Secondary Row: Causal Deltas or NO MEASURABLE IMPACT */}
                  {res ? (
                    hasImpact ? (
                      <div className="bg-[#06131F] px-2 py-1 rounded border border-[#1D3A4C] text-[10px] font-mono grid grid-cols-2 gap-x-2 gap-y-0.5 text-slate-300">
                        <div>
                          ETA: <span className="text-slate-400">{res.eta_before?.toFixed(1)}→</span>
                          <span className="text-white font-bold">{res.eta_after?.toFixed(1)}h</span>
                          {res.eta_change_hours > 0 && <span className="text-amber-400 font-bold ml-1">+{res.eta_change_hours.toFixed(1)}h</span>}
                        </div>
                        <div>
                          FUEL: <span className="text-slate-400">{res.fuel_before?.toFixed(1)}→</span>
                          <span className="text-white font-bold">{res.fuel_after?.toFixed(1)}MT</span>
                          {res.fuel_change_mt > 0 && <span className="text-amber-400 font-bold ml-1">+{res.fuel_change_mt.toFixed(1)}</span>}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-[#06131F] px-2 py-1 rounded border border-[#1D3A4C] text-[10px] font-mono text-slate-400 flex items-center justify-between">
                        <span className="font-bold tracking-wider text-slate-300 uppercase text-[9px]">NO MEASURABLE IMPACT</span>
                        <span className="text-[9px] text-slate-500">Δ 0.0</span>
                      </div>
                    )
                  ) : (
                    <div className="bg-[#06131F] px-2 py-1 rounded border border-[#1D3A4C] text-[10px] text-slate-400 truncate">
                      {event.description}
                    </div>
                  )}

                  {/* Tertiary Row: Short Reason Excerpt */}
                  <div className="flex items-center justify-between text-[9px] text-slate-400 truncate">
                    <span className="truncate pr-1 text-slate-300" title={res?.reason || event.description}>
                      {res?.reason ? res.reason.substring(0, 55) + '...' : event.description}
                    </span>
                    <span className="text-cyan-400 font-medium flex items-center flex-shrink-0 hover:underline">
                      Log <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Decision Analysis Log Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#0A1B29] border border-[#1D3A4C] rounded-xl max-w-xl w-full max-h-[85vh] overflow-y-auto p-6 shadow-2xl text-slate-200 relative">
            <button 
              onClick={() => setSelectedEvent(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4 border-b border-[#1D3A4C] pb-3">
              {getEventIcon(selectedEvent)}
              <div>
                <h2 className="text-base font-bold text-white">{selectedEvent.title}</h2>
                <div className="text-xs text-slate-400 font-mono">
                  Time: {getFormattedTime(selectedEvent.timestamp)} | ID: {selectedEvent.id}
                </div>
              </div>
            </div>

            {selectedEvent.simulation_result ? (
              <div className="space-y-4 text-xs">
                {/* Decision Header */}
                <div className="flex items-center justify-between bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C]">
                  <span className="text-slate-400 font-medium">Decision Status</span>
                  {getDecisionBadge(selectedEvent.simulation_result)}
                </div>

                {/* Causal Metrics Breakdown Table */}
                <div className="space-y-2">
                  <h3 className="font-semibold text-cyan-400 uppercase text-[10px] tracking-wider">Authoritative Metric Impact</h3>
                  <div className="grid grid-cols-3 gap-2 bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C] text-center font-mono">
                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px]">ETA (Hours)</span>
                      <span className="font-bold text-white mt-1">
                        {selectedEvent.simulation_result.eta_before?.toFixed(1) || '--'} → {selectedEvent.simulation_result.eta_after?.toFixed(1) || '--'}
                      </span>
                      <span className="text-[10px] font-semibold text-amber-400 mt-0.5">
                        Δ: {selectedEvent.simulation_result.eta_change_hours > 0 ? '+' : ''}{selectedEvent.simulation_result.eta_change_hours.toFixed(1)}h
                      </span>
                    </div>

                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px]">Fuel (MT)</span>
                      <span className="font-bold text-white mt-1">
                        {selectedEvent.simulation_result.fuel_before?.toFixed(1) || '--'} → {selectedEvent.simulation_result.fuel_after?.toFixed(1) || '--'}
                      </span>
                      <span className="text-[10px] font-semibold text-amber-400 mt-0.5">
                        Δ: {selectedEvent.simulation_result.fuel_change_mt > 0 ? '+' : ''}{selectedEvent.simulation_result.fuel_change_mt.toFixed(1)} MT
                      </span>
                    </div>

                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px]">Safety Score</span>
                      <span className="font-bold text-white mt-1">
                        {selectedEvent.simulation_result.safety_before?.toFixed(1) || '--'} → {selectedEvent.simulation_result.safety_after?.toFixed(1) || '--'}
                      </span>
                      <span className="text-[10px] font-semibold text-emerald-400 mt-0.5">
                        Δ: {selectedEvent.simulation_result.safety_change.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Hysteresis & Cost Tradeoff */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C]">
                    <div className="text-slate-400 text-[10px]">Alternate Route Cost Improvement</div>
                    <div className="text-sm font-bold text-cyan-400 mt-1 font-mono">
                      {selectedEvent.simulation_result.cost_improvement_percent?.toFixed(1) || '0.0'}%
                    </div>
                  </div>

                  <div className="bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C]">
                    <div className="text-slate-400 text-[10px]">Configured Hysteresis Threshold</div>
                    <div className="text-sm font-bold text-amber-400 mt-1 font-mono">
                      {selectedEvent.simulation_result.hysteresis_threshold_percent?.toFixed(1) || '5.0'}%
                    </div>
                  </div>
                </div>

                {/* Full Rationale String */}
                <div className="space-y-1">
                  <h3 className="font-semibold text-cyan-400 uppercase text-[10px] tracking-wider">Authoritative Backend Rationale</h3>
                  <div className="bg-[#06131F] p-3 rounded-lg border border-[#1D3A4C] font-mono text-[11px] text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {selectedEvent.simulation_result.reason}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-[#06131F] p-4 rounded-lg border border-[#1D3A4C] text-slate-300 leading-relaxed">
                {selectedEvent.description}
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-lg transition-colors"
              >
                Close Log Analysis
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

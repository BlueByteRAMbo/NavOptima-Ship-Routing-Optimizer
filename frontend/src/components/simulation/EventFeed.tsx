import React, { useEffect, useRef } from 'react';
import { FeedEvent } from '../../types/maritime';
import { Route, AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface EventFeedProps {
  events: FeedEvent[];
}

export const EventFeed: React.FC<EventFeedProps> = ({ events }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = 0; // The newest items are on the left
    }
  }, [events]);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'route_calculated': return <Route className="w-5 h-5 text-maritime-cyan" />;
      case 'simulation_event': return <AlertTriangle className="w-5 h-5 text-maritime-warning" />;
      case 'reroute': return <AlertCircle className="w-5 h-5 text-maritime-danger" />;
      case 'info':
      default: return <Info className="w-5 h-5 text-maritime-muted" />;
    }
  };

  const getRelativeTime = (timestamp: Date) => {
    const diff = Math.floor((new Date().getTime() - timestamp.getTime()) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return 'older';
  };

  return (
    <div className="h-[100px] w-full bg-maritime-panel-secondary border-t border-maritime-border flex items-center px-4 overflow-hidden z-40">
      <div 
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto h-full items-center custom-scrollbar w-full"
        style={{ scrollBehavior: 'smooth' }}
      >
        {events.length === 0 ? (
          <div className="text-sm text-maritime-muted-dim italic flex w-full justify-center">
            No events recorded
          </div>
        ) : (
          events.map((event, idx) => (
            <div 
              key={event.id} 
              className={`glass-panel min-w-[300px] max-w-[300px] p-3 flex gap-3 flex-shrink-0 border-l-2 ${
                event.type === 'route_calculated' ? 'border-l-maritime-cyan' :
                event.type === 'simulation_event' ? 'border-l-maritime-warning' :
                event.type === 'reroute' ? 'border-l-maritime-danger' : 'border-l-maritime-muted'
              } ${idx === 0 ? 'animate-slide-right' : ''}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getEventIcon(event.type)}
              </div>
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex justify-between items-start">
                  <span className="font-title text-sm font-semibold text-white truncate pr-2" title={event.title}>
                    {event.title}
                  </span>
                  <span className="text-[10px] text-maritime-muted flex-shrink-0">
                    {getRelativeTime(event.timestamp)}
                  </span>
                </div>
                <p 
                  className="text-xs text-maritime-muted-dim truncate" 
                  title={event.description}
                >
                  {event.description}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

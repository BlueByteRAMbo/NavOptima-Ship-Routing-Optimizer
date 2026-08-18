import React, { useState } from 'react';
import { DataSource } from '../../types/maritime';
import { Database, ChevronDown, ChevronUp } from 'lucide-react';

interface DataSourcesPanelProps {
  sources: DataSource[];
}

const DataSourcesPanel: React.FC<DataSourcesPanelProps> = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="flex flex-col">
      <div 
        className="flex items-center justify-between cursor-pointer p-2 rounded hover:bg-maritime-panel-secondary transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-maritime-cyan" />
          <h3 className="section-label mb-0 text-maritime-muted uppercase text-xs font-bold tracking-wider">Data Sources</h3>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-maritime-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-maritime-muted" />
        )}
      </div>

      {expanded && (
        <div className="mt-3 space-y-3 px-2">
          {sources.map((source, idx) => (
            <div key={idx} className="flex flex-col bg-maritime-panel-secondary p-2 rounded border border-maritime-border text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-white">{source.source}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  source.status === 'LIVE' ? 'bg-maritime-success/20 text-maritime-success' : 
                  source.status === 'CACHED' ? 'bg-maritime-cyan/20 text-maritime-cyan' :
                  source.status === 'MOCK' ? 'bg-maritime-warning/20 text-maritime-warning' : 
                  'bg-maritime-danger/20 text-maritime-danger'
                }`}>
                  {source.status}
                </span>
              </div>
              <div className="text-maritime-muted mb-1">
                Dataset: <span className="text-maritime-cyan-dim">{source.dataset}</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-1">
                {source.variables.map((v, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-maritime-panel text-[10px] text-maritime-muted rounded border border-maritime-border">
                    {v}
                  </span>
                ))}
              </div>
              {source.note && (
                <div className="mt-2 text-[10px] text-maritime-muted-dim italic">
                  {source.note}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DataSourcesPanel;

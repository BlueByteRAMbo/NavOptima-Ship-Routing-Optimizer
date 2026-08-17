import React from 'react';
import { RouteResponse, SimulationResponse, Port, EnvironmentCell, DataSource } from '../../types/maritime';
import RouteStats from './RouteStats';
import RouteComparison from './RouteComparison';
import PortCongestionChart from './PortCongestionChart';
import WeatherSummary from './WeatherSummary';
import DataSourcesPanel from './DataSourcesPanel';

interface AnalyticsPanelProps {
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
  simulationResult: SimulationResponse | null;
  ports: Port[];
  environment: EnvironmentCell[];
  dataSources: DataSource[];
}

const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({
  currentRoute,
  previousRoute,
  simulationResult,
  ports,
  environment,
  dataSources
}) => {
  return (
    <div className="h-full flex flex-col bg-maritime-panel overflow-y-auto border-l border-maritime-border text-maritime-muted-dim p-4 space-y-6">
      
      {currentRoute ? (
        <>
          <section>
            <h3 className="section-label mb-3 text-maritime-muted uppercase text-xs font-bold tracking-wider">Route Stats</h3>
            <RouteStats route={currentRoute} />
          </section>

          {simulationResult && previousRoute && (
            <>
              <div className="divider my-2 border-t border-maritime-border"></div>
              <section>
                <h3 className="section-label mb-3 text-maritime-muted uppercase text-xs font-bold tracking-wider">Route Comparison</h3>
                <RouteComparison 
                  simulationResult={simulationResult} 
                  currentRoute={currentRoute} 
                  previousRoute={previousRoute} 
                />
              </section>
            </>
          )}

          <div className="divider my-2 border-t border-maritime-border"></div>
          <section>
            <h3 className="section-label mb-3 text-maritime-muted uppercase text-xs font-bold tracking-wider">Weather Summary</h3>
            <WeatherSummary environment={environment} route={currentRoute} />
          </section>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center text-maritime-muted">
          Select a vessel or calculate a route to view analytics.
        </div>
      )}

      <div className="divider my-2 border-t border-maritime-border"></div>
      <section>
        <h3 className="section-label mb-3 text-maritime-muted uppercase text-xs font-bold tracking-wider">Port Congestion</h3>
        <PortCongestionChart ports={ports} />
      </section>

      <div className="divider my-2 border-t border-maritime-border"></div>
      <section>
        <DataSourcesPanel sources={dataSources} />
      </section>
      
    </div>
  );
};

export default AnalyticsPanel;

import React from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import { RouteResponse, Port, EnvironmentCell, SimulationEvent } from '../../types/maritime';
import RouteLayer from './RouteLayer';
import PortLayer from './PortLayer';
import WeatherLayer from './WeatherLayer';
import RiskLayer from './RiskLayer';
import 'leaflet/dist/leaflet.css';

interface MaritimeMapProps {
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
  ports: Port[];
  environment: EnvironmentCell[];
  activeSimulation: SimulationEvent | null;
  riskZones: SimulationEvent[];
  showWeatherLayer: boolean;
  showRiskLayer: boolean;
}

const MaritimeMap: React.FC<MaritimeMapProps> = ({
  currentRoute,
  previousRoute,
  ports,
  environment,
  activeSimulation,
  riskZones,
  showWeatherLayer,
  showRiskLayer
}) => {
  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={[8, 72]}
        zoom={4}
        className="w-full h-full z-0"
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
        />
        
        <RouteLayer currentRoute={currentRoute} previousRoute={previousRoute} />
        <PortLayer ports={ports} />
        <WeatherLayer cells={environment} visible={showWeatherLayer} />
        <RiskLayer riskZones={riskZones} activeSimulation={activeSimulation} visible={showRiskLayer} />
      </MapContainer>

      {/* Legend overlay */}
      <div className="absolute bottom-4 left-4 z-[400] glass-panel-solid p-3 text-xs flex flex-col gap-2 rounded border border-maritime-border bg-maritime-panel shadow-glow">
        <div className="font-semibold text-maritime-muted mb-1 uppercase tracking-wider">Legend</div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-maritime-cyan"></div>
          <span className="text-gray-300">Active Route</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 border-t border-dashed border-maritime-cyan-dim"></div>
          <span className="text-gray-300">Previous Route</span>
        </div>
      </div>
    </div>
  );
};

export default MaritimeMap;

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { RouteResponse, Port, EnvironmentCell, SimulationEvent, VoyageStateResponse, SimulationResponse } from '../../types/maritime';
import RouteLayer from './RouteLayer';
import PortLayer from './PortLayer';
import WeatherLayer from './WeatherLayer';
import RiskLayer from './RiskLayer';
import { CanvasOceanCurrents } from './CanvasOceanCurrents';
import { OnMapDecisionOverlay } from '../simulation/OnMapDecisionOverlay';
import 'leaflet/dist/leaflet.css';

interface MaritimeMapProps {
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
  activeVoyage?: VoyageStateResponse | null;
  ports: Port[];
  environment: EnvironmentCell[];
  activeSimulation: SimulationEvent | null;
  riskZones: SimulationEvent[];
  showWeatherLayer: boolean;
  showRiskLayer: boolean;
  showOceanCurrents: boolean;
  focusCoords?: [number, number] | null;
  activeDisruption?: SimulationResponse | null;
  alternativeRoute?: RouteResponse | null;
  onAcceptAlternative?: () => void;
  onKeepCurrent?: () => void;
  onFocusMap?: (lat: number, lon: number) => void;
  onResetView?: () => void;
}

const MapFocusHandler: React.FC<{ focusCoords?: [number, number] | null }> = ({ focusCoords }) => {
  const map = useMap();
  useEffect(() => {
    if (focusCoords && focusCoords[0] && focusCoords[1]) {
      map.flyTo(focusCoords, 6, { duration: 1.2 });
    }
  }, [focusCoords, map]);
  return null;
};

const MaritimeMap: React.FC<MaritimeMapProps> = ({
  currentRoute,
  previousRoute,
  activeVoyage,
  ports,
  environment,
  activeSimulation,
  riskZones,
  showWeatherLayer,
  showRiskLayer,
  showOceanCurrents,
  focusCoords,
  activeDisruption,
  alternativeRoute,
  onAcceptAlternative,
  onKeepCurrent,
  onFocusMap,
  onResetView,
}) => {
  return (
    <div className="relative w-full h-full">
      {/* On-Map Disruption Decision Overlay Modal */}
      {activeDisruption && onAcceptAlternative && onKeepCurrent && (
        <OnMapDecisionOverlay
          activeDisruption={activeDisruption}
          alternativeRoute={alternativeRoute || null}
          currentRoute={currentRoute}
          activeVoyage={activeVoyage || null}
          onAcceptAlternative={onAcceptAlternative}
          onKeepCurrent={onKeepCurrent}
          onFocusMap={onFocusMap}
          onResetView={onResetView}
        />
      )}

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
        
        <MapFocusHandler focusCoords={focusCoords} />
        <CanvasOceanCurrents environment={environment} visible={showOceanCurrents} />
        <RouteLayer currentRoute={currentRoute} previousRoute={previousRoute} activeVoyage={activeVoyage} />
        <PortLayer ports={ports} />
        <WeatherLayer cells={environment} visible={showWeatherLayer} />
        <RiskLayer riskZones={riskZones} activeSimulation={activeSimulation} visible={showRiskLayer} />
      </MapContainer>

      {/* Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-[400] p-3 text-xs flex flex-col gap-1.5 rounded-xl border border-[#1D3A4C] bg-[#0A1B29]/90 backdrop-blur-md shadow-2xl">
        <div className="font-semibold text-slate-400 mb-1 uppercase tracking-wider text-[10px]">Route & Congestion</div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 rounded" style={{ background: '#00F0FF' }}></div>
          <span className="text-slate-200">Active Route — Low</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 rounded" style={{ background: '#F59E0B' }}></div>
          <span className="text-amber-400">Moderate Congestion</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-1 rounded" style={{ background: '#EF4444' }}></div>
          <span className="text-red-400">High Congestion</span>
        </div>
        <div className="flex items-center gap-2 border-t border-[#1D3A4C] pt-1 mt-0.5">
          <div className="w-4 h-0.5 border-t border-dashed border-slate-400"></div>
          <span className="text-slate-400">Travelled Trail</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 border-t border-dashed border-amber-400"></div>
          <span className="text-amber-400">Alternative Route</span>
        </div>
      </div>
    </div>
  );
};

export default MaritimeMap;

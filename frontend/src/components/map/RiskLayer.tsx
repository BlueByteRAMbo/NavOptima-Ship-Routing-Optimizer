import React from 'react';
import { Circle, Tooltip } from 'react-leaflet';
import { SimulationEvent } from '../../types/maritime';

interface RiskLayerProps {
  riskZones: SimulationEvent[];
  activeSimulation: SimulationEvent | null;
  visible: boolean;
}

const RiskLayer: React.FC<RiskLayerProps> = ({ riskZones, activeSimulation, visible }) => {
  if (!visible) return null;

  return (
    <>
      {riskZones.map((zone) => {
        const isSecurity = zone.type === 'security';
        const color = isSecurity ? '#FF4D5E' : '#F5A623';
        const opacity = Math.max(0.1, Math.min(0.3, zone.severity / 10));
        const isActive = activeSimulation?.type === zone.type;
        
        return (
          <Circle
            key={`${zone.type}-${zone.lat}-${zone.lon}`}
            center={[zone.lat, zone.lon]}
            radius={zone.radius_km * 1000}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: isActive ? opacity + 0.2 : opacity,
              weight: isActive ? 3 : 1,
              className: !isSecurity && isActive ? 'animate-pulse storm-zone' : ''
            }}
          >
            <Tooltip>
              <div className="font-semibold text-white">
                {zone.type === 'security' ? 'Security Risk' : 'Storm Zone'}
              </div>
              <div className="text-gray-300 text-sm">Severity: {zone.severity.toFixed(1)}/10</div>
            </Tooltip>
          </Circle>
        );
      })}
    </>
  );
};

export default RiskLayer;

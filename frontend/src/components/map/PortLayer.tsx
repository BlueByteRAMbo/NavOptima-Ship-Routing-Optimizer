import React from 'react';
import { CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { Port } from '../../types/maritime';

interface PortLayerProps {
  ports: Port[];
}

const PortLayer: React.FC<PortLayerProps> = ({ ports }) => {
  const getPortColor = (congestion: number) => {
    if (congestion < 0.4) return '#28D7A0'; // maritime-success
    if (congestion <= 0.7) return '#F5A623'; // maritime-warning
    return '#FF4D5E'; // maritime-danger
  };

  return (
    <>
      {ports.map((port) => {
        const color = getPortColor(port.congestion);
        
        return (
          <CircleMarker
            key={port.id}
            center={[port.lat, port.lon]}
            radius={6}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.8,
              weight: 2
            }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
              <span className="font-semibold">{port.name}</span>
            </Tooltip>
            
            <Popup className="maritime-popup">
              <div className="p-1 min-w-[200px]">
                <h4 className="font-bold text-base mb-1 text-white">{port.name}</h4>
                <p className="text-maritime-muted text-xs mb-3">{port.country}</p>
                
                <div className="space-y-2 text-sm text-gray-300">
                  <div className="flex justify-between">
                    <span>Congestion:</span>
                    <span style={{ color }}>{(port.congestion * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Waiting:</span>
                    <span>{port.waiting_hours}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Utilization:</span>
                    <span>{(port.utilization * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
};

export default PortLayer;

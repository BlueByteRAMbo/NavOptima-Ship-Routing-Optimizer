import React from 'react';
import { Marker, Circle } from 'react-leaflet';
import L from 'leaflet';
import { EnvironmentCell } from '../../types/maritime';

interface WeatherLayerProps {
  cells: EnvironmentCell[];
  visible: boolean;
}

const WeatherLayer: React.FC<WeatherLayerProps> = ({ cells, visible }) => {
  if (!visible) return null;

  const getWindColor = (speed: number) => {
    if (speed < 15) return '#28D7A0';
    if (speed < 30) return '#F5A623';
    return '#FF4D5E';
  };

  return (
    <>
      {cells.map((cell, index) => {
        const color = getWindColor(cell.wind_speed);
        
        const arrowIcon = L.divIcon({
          className: 'wind-arrow-icon',
          html: `<div style="transform: rotate(${cell.wind_direction}deg); color: ${color}; opacity: 0.7; font-size: 14px; font-weight: bold; text-shadow: 0 0 2px rgba(0,0,0,0.5);">↑</div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });

        return (
          <React.Fragment key={`env-${index}`}>
            {/* Wave height indicator */}
            <Circle
              center={[cell.lat, cell.lon]}
              radius={cell.wave_height * 5000} // Scale factor for visualization
              pathOptions={{
                color: '#4A6274',
                fillColor: '#4A6274',
                fillOpacity: 0.2,
                weight: 1
              }}
            />
            {/* Wind direction indicator */}
            <Marker position={[cell.lat, cell.lon]} icon={arrowIcon} />
          </React.Fragment>
        );
      })}
    </>
  );
};

export default WeatherLayer;

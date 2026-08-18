import React, { useMemo } from 'react';
import { Marker } from 'react-leaflet';
import L from 'leaflet';
import { EnvironmentCell } from '../../types/maritime';

interface WeatherLayerProps {
  cells: EnvironmentCell[];
  visible: boolean;
}

const WeatherLayer: React.FC<WeatherLayerProps> = ({ cells, visible }) => {
  // Spatial downsampling to ensure at most ~300 visual markers rendered for maximum 60 FPS performance
  const sampledCells = useMemo(() => {
    if (!visible || !cells || cells.length === 0) return [];
    
    // Target maximum ~300 visible weather vector arrows on map
    const TARGET_MAX_VECTORS = 300;
    if (cells.length <= TARGET_MAX_VECTORS) return cells;

    const step = Math.ceil(cells.length / TARGET_MAX_VECTORS);
    return cells.filter((_, index) => index % step === 0);
  }, [cells, visible]);

  if (!visible || sampledCells.length === 0) return null;

  const getWindColor = (speed: number) => {
    if (speed < 15) return '#28D7A0';
    if (speed < 30) return '#F5A623';
    return '#FF4D5E';
  };

  return (
    <>
      {sampledCells.map((cell, index) => {
        const color = getWindColor(cell.wind_speed);
        
        // Single lightweight SVG arrow icon representing wind/current direction & magnitude
        const arrowIcon = L.divIcon({
          className: 'weather-vector-icon',
          html: `<div style="transform: rotate(${cell.wind_direction}deg); color: ${color}; opacity: 0.85; font-size: 13px; font-weight: bold; line-height: 1; text-shadow: 0 0 3px rgba(0,0,0,0.8);">↑</div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        });

        return (
          <Marker
            key={`weather-vec-${cell.lat}-${cell.lon}-${index}`}
            position={[cell.lat, cell.lon]}
            icon={arrowIcon}
          />
        );
      })}
    </>
  );
};

export default WeatherLayer;

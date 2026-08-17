import React, { useMemo } from 'react';
import { Polyline, CircleMarker, Marker } from 'react-leaflet';
import L from 'leaflet';
import { RouteResponse } from '../../types/maritime';

interface RouteLayerProps {
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
}

const shipIcon = L.divIcon({
  className: 'ship-marker',
  html: `<div class="w-4 h-4 bg-maritime-cyan" style="clip-path: polygon(50% 0%, 0% 100%, 100% 100%);"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

const RouteLayer: React.FC<RouteLayerProps> = ({ currentRoute, previousRoute }) => {
  const previousPositions = useMemo(() => {
    if (!previousRoute) return [];
    return previousRoute.coordinates;
  }, [previousRoute]);

  const currentPositions = useMemo(() => {
    if (!currentRoute) return [];
    return currentRoute.coordinates;
  }, [currentRoute]);

  const shipPosition = useMemo(() => {
    if (currentPositions.length < 2) return null;
    const midIndex = Math.floor(currentPositions.length / 2);
    return currentPositions[midIndex];
  }, [currentPositions]);

  return (
    <>
      {previousRoute && (
        <Polyline
          positions={previousPositions}
          pathOptions={{
            color: '#0EA5B5',
            weight: 2,
            opacity: 0.5,
            dashArray: '10, 8'
          }}
        />
      )}
      
      {currentRoute && (
        <>
          <Polyline
            positions={currentPositions}
            pathOptions={{
              color: '#20E5F5',
              weight: 3,
              opacity: 0.9
            }}
          />
          
          {/* Start marker */}
          {currentPositions.length > 0 && (
            <CircleMarker
              center={currentPositions[0]}
              radius={4}
              pathOptions={{ color: '#20E5F5', fillColor: '#20E5F5', fillOpacity: 1 }}
              className="animate-glow-pulse"
            />
          )}

          {/* End marker */}
          {currentPositions.length > 1 && (
            <CircleMarker
              center={currentPositions[currentPositions.length - 1]}
              radius={4}
              pathOptions={{ color: '#20E5F5', fillColor: '#20E5F5', fillOpacity: 1 }}
              className="animate-glow-pulse"
            />
          )}

          {/* Ship indicator */}
          {shipPosition && (
            <Marker position={shipPosition} icon={shipIcon} />
          )}
        </>
      )}
    </>
  );
};

export default RouteLayer;

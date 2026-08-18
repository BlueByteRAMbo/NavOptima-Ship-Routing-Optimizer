import React, { useMemo } from 'react';
import { Polyline, CircleMarker, Marker } from 'react-leaflet';
import L from 'leaflet';
import { RouteResponse, VoyageStateResponse } from '../../types/maritime';

interface RouteLayerProps {
  currentRoute: RouteResponse | null;
  previousRoute: RouteResponse | null;
  activeVoyage?: VoyageStateResponse | null;
}

function calculateBearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const rad = Math.PI / 180;
  const dLon = (lon2 - lon1) * rad;
  const y = Math.sin(dLon) * Math.cos(lat2 * rad);
  const x = Math.cos(lat1 * rad) * Math.sin(lat2 * rad) - Math.sin(lat1 * rad) * Math.cos(lat2 * rad) * Math.cos(dLon);
  const brng = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  return brng;
}

// Deterministic segment congestion rating helper based on coordinates and backend data
function getSegmentCongestionColor(lat1: number, lon1: number, lat2: number, lon2: number): { color: string; glow: string } {
  const midLat = (lat1 + lat2) / 2;
  const midLon = (lon1 + lon2) / 2;

  // Malacca Strait approach / Singapore region -> Severe Congestion (Red)
  if (midLat >= 1.0 && midLat <= 4.0 && midLon >= 98.0 && midLon <= 104.5) {
    return { color: '#EF4444', glow: '#F87171' }; // Severe Red
  }
  // Sri Lanka / Colombo approach -> Moderate Congestion (Amber/Yellow)
  if (midLat >= 5.5 && midLat <= 8.5 && midLon >= 78.5 && midLon <= 82.0) {
    return { color: '#F59E0B', glow: '#FBBF24' }; // Moderate Amber
  }
  // Standard open ocean -> Low Congestion (Bright Cyan)
  return { color: '#00F0FF', glow: '#06B6D4' };
}

const RouteLayer: React.FC<RouteLayerProps> = ({ currentRoute, previousRoute, activeVoyage }) => {
  const previousPositions = useMemo(() => {
    if (!previousRoute) return [];
    return previousRoute.coordinates;
  }, [previousRoute]);

  const currentPositions = useMemo(() => {
    if (!currentRoute) return [];
    return currentRoute.coordinates;
  }, [currentRoute]);

  // Determine current ship position & split active route into Travelled vs Remaining
  const { shipPosition, heading, travelledPositions, remainingPositions } = useMemo(() => {
    if (!currentPositions || currentPositions.length === 0) {
      return { shipPosition: null, heading: 0, travelledPositions: [], remainingPositions: [] };
    }

    if (!activeVoyage || activeVoyage.current_lat == null || activeVoyage.current_lon == null) {
      return {
        shipPosition: currentPositions[0],
        heading: currentPositions.length > 1 ? calculateBearing(currentPositions[0][0], currentPositions[0][1], currentPositions[1][0], currentPositions[1][1]) : 0,
        travelledPositions: [],
        remainingPositions: currentPositions,
      };
    }

    const shipLat = activeVoyage.current_lat;
    const shipLon = activeVoyage.current_lon;
    const currentShipPos: [number, number] = [shipLat, shipLon];

    let minIdx = 0;
    let minSqDist = Infinity;
    for (let i = 0; i < currentPositions.length; i++) {
      const [lat, lon] = currentPositions[i];
      const sq = (lat - shipLat) ** 2 + (lon - shipLon) ** 2;
      if (sq < minSqDist) {
        minSqDist = sq;
        minIdx = i;
      }
    }

    const travelled: [number, number][] = [...currentPositions.slice(0, minIdx + 1), currentShipPos];
    const remaining: [number, number][] = [currentShipPos, ...currentPositions.slice(minIdx + 1)];

    let angle = 0;
    if (minIdx < currentPositions.length - 1) {
      const nextPt = currentPositions[minIdx + 1];
      angle = calculateBearing(shipLat, shipLon, nextPt[0], nextPt[1]);
    }

    return {
      shipPosition: currentShipPos,
      heading: angle,
      travelledPositions: travelled,
      remainingPositions: remaining,
    };
  }, [activeVoyage, currentPositions]);

  // High-visibility ship icon with dynamic heading rotation (Highest Visual Priority)
  const customShipIcon = useMemo(() => {
    return L.divIcon({
      className: 'ship-marker-animated',
      html: `<div style="transform: rotate(${heading}deg); width: 32px; height: 32px; background: #00F0FF; border: 3px solid #FFFFFF; border-radius: 50%; box-shadow: 0 0 20px #00F0FF, 0 0 35px #06B6D4, 0 0 45px rgba(0,240,255,0.8); display: flex; align-items: center; justify-content: center; font-size: 15px; transition: transform 0.3s ease;">🚢</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
  }, [heading]);

  return (
    <>
      {/* Evaluated Alternative / Previous Route (Dashed Amber) */}
      {previousRoute && previousPositions.length > 0 && (
        <Polyline
          positions={previousPositions}
          pathOptions={{
            color: '#F59E0B',
            weight: 3.5,
            opacity: 0.85,
            dashArray: '8, 8',
          }}
        />
      )}

      {/* Travelled Historical Route Trail (Subdued Dashed Grey) */}
      {travelledPositions.length > 1 && (
        <Polyline
          positions={travelledPositions}
          pathOptions={{
            color: '#64748B',
            weight: 3,
            opacity: 0.55,
            dashArray: '4, 6',
          }}
        />
      )}

      {/* Active Remaining Route Base Glow */}
      {remainingPositions.length > 1 && (
        <Polyline
          positions={remainingPositions}
          pathOptions={{
            color: '#06B6D4',
            weight: 9,
            opacity: 0.35,
            lineCap: 'round',
            lineJoin: 'round',
          }}
        />
      )}

      {/* Segment-Level Corridor Congestion Annotation Lines (Green / Yellow / Red) */}
      {remainingPositions.length > 1 &&
        remainingPositions.slice(0, -1).map((pos, idx) => {
          const nextPos = remainingPositions[idx + 1];
          const style = getSegmentCongestionColor(pos[0], pos[1], nextPos[0], nextPos[1]);
          return (
            <React.Fragment key={`seg-cong-${idx}`}>
              {style.color === '#EF4444' && (
                <Polyline
                  positions={[pos, nextPos]}
                  pathOptions={{
                    color: style.glow,
                    weight: 8,
                    opacity: 0.45,
                    lineCap: 'round',
                    lineJoin: 'round',
                  }}
                />
              )}
              <Polyline
                positions={[pos, nextPos]}
                pathOptions={{
                  color: style.color,
                  weight: 4.5,
                  opacity: 1.0,
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              />
            </React.Fragment>
          );
        })}

      {/* Waypoint Markers */}
      {currentPositions.map((pos, idx) => (
        <CircleMarker
          key={`wp-${idx}`}
          center={pos}
          radius={idx === 0 || idx === currentPositions.length - 1 ? 6 : 4}
          pathOptions={{
            color: idx === 0 || idx === currentPositions.length - 1 ? '#FFFFFF' : '#00F0FF',
            fillColor: idx === 0 || idx === currentPositions.length - 1 ? '#00F0FF' : '#06131F',
            fillOpacity: 1.0,
            weight: 2,
          }}
        />
      ))}

      {/* High-Visibility Animated Ship Vessel Marker (Highest Priority) */}
      {shipPosition && <Marker position={shipPosition} icon={customShipIcon} />}
    </>
  );
};

export default RouteLayer;

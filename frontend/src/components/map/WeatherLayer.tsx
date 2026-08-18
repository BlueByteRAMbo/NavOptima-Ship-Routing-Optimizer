import React, { useEffect, useRef, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { EnvironmentCell } from '../../types/maritime';
import {
  fetchOpenMeteoWindGrid,
  getInterpolatedWindVector,
  OpenMeteoWindGrid,
} from '../../services/openMeteoWindService';

interface WeatherLayerProps {
  cells: EnvironmentCell[];
  visible: boolean;
}

interface Particle {
  lat: number;
  lon: number;
  age: number;
  maxAge: number;
  trail: { x: number; y: number }[];
}

const MIN_LON = 40.0;
const MAX_LON = 110.0;
const MIN_LAT = -35.0;
const MAX_LAT = 30.0;
const MAX_TRAIL_LENGTH = 14;

const WeatherLayer: React.FC<WeatherLayerProps> = ({ cells, visible }) => {
  const map = useMap();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const [windGrid, setWindGrid] = useState<OpenMeteoWindGrid | null>(null);
  const [statusText, setStatusText] = useState<string>('Open-Meteo Loading...');

  // Fetch Open-Meteo wind forecast grid when Weather Layer is toggled ON
  useEffect(() => {
    if (!visible) {
      setWindGrid(null);
      return;
    }

    let isMounted = true;
    fetchOpenMeteoWindGrid()
      .then((grid) => {
        if (isMounted) {
          setWindGrid(grid);
          if (grid.status === 'live') {
            setStatusText(`Open-Meteo • ${grid.forecastTimeISO.substring(0, 16).replace('T', ' ')} UTC`);
          } else {
            setStatusText('Environment Grid (Fallback)');
          }
        }
      })
      .catch((err) => {
        console.warn('[WeatherLayer] Error loading Open-Meteo wind data:', err);
        if (isMounted) setStatusText('Environment Grid (Fallback)');
      });

    return () => {
      isMounted = false;
    };
  }, [visible]);

  // Spatial Wind Field Streamline & Particle Advection Loop
  useEffect(() => {
    if (!visible) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (canvasRef.current && canvasRef.current.parentNode) {
        canvasRef.current.parentNode.removeChild(canvasRef.current);
        canvasRef.current = null;
      }
      return;
    }

    // Create or select HTML5 canvas overlay pane
    let canvas = canvasRef.current;
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.style.position = 'absolute';
      canvas.style.top = '0';
      canvas.style.left = '0';
      canvas.style.pointerEvents = 'none';
      canvas.style.zIndex = '180'; // Subordinate to active route & vessel beacon
      canvas.style.opacity = '0.75';
      map.getPanes().overlayPane.appendChild(canvas);
      canvasRef.current = canvas;
    }

    const updateCanvasSize = () => {
      if (!canvas) return;
      const size = map.getSize();
      canvas.width = size.x;
      canvas.height = size.y;
      const topLeft = map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setPosition(canvas, topLeft);
    };

    updateCanvasSize();

    // Fallback spatial vector calculation from backend environment cells if Open-Meteo is offline
    const getFallbackVector = (lat: number, lon: number) => {
      let nearest: EnvironmentCell | null = null;
      let minSqDist = Infinity;
      for (let i = 0; i < cells.length; i++) {
        const c = cells[i];
        const dLat = c.lat - lat;
        const dLon = c.lon - lon;
        const sqDist = dLat * dLat + dLon * dLon;
        if (sqDist < minSqDist) {
          minSqDist = sqDist;
          nearest = c;
        }
      }
      if (nearest && minSqDist < 9.0) {
        const blowingTowardsDeg = (nearest.wind_direction + 180) % 360;
        const rad = blowingTowardsDeg * (Math.PI / 180);
        const speedKnots = nearest.wind_speed;
        return {
          u: speedKnots * Math.sin(rad),
          v: speedKnots * Math.cos(rad),
          speedKnots,
          directionDeg: nearest.wind_direction,
          forecastTimestamp: 'Environment Grid',
        };
      }
      return { u: 0, v: 0, speedKnots: 0, directionDeg: 0, forecastTimestamp: 'N/A' };
    };

    // Initialize 500 streamline advection particles across the Indian Ocean basin
    const particleCount = 500;
    const particles: Particle[] = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        lat: MIN_LAT + Math.random() * (MAX_LAT - MIN_LAT),
        lon: MIN_LON + Math.random() * (MAX_LON - MIN_LON),
        age: Math.floor(Math.random() * 60),
        maxAge: 45 + Math.floor(Math.random() * 50),
        trail: [],
      });
    }

    const ctx = canvas.getContext('2d');

    const renderFrame = () => {
      if (!ctx || !canvas) return;

      // Clear canvas with subtle semi-transparent fill to produce smooth streamline flow trails
      ctx.fillStyle = 'rgba(7, 26, 43, 0.16)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const zoom = map.getZoom();
      const speedScale = 0.035 * (8 / Math.max(1, zoom));
      const now = new Date();

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.age++;

        // Respawn particle if age limit reached or drifted out of Indian Ocean bounds
        if (p.age >= p.maxAge || p.lat < MIN_LAT || p.lat > MAX_LAT || p.lon < MIN_LON || p.lon > MAX_LON) {
          p.lat = MIN_LAT + Math.random() * (MAX_LAT - MIN_LAT);
          p.lon = MIN_LON + Math.random() * (MAX_LON - MIN_LON);
          p.age = 0;
          p.maxAge = 45 + Math.floor(Math.random() * 50);
          p.trail = [];
          continue;
        }

        // Get continuous spatially bilinear & time-interpolated wind vector
        const vec = windGrid && windGrid.points.length > 0
          ? getInterpolatedWindVector(windGrid, p.lat, p.lon, now)
          : getFallbackVector(p.lat, p.lon);

        // Convert current lat/lon position to screen pixel coordinates
        const currentPt = map.latLngToContainerPoint([p.lat, p.lon]);

        // Advect particle along continuous vector field (u = Eastward, v = Northward)
        const nextLat = p.lat + vec.v * speedScale;
        const nextLon = p.lon + vec.u * speedScale;

        p.lat = nextLat;
        p.lon = nextLon;

        // Record screen position in particle trail
        p.trail.push(currentPt);
        if (p.trail.length > MAX_TRAIL_LENGTH) {
          p.trail.shift();
        }

        if (p.trail.length < 2) continue;

        // Color coding by wind speed: Sky Cyan (<12 kn), Amber (12-25 kn), Pink/Coral (>25 kn)
        let strokeColor = '#38BDF8';
        if (vec.speedKnots > 25) {
          strokeColor = '#F43F5E';
        } else if (vec.speedKnots > 12) {
          strokeColor = '#F59E0B';
        }

        const alpha = Math.sin((p.age / p.maxAge) * Math.PI);

        // Draw curved streamline flow trail connecting historical positions
        ctx.beginPath();
        ctx.moveTo(p.trail[0].x, p.trail[0].y);

        for (let t = 1; t < p.trail.length; t++) {
          const pt = p.trail[t];
          ctx.lineTo(pt.x, pt.y);
        }

        ctx.strokeStyle = strokeColor;
        ctx.globalAlpha = alpha * 0.38; // Subtle & subordinate to active route & vessel
        ctx.lineWidth = vec.speedKnots > 20 ? 1.6 : 1.2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();

        // Draw small directional flow arrow at particle head
        const headPt = p.trail[p.trail.length - 1];
        const prevPt = p.trail[p.trail.length - 2];
        const angle = Math.atan2(headPt.y - prevPt.y, headPt.x - prevPt.x);

        ctx.beginPath();
        ctx.moveTo(headPt.x, headPt.y);
        ctx.lineTo(
          headPt.x - 4 * Math.cos(angle - Math.PI / 6),
          headPt.y - 4 * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          headPt.x - 4 * Math.cos(angle + Math.PI / 6),
          headPt.y - 4 * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = strokeColor;
        ctx.globalAlpha = alpha * 0.45;
        ctx.fill();
      }

      ctx.globalAlpha = 1.0;
      animFrameRef.current = requestAnimationFrame(renderFrame);
    };

    renderFrame();

    const onMapMove = () => {
      updateCanvasSize();
      // Clear trails on map zoom/pan to avoid pixel artifacts
      for (const p of particles) {
        p.trail = [];
      }
    };

    map.on('move zoom', onMapMove);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      map.off('move zoom', onMapMove);
      if (canvas && canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
        canvasRef.current = null;
      }
    };
  }, [visible, windGrid, cells, map]);

  if (!visible) return null;

  return (
    <>
      {/* Unobtrusive Data Attribution Badge Overlay */}
      <div className="absolute top-4 left-16 z-[400] bg-[#0B2740]/90 backdrop-blur-md border border-[#1B4965] px-3 py-1.5 rounded-xl shadow-xl text-xs flex items-center gap-2 pointer-events-auto">
        <span className="w-2 h-2 rounded-full bg-[#38BDF8] animate-pulse"></span>
        <span className="font-bold text-white text-[11px] font-title">WIND FIELD</span>
        <span className="text-slate-300 font-mono text-[10px] border-l border-[#1B4965] pl-2">
          {statusText}
        </span>
      </div>
    </>
  );
};

export default WeatherLayer;

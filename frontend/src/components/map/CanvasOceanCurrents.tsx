import React, { useEffect, useRef, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { EnvironmentCell } from '../../types/maritime';

interface CanvasOceanCurrentsProps {
  environment: EnvironmentCell[];
  visible: boolean;
}

interface Particle {
  lat: number;
  lon: number;
  age: number;
  maxAge: number;
}

interface SelectedCurrentInfo {
  lat: number;
  lon: number;
  speedKnots: number;
  speedMs: number;
  directionDeg: number;
  directionCardinal: string;
  intensity: 'Low' | 'Moderate' | 'High' | 'Extreme';
  source: string;
  x: number;
  y: number;
}

export const CanvasOceanCurrents: React.FC<CanvasOceanCurrentsProps> = ({ environment, visible }) => {
  const map = useMap();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const [hoverInfo, setHoverInfo] = useState<SelectedCurrentInfo | null>(null);

  // Indian Ocean Bounding Box
  const MIN_LON = 40.0;
  const MAX_LON = 110.0;
  const MIN_LAT = -35.0;
  const MAX_LAT = 30.0;

  useEffect(() => {
    if (!visible || environment.length === 0) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      setHoverInfo(null);
      return;
    }

    const ioCells = environment.filter(
      (c) => c.lon >= MIN_LON && c.lon <= MAX_LON && c.lat >= MIN_LAT && c.lat <= MAX_LAT
    );

    if (ioCells.length === 0) return;

    let canvas = canvasRef.current;
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.style.position = 'absolute';
      canvas.style.top = '0';
      canvas.style.left = '0';
      canvas.style.pointerEvents = 'none';
      canvas.style.zIndex = '180'; // Positioned behind route layer (z-index 400+)
      canvas.style.opacity = '0.85'; // High visibility contrast against nautical navy blue ocean
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

    const getInterpolatedVector = (lat: number, lon: number) => {
      let nearest: EnvironmentCell | null = null;
      let minSqDist = Infinity;
      for (let i = 0; i < ioCells.length; i++) {
        const c = ioCells[i];
        const dLat = c.lat - lat;
        const dLon = c.lon - lon;
        const sqDist = dLat * dLat + dLon * dLon;
        if (sqDist < minSqDist) {
          minSqDist = sqDist;
          nearest = c;
        }
      }
      if (nearest && minSqDist < 4.0) {
        return { u: nearest.current_u, v: nearest.current_v };
      }
      return { u: 0, v: 0 };
    };

    const particleCount = 750;
    const particles: Particle[] = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        lat: MIN_LAT + Math.random() * (MAX_LAT - MIN_LAT),
        lon: MIN_LON + Math.random() * (MAX_LON - MIN_LON),
        age: Math.floor(Math.random() * 80),
        maxAge: 40 + Math.floor(Math.random() * 60),
      });
    }

    const ctx = canvas.getContext('2d');

    const renderFrame = () => {
      if (!ctx || !canvas) return;

      // Clean nautical navy trail background fill
      ctx.fillStyle = 'rgba(9, 23, 37, 0.16)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const zoom = map.getZoom();
      const speedScale = 0.04 * (8 / Math.max(1, zoom));

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.age++;

        if (p.age >= p.maxAge || p.lat < MIN_LAT || p.lat > MAX_LAT || p.lon < MIN_LON || p.lon > MAX_LON) {
          p.lat = MIN_LAT + Math.random() * (MAX_LAT - MIN_LAT);
          p.lon = MIN_LON + Math.random() * (MAX_LON - MIN_LON);
          p.age = 0;
          p.maxAge = 40 + Math.floor(Math.random() * 60);
          continue;
        }

        const vec = getInterpolatedVector(p.lat, p.lon);
        const speedMs = Math.sqrt(vec.u * vec.u + vec.v * vec.v);
        const speedKnots = speedMs * 1.94384;

        const currentPt = map.latLngToContainerPoint([p.lat, p.lon]);

        const nextLat = p.lat + vec.v * speedScale;
        const nextLon = p.lon + vec.u * speedScale;
        const nextPt = map.latLngToContainerPoint([nextLat, nextLon]);

        p.lat = nextLat;
        p.lon = nextLon;

        // Vivid Copernicus SWV palette
        let strokeColor = '#00F0FF'; // Low (<0.8 kn): Cyan
        if (speedKnots > 2.5) {
          strokeColor = '#FF3D00'; // Extreme (>2.5 kn): Coral Red
        } else if (speedKnots > 1.5) {
          strokeColor = '#FFD600'; // High (>1.5 kn): Bright Gold
        } else if (speedKnots > 0.8) {
          strokeColor = '#00E676'; // Moderate (>0.8 kn): Emerald
        }

        const alpha = Math.sin((p.age / p.maxAge) * Math.PI);

        ctx.beginPath();
        ctx.moveTo(currentPt.x, currentPt.y);
        ctx.lineTo(nextPt.x, nextPt.y);
        ctx.strokeStyle = strokeColor;
        ctx.globalAlpha = alpha * 0.75;
        ctx.lineWidth = speedKnots > 1.5 ? 1.8 : 1.2;
        ctx.stroke();
      }

      ctx.globalAlpha = 1.0;
      animFrameRef.current = requestAnimationFrame(renderFrame);
    };

    renderFrame();

    const onMapMove = () => {
      updateCanvasSize();
    };

    const onMapClick = (e: L.LeafletMouseEvent) => {
      if (e.latlng.lat < MIN_LAT || e.latlng.lat > MAX_LAT || e.latlng.lng < MIN_LON || e.latlng.lng > MAX_LON) {
        setHoverInfo(null);
        return;
      }

      const vec = getInterpolatedVector(e.latlng.lat, e.latlng.lng);
      const speedMs = Math.sqrt(vec.u * vec.u + vec.v * vec.v);
      const speedKnots = speedMs * 1.94384;

      if (speedKnots < 0.1) {
        setHoverInfo(null);
        return;
      }

      let rad = Math.atan2(vec.u, vec.v);
      let deg = (rad * (180 / Math.PI) + 360) % 360;
      
      const cardinals = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
      const cardinalIdx = Math.round(deg / 45) % 8;

      let intensity: SelectedCurrentInfo['intensity'] = 'Low';
      if (speedKnots > 2.0) intensity = 'Extreme';
      else if (speedKnots > 1.2) intensity = 'High';
      else if (speedKnots > 0.5) intensity = 'Moderate';

      setHoverInfo({
        lat: e.latlng.lat,
        lon: e.latlng.lng,
        speedKnots: Math.round(speedKnots * 10) / 10,
        speedMs: Math.round(speedMs * 100) / 100,
        directionDeg: Math.round(deg),
        directionCardinal: cardinals[cardinalIdx],
        intensity,
        source: 'Copernicus Marine (GLOBAL_ANALYSISFORECAST_PHY)',
        x: e.containerPoint.x,
        y: e.containerPoint.y,
      });
    };

    map.on('move zoom', onMapMove);
    map.on('click', onMapClick);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      map.off('move zoom', onMapMove);
      map.off('click', onMapClick);
      if (canvas && canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
        canvasRef.current = null;
      }
    };
  }, [environment, visible, map]);

  if (!visible) return null;

  return (
    <>
      {/* Ocean Current On-Click Telemetry Card */}
      {hoverInfo && (
        <div 
          className="pointer-events-auto fixed z-[500] p-3 rounded-xl border border-cyan-500/50 bg-[#0A1B29]/95 shadow-2xl text-xs space-y-1.5 transform -translate-x-1/2 -translate-y-full mb-4 min-w-[220px] backdrop-blur-md"
          style={{ left: hoverInfo.x, top: hoverInfo.y }}
        >
          <div className="font-bold text-white flex items-center justify-between border-b border-[#1D3A4C] pb-1">
            <span className="flex items-center gap-1.5 text-cyan-400 font-mono text-[11px]">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              COPERNICUS CURRENT
            </span>
            <div className="flex items-center gap-1.5">
              <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${
                hoverInfo.intensity === 'Extreme' ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                hoverInfo.intensity === 'High' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                hoverInfo.intensity === 'Moderate' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
              }`}>
                {hoverInfo.intensity}
              </span>
              <button 
                onClick={(e) => { e.stopPropagation(); setHoverInfo(null); }}
                className="text-slate-400 hover:text-white text-xs px-1 font-bold rounded hover:bg-slate-800"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1 text-slate-200">
            <div>
              <span className="text-slate-400 text-[9px] block">VELOCITY</span>
              <span className="font-bold text-white">{hoverInfo.speedKnots} kn</span> ({hoverInfo.speedMs} m/s)
            </div>
            <div>
              <span className="text-slate-400 text-[9px] block">FLOW DIRECTION</span>
              <span className="font-bold text-white">{hoverInfo.directionCardinal} ({hoverInfo.directionDeg}°)</span>
            </div>
          </div>

          <div className="text-[9px] text-slate-400 pt-1 border-t border-[#1D3A4C] truncate">
            Source: <span className="text-cyan-400">{hoverInfo.source}</span>
          </div>
        </div>
      )}
    </>
  );
};

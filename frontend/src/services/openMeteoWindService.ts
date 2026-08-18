/**
 * Open-Meteo Public Forecast API Wind Data Service
 * 
 * Provides batched spatial grid wind data for the Indian Ocean extent.
 * Features 30-minute in-memory caching, request deduplication,
 * smooth hourly time interpolation, spatial bilinear vector interpolation, and vector conversion.
 */

export interface WindPointData {
  lat: number;
  lon: number;
  speedKnots: number;
  directionDeg: number; // Meteorological direction (coming FROM)
  u: number;            // Eastward vector component (knots)
  v: number;            // Northward vector component (knots)
}

export interface OpenMeteoWindGrid {
  fetchedAt: number;
  forecastTimeISO: string;
  points: {
    lat: number;
    lon: number;
    hourlyTimes: string[];
    speedsKnots: number[];
    directionsDeg: number[];
  }[];
  status: 'live' | 'fallback' | 'error';
}

export interface VectorResult {
  u: number;
  v: number;
  speedKnots: number;
  directionDeg: number;
  forecastTimestamp: string;
}

// Indian Ocean Spatial Grid Bounding Box
const LATS = [-30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25];
const LONS = [45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105];

const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes in-memory cache

let cachedWindGrid: OpenMeteoWindGrid | null = null;
let pendingFetchPromise: Promise<OpenMeteoWindGrid> | null = null;

/**
 * Fetches Open-Meteo 10m wind forecast for the Indian Ocean spatial grid in a single batched HTTP GET request.
 */
export async function fetchOpenMeteoWindGrid(): Promise<OpenMeteoWindGrid> {
  const now = Date.now();

  // Return valid cached data if present
  if (cachedWindGrid && now - cachedWindGrid.fetchedAt < CACHE_TTL_MS) {
    return cachedWindGrid;
  }

  // Deduplicate concurrent fetch requests
  if (pendingFetchPromise) {
    return pendingFetchPromise;
  }

  // Generate latitude and longitude arrays for multi-location query
  const gridLats: number[] = [];
  const gridLons: number[] = [];

  for (const lat of LATS) {
    for (const lon of LONS) {
      gridLats.push(lat);
      gridLons.push(lon);
    }
  }

  const latParam = gridLats.join(',');
  const lonParam = gridLons.join(',');
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${latParam}&longitude=${lonParam}&hourly=wind_speed_10m,wind_direction_10m&wind_speed_unit=kn`;

  pendingFetchPromise = (async () => {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Open-Meteo API returned HTTP ${response.status}`);
      }

      const json = await response.json();
      // Handle array of location responses returned by Open-Meteo multi-location API
      const locationResults = Array.isArray(json) ? json : [json];

      const points: OpenMeteoWindGrid['points'] = locationResults.map((loc, idx) => {
        const lat = gridLats[idx] ?? loc.latitude;
        const lon = gridLons[idx] ?? loc.longitude;
        const hourlyTimes: string[] = loc.hourly?.time || [];
        const speedsKnots: number[] = loc.hourly?.wind_speed_10m || [];
        const directionsDeg: number[] = loc.hourly?.wind_direction_10m || [];

        return {
          lat,
          lon,
          hourlyTimes,
          speedsKnots,
          directionsDeg,
        };
      });

      const forecastTimeISO = points[0]?.hourlyTimes[0] || new Date().toISOString();

      const newGrid: OpenMeteoWindGrid = {
        fetchedAt: Date.now(),
        forecastTimeISO,
        points,
        status: 'live',
      };

      cachedWindGrid = newGrid;
      return newGrid;
    } catch (err) {
      console.warn('[Open-Meteo Wind Service] Fetch failed, falling back to cached or default state:', err);
      if (cachedWindGrid) {
        return cachedWindGrid;
      }
      // Return empty fallback grid on complete network error
      return {
        fetchedAt: Date.now(),
        forecastTimeISO: new Date().toISOString(),
        points: [],
        status: 'error',
      };
    } finally {
      pendingFetchPromise = null;
    }
  })();

  return pendingFetchPromise;
}

/**
 * Computes time-interpolated wind vector for a specific grid point index.
 */
function getVectorForPointIndex(
  grid: OpenMeteoWindGrid,
  pointIdx: number,
  targetDate: Date
): { u: number; v: number; speedKnots: number; forecastTimestamp: string } {
  if (!grid || !grid.points || grid.points.length === 0) {
    return { u: 0, v: 0, speedKnots: 0, forecastTimestamp: 'N/A' };
  }

  const safeIdx = Math.max(0, Math.min(grid.points.length - 1, pointIdx));
  const point = grid.points[safeIdx];
  const times = point.hourlyTimes;

  if (!times || times.length === 0) {
    return { u: 0, v: 0, speedKnots: 0, forecastTimestamp: grid.forecastTimeISO };
  }

  const targetTimeMs = targetDate.getTime();
  let idx1 = 0;
  let idx2 = 0;

  for (let i = 0; i < times.length - 1; i++) {
    const t1 = new Date(times[i]).getTime();
    const t2 = new Date(times[i + 1]).getTime();

    if (targetTimeMs >= t1 && targetTimeMs <= t2) {
      idx1 = i;
      idx2 = i + 1;
      break;
    }
    if (targetTimeMs < t1) {
      idx1 = i;
      idx2 = i;
      break;
    }
    idx1 = times.length - 1;
    idx2 = times.length - 1;
  }

  const time1 = new Date(times[idx1]).getTime();
  const time2 = new Date(times[idx2]).getTime();
  const duration = time2 - time1;
  const tFactor = duration > 0 ? Math.max(0, Math.min(1, (targetTimeMs - time1) / duration)) : 0;

  const speed1 = point.speedsKnots[idx1] ?? 0;
  const speed2 = point.speedsKnots[idx2] ?? speed1;
  const speedKnots = speed1 + tFactor * (speed2 - speed1);

  const dir1 = point.directionsDeg[idx1] ?? 0;
  const dir2 = point.directionsDeg[idx2] ?? dir1;

  // Shortest angular arc interpolation
  const diff = (((dir2 - dir1 + 540) % 360) - 180);
  const directionDeg = (dir1 + tFactor * diff + 360) % 360;

  // Convert Meteorological Direction (coming FROM) to Vector blowing TOWARDS
  const blowingTowardsDeg = (directionDeg + 180) % 360;
  const rad = blowingTowardsDeg * (Math.PI / 180);

  return {
    u: speedKnots * Math.sin(rad),
    v: speedKnots * Math.cos(rad),
    speedKnots,
    forecastTimestamp: times[idx1] || grid.forecastTimeISO,
  };
}

/**
 * Computes spatially bilinear and time-interpolated wind vector for any target (lat, lon) position.
 * Produces a continuous, smooth spatial vector field without step boundaries.
 */
export function getInterpolatedWindVector(
  grid: OpenMeteoWindGrid,
  lat: number,
  lon: number,
  targetDate: Date = new Date()
): VectorResult {
  if (!grid || grid.points.length === 0) {
    return { u: 0, v: 0, speedKnots: 0, directionDeg: 0, forecastTimestamp: 'N/A' };
  }

  const STEP = 5.0;
  const LAT_MIN = -30.0;
  const LON_MIN = 45.0;

  const latClamped = Math.max(-30.0, Math.min(25.0, lat));
  const lonClamped = Math.max(45.0, Math.min(105.0, lon));

  const latIdx1 = Math.min(LATS.length - 1, Math.max(0, Math.floor((latClamped - LAT_MIN) / STEP)));
  const latIdx2 = Math.min(LATS.length - 1, latIdx1 + 1);

  const lonIdx1 = Math.min(LONS.length - 1, Math.max(0, Math.floor((lonClamped - LON_MIN) / STEP)));
  const lonIdx2 = Math.min(LONS.length - 1, lonIdx1 + 1);

  const fy = (latClamped - LATS[latIdx1]) / STEP; // 0..1
  const fx = (lonClamped - LONS[lonIdx1]) / STEP; // 0..1

  const pSW = latIdx1 * LONS.length + lonIdx1;
  const pSE = latIdx1 * LONS.length + lonIdx2;
  const pNW = latIdx2 * LONS.length + lonIdx1;
  const pNE = latIdx2 * LONS.length + lonIdx2;

  const vSW = getVectorForPointIndex(grid, pSW, targetDate);
  const vSE = getVectorForPointIndex(grid, pSE, targetDate);
  const vNW = getVectorForPointIndex(grid, pNW, targetDate);
  const vNE = getVectorForPointIndex(grid, pNE, targetDate);

  // Bilinear spatial vector interpolation
  const uSouth = vSW.u * (1 - fx) + vSE.u * fx;
  const uNorth = vNW.u * (1 - fx) + vNE.u * fx;
  const u = uSouth * (1 - fy) + uNorth * fy;

  const vSouth = vSW.v * (1 - fx) + vSE.v * fx;
  const vNorth = vNW.v * (1 - fx) + vNE.v * fx;
  const v = vSouth * (1 - fy) + vNorth * fy;

  const speedKnots = Math.sqrt(u * u + v * v);
  const blowingTowardsRad = Math.atan2(u, v);
  const directionDeg = ((blowingTowardsRad * (180 / Math.PI)) + 180 + 360) % 360;

  return {
    u,
    v,
    speedKnots,
    directionDeg,
    forecastTimestamp: vSW.forecastTimestamp,
  };
}

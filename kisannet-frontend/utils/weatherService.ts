import { WeatherType } from '../types';

export interface HourlyForecastItem {
  time: string;
  hourLabel: string;
  temp: number;
  rainChance: number;
  weatherCode: number;
  icon: string;
  isDay: boolean;
}

export interface DailyForecastItem {
  date: string;
  dayName: string;
  weatherCode: number;
  weatherType: WeatherType;
  maxTemp: number;
  minTemp: number;
  rainChance: number;
  conditionText: string;
  icon: string;
}

export interface LiveWeatherData {
  locationName: string;
  city: string;
  state: string;
  country: string;
  latitude: number;
  longitude: number;
  temperature: number;
  feelsLike: number;
  humidity: number;
  windSpeed: number;
  windDirection: number;
  precipitationProb: number;
  precipitationMm: number;
  weatherCode: number;
  weatherType: WeatherType;
  conditionText: string;
  conditionIcon: string;
  uvIndex: number;
  pressure: number;
  isDay: boolean;
  sourceApi: 'OpenWeather' | 'Open-Meteo';
  hourly: HourlyForecastItem[];
  forecast: DailyForecastItem[];
}

export interface DetectedLocation {
  lat: number;
  lon: number;
  name: string;
  city: string;
  state: string;
  country: string;
  source: 'google' | 'gps' | 'saved' | 'search' | 'ip';
}

export interface LocationSearchResult {
  id: number | string;
  name: string;
  latitude: number;
  longitude: number;
  admin1?: string;
  admin2?: string;
  country?: string;
  displayName: string;
}

const OPENWEATHER_API_KEY = (process.env.NEXT_PUBLIC_OPENWEATHER_API_KEY as string) || '';

/**
 * Maps OpenWeatherMap icon/condition code to WeatherType
 */
export function mapOpenWeatherCodeToType(iconCode: string, mainGroup: string = ''): { type: WeatherType; icon: string; descEn: string; descTe: string } {
  const isNight = iconCode.includes('n');
  const group = mainGroup.toLowerCase();

  if (group.includes('thunderstorm') || iconCode.startsWith('11')) {
    return { type: 'rain', icon: '⛈️', descEn: 'Thunderstorm', descTe: 'ఉరుములు & వర్షం' };
  }
  if (group.includes('drizzle') || iconCode.startsWith('09')) {
    return { type: 'rain', icon: '🌦️', descEn: 'Drizzle', descTe: 'తేలికపాటి చినుకులు' };
  }
  if (group.includes('rain') || iconCode.startsWith('10')) {
    return { type: 'rain', icon: '🌧️', descEn: 'Rain Showers', descTe: 'వర్షం / జల్లులు' };
  }
  if (group.includes('snow') || iconCode.startsWith('13')) {
    return { type: 'rain', icon: '🌨️', descEn: 'Snow / Hail', descTe: 'మంచు / వడగండ్లు' };
  }
  if (group.includes('clear') || iconCode.startsWith('01')) {
    return isNight
      ? { type: 'night', icon: '🌙', descEn: 'Clear Night', descTe: 'స్పష్టమైన రాత్రి' }
      : { type: 'sunny', icon: '☀️', descEn: 'Clear Sky', descTe: 'స్పష్టమైన ఎండ' };
  }
  if (group.includes('cloud') || iconCode.startsWith('02') || iconCode.startsWith('03') || iconCode.startsWith('04')) {
    return { type: 'cloudy', icon: '⛅', descEn: 'Cloudy', descTe: 'పాక్షికంగా మబ్బులు' };
  }
  if (iconCode.startsWith('50') || group.includes('mist') || group.includes('fog')) {
    return { type: 'cloudy', icon: '🌫️', descEn: 'Mist & Fog', descTe: 'మంచు / పొగమంచు' };
  }
  return { type: 'sunny', icon: '☀️', descEn: 'Pleasant Weather', descTe: 'సాధారణ వాతావరణం' };
}

export function mapWmoCodeToType(code: number, isDay: boolean = true): { type: WeatherType; icon: string; descEn: string; descTe: string } {
  if (code === 0) {
    return isDay
      ? { type: 'sunny', icon: '☀️', descEn: 'Clear Sky', descTe: 'స్పష్టమైన ఎండ' }
      : { type: 'night', icon: '🌙', descEn: 'Clear Night', descTe: 'స్పష్టమైన రాత్రి' };
  }
  if ([1, 2].includes(code)) {
    return { type: 'cloudy', icon: '⛅', descEn: 'Partly Cloudy', descTe: 'పాక్షికంగా మేఘావృతం' };
  }
  if (code === 3) {
    return { type: 'cloudy', icon: '☁️', descEn: 'Overcast Sky', descTe: 'దట్టమైన మబ్బులు' };
  }
  if ([45, 48].includes(code)) {
    return { type: 'cloudy', icon: '🌫️', descEn: 'Fog & Mist', descTe: 'మంచు / పొగమంచు' };
  }
  if ([51, 53, 55].includes(code)) {
    return { type: 'rain', icon: '🌦️', descEn: 'Light Drizzle', descTe: 'తేలికపాటి చినుకులు' };
  }
  if ([61, 63, 65, 80, 81, 82].includes(code)) {
    return { type: 'rain', icon: '🌧️', descEn: 'Rain Showers', descTe: 'వర్షం / జల్లులు' };
  }
  if ([71, 73, 75, 77, 85, 86].includes(code)) {
    return { type: 'rain', icon: '🌨️', descEn: 'Hail & Cold Showers', descTe: 'వడగండ్ల వర్షం' };
  }
  if ([95, 96, 99].includes(code)) {
    return { type: 'rain', icon: '⛈️', descEn: 'Thunderstorm', descTe: 'ఉరుములు & వర్షం' };
  }
  return { type: 'sunny', icon: '☀️', descEn: 'Normal Weather', descTe: 'సాధారణ వాతావరణం' };
}

/**
 * Fetch from OpenWeatherMap API (2.5 Current + 5-day / 3-hour Forecast)
 */
export async function fetchOpenWeatherMap(
  latitude: number,
  longitude: number,
  apiKey: string = OPENWEATHER_API_KEY
): Promise<LiveWeatherData> {
  const currentUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${latitude}&lon=${longitude}&units=metric&appid=${apiKey}`;
  const forecastUrl = `https://api.openweathermap.org/data/2.5/forecast?lat=${latitude}&lon=${longitude}&units=metric&appid=${apiKey}`;

  const [currentRes, forecastRes] = await Promise.all([fetch(currentUrl), fetch(forecastUrl)]);

  if (!currentRes.ok) {
    throw new Error(`OpenWeather API error: ${currentRes.status} ${currentRes.statusText}`);
  }

  const current = await currentRes.json();
  const forecastData = forecastRes.ok ? await forecastRes.json() : { list: [] };

  const weatherObj = current.weather?.[0] || {};
  const iconCode = weatherObj.icon || '01d';
  const mainGroup = weatherObj.main || 'Clear';
  const { type: weatherType, icon: conditionIcon, descEn: conditionText } = mapOpenWeatherCodeToType(iconCode, mainGroup);

  const cityName = current.name || 'Farm';
  const country = current.sys?.country || 'IN';

  // Parse Hourly from 3-hour intervals
  const hourlyList: HourlyForecastItem[] = (forecastData.list || []).slice(0, 8).map((item: any, idx: number) => {
    const d = new Date(item.dt * 1000);
    const hourNum = d.getHours();
    const ampm = hourNum >= 12 ? 'PM' : 'AM';
    const displayHour = hourNum % 12 === 0 ? 12 : hourNum % 12;
    const hourLabel = idx === 0 ? 'Now' : `${displayHour} ${ampm}`;
    const ic = item.weather?.[0]?.icon || '01d';
    const { icon } = mapOpenWeatherCodeToType(ic, item.weather?.[0]?.main);

    return {
      time: item.dt_txt || d.toISOString(),
      hourLabel,
      temp: Math.round(item.main?.temp ?? 30),
      rainChance: Math.round((item.pop ?? 0) * 100),
      weatherCode: item.weather?.[0]?.id ?? 800,
      icon,
      isDay: !ic.includes('n'),
    };
  });

  // Group 5-Day Daily Forecast
  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const dailyMap: Record<string, any> = {};

  (forecastData.list || []).forEach((item: any) => {
    const dateKey = item.dt_txt.split(' ')[0];
    if (!dailyMap[dateKey]) {
      dailyMap[dateKey] = {
        temps: [],
        weather: item.weather?.[0],
        rainChances: [],
        date: dateKey,
      };
    }
    dailyMap[dateKey].temps.push(item.main?.temp);
    dailyMap[dateKey].rainChances.push(item.pop ?? 0);
  });

  const forecast: DailyForecastItem[] = Object.keys(dailyMap).slice(0, 7).map((dateKey, idx) => {
    const item = dailyMap[dateKey];
    const d = new Date(dateKey);
    const dayName = idx === 0 ? 'Today' : daysOfWeek[d.getDay()];
    const maxTemp = Math.round(Math.max(...item.temps));
    const minTemp = Math.round(Math.min(...item.temps));
    const maxPop = Math.round(Math.max(...item.rainChances) * 100);
    const ic = item.weather?.icon || '01d';
    const { type, icon, descEn } = mapOpenWeatherCodeToType(ic, item.weather?.main);

    return {
      date: dateKey,
      dayName,
      weatherCode: item.weather?.id || 800,
      weatherType: type,
      conditionText: descEn,
      maxTemp,
      minTemp,
      rainChance: maxPop,
      icon,
    };
  });

  return {
    locationName: `${cityName}, ${country}`,
    city: cityName,
    state: country,
    country,
    latitude,
    longitude,
    temperature: Math.round(current.main?.temp ?? 31),
    feelsLike: Math.round(current.main?.feels_like ?? 33),
    humidity: Math.round(current.main?.humidity ?? 65),
    windSpeed: Math.round((current.wind?.speed ?? 3.5) * 3.6), // m/s to km/h
    windDirection: Math.round(current.wind?.deg ?? 180),
    precipitationProb: hourlyList[0]?.rainChance || 20,
    precipitationMm: Number((current.rain?.['1h'] ?? 0).toFixed(1)),
    weatherCode: weatherObj.id || 800,
    weatherType,
    conditionText: weatherObj.description ? weatherObj.description.toUpperCase() : conditionText,
    conditionIcon,
    uvIndex: 6,
    pressure: Math.round(current.main?.pressure ?? 1012),
    isDay: !iconCode.includes('n'),
    sourceApi: 'OpenWeather',
    hourly: hourlyList,
    forecast: forecast.length > 0 ? forecast : [],
  };
}

/**
 * Open-Meteo Satellite Feed (Fallback / Free API)
 */
export async function fetchOpenMeteo(
  latitude: number,
  longitude: number,
  locationMeta?: { name?: string; city?: string; state?: string; country?: string }
): Promise<LiveWeatherData> {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure&hourly=temperature_2m,precipitation_probability,weather_code,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max&timezone=auto`;

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Open-Meteo API failed: ${res.statusText}`);
  }

  const data = await res.json();
  const current = data.current || {};
  const hourly = data.hourly || {};
  const daily = data.daily || {};
  const isDay = current.is_day === 1;

  const currentCode = current.weather_code ?? 0;
  const { type: weatherType, icon: conditionIcon, descEn: conditionText } = mapWmoCodeToType(currentCode, isDay);

  const hourlyList: HourlyForecastItem[] = [];
  const hourlyTimes = hourly.time || [];
  
  let startIdx = 0;
  const currentIsoPrefix = new Date().toISOString().slice(0, 13);
  for (let i = 0; i < hourlyTimes.length; i++) {
    if (hourlyTimes[i].startsWith(currentIsoPrefix)) {
      startIdx = i;
      break;
    }
  }

  for (let i = startIdx; i < Math.min(startIdx + 12, hourlyTimes.length); i++) {
    const timeStr = hourlyTimes[i];
    const dateObj = new Date(timeStr);
    const hourNum = dateObj.getHours();
    const ampm = hourNum >= 12 ? 'PM' : 'AM';
    const displayHour = hourNum % 12 === 0 ? 12 : hourNum % 12;
    const hourLabel = i === startIdx ? 'Now' : `${displayHour} ${ampm}`;
    const code = hourly.weather_code?.[i] ?? 0;
    const dayFlag = hourly.is_day?.[i] === 1;
    const { icon } = mapWmoCodeToType(code, dayFlag);

    hourlyList.push({
      time: timeStr,
      hourLabel,
      temp: Math.round(hourly.temperature_2m?.[i] ?? 30),
      rainChance: Math.round(hourly.precipitation_probability?.[i] ?? 10),
      weatherCode: code,
      icon,
      isDay: dayFlag,
    });
  }

  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const forecast: DailyForecastItem[] = (daily.time || []).slice(0, 7).map((dateStr: string, idx: number) => {
    const d = new Date(dateStr);
    const dayName = idx === 0 ? 'Today' : daysOfWeek[d.getDay()];
    const code = daily.weather_code?.[idx] ?? 0;
    const { type, icon, descEn } = mapWmoCodeToType(code, true);

    return {
      date: dateStr,
      dayName,
      weatherCode: code,
      weatherType: type,
      conditionText: descEn,
      maxTemp: Math.round(daily.temperature_2m_max?.[idx] ?? 32),
      minTemp: Math.round(daily.temperature_2m_min?.[idx] ?? 22),
      rainChance: Math.round(daily.precipitation_probability_max?.[idx] ?? 20),
      icon,
    };
  });

  return {
    locationName: locationMeta?.name || 'Local Farm',
    city: locationMeta?.city || 'Local',
    state: locationMeta?.state || 'India',
    country: locationMeta?.country || 'India',
    latitude,
    longitude,
    temperature: Math.round(current.temperature_2m ?? 31),
    feelsLike: Math.round(current.apparent_temperature ?? 33),
    humidity: Math.round(current.relative_humidity_2m ?? 65),
    windSpeed: Math.round(current.wind_speed_10m ?? 12),
    windDirection: Math.round(current.wind_direction_10m ?? 180),
    precipitationProb: Math.round(daily.precipitation_probability_max?.[0] ?? 35),
    precipitationMm: Number((current.precipitation ?? 0).toFixed(1)),
    weatherCode: currentCode,
    weatherType,
    conditionText,
    conditionIcon,
    uvIndex: Math.round(daily.uv_index_max?.[0] ?? 6),
    pressure: Math.round(current.surface_pressure ?? 1012),
    isDay,
    sourceApi: 'Open-Meteo',
    hourly: hourlyList,
    forecast,
  };
}

/**
 * Unified Live Weather Fetcher:
 * Automatically uses OpenWeatherMap if key is provided in .env, otherwise Open-Meteo
 */
export async function fetchLiveWeather(
  latitude: number,
  longitude: number,
  locationMeta?: { name?: string; city?: string; state?: string; country?: string }
): Promise<LiveWeatherData> {
  const customKey = localStorage.getItem('kissannet_openweather_key') || OPENWEATHER_API_KEY;

  if (customKey && customKey.trim()) {
    try {
      return await fetchOpenWeatherMap(latitude, longitude, customKey.trim());
    } catch (e) {
      console.warn('OpenWeatherMap call failed, falling back to Open-Meteo:', e);
    }
  }

  return fetchOpenMeteo(latitude, longitude, locationMeta);
}

/**
 * Search locations using Open-Meteo or OpenWeather Geocoding
 */
export async function searchLocationByName(query: string): Promise<LocationSearchResult[]> {
  if (!query || query.trim().length < 2) return [];
  
  const customKey = localStorage.getItem('kissannet_openweather_key') || OPENWEATHER_API_KEY;

  if (customKey && customKey.trim()) {
    try {
      const res = await fetch(`https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(query.trim())}&limit=8&appid=${customKey.trim()}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          return data.map((r: any, idx: number) => ({
            id: `owm_${idx}_${r.lat}`,
            name: r.name,
            latitude: r.lat,
            longitude: r.lon,
            admin1: r.state,
            country: r.country,
            displayName: [r.name, r.state, r.country].filter(Boolean).join(', '),
          }));
        }
      }
    } catch (e) {}
  }

  try {
    const res = await fetch(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query.trim())}&count=10&language=en&format=json`
    );
    if (res.ok) {
      const data = await res.json();
      const results = data.results || [];
      return results.map((r: any) => {
        const parts = [r.name, r.admin2, r.admin1, r.country].filter(Boolean);
        return {
          id: r.id,
          name: r.name,
          latitude: r.latitude,
          longitude: r.longitude,
          admin1: r.admin1,
          admin2: r.admin2,
          country: r.country,
          displayName: parts.join(', '),
        };
      });
    }
  } catch (e) {
    console.warn('Geocoding search error:', e);
  }
  return [];
}

/**
 * High-accuracy Device GPS Detection
 */
export async function getHighAccuracyGPS(): Promise<DetectedLocation> {
  if (typeof navigator === 'undefined' || !navigator.geolocation) {
    throw new Error('Geolocation is not supported by your browser.');
  }

  const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      timeout: 10000,
      enableHighAccuracy: true,
      maximumAge: 0,
    });
  });

  const { latitude, longitude } = pos.coords;
  const reverse = await reverseGeocode(latitude, longitude);

  const locObj: DetectedLocation = {
    lat: latitude,
    lon: longitude,
    name: reverse.fullName,
    city: reverse.city,
    state: reverse.state,
    country: reverse.country,
    source: 'gps',
  };

  try {
    localStorage.setItem('kissannet_weather_loc', JSON.stringify(locObj));
  } catch (e) {}

  return locObj;
}

/**
 * Automatic Location Detection Strategy
 */
export async function autoDetectLocation(): Promise<DetectedLocation> {
  try {
    const saved = localStorage.getItem('kissannet_weather_loc');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.lat && parsed.lon && parsed.name) {
        return parsed;
      }
    }
  } catch (e) {}

  if (typeof navigator !== 'undefined' && navigator.geolocation) {
    try {
      return await getHighAccuracyGPS();
    } catch (gpsError) {
      throw new Error('GPS permission denied or unavailable. Please select your district manually.');
    }
  }

  throw new Error('Location services not supported. Please select your district manually.');
}

export async function reverseGeocode(lat: number, lon: number): Promise<{ fullName: string; city: string; state: string; country: string }> {
  try {
    const res = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`
    );
    if (res.ok) {
      const data = await res.json();
      const city = data.locality || data.city || data.principalSubdivision || 'Local Farm';
      const state = data.principalSubdivision || 'India';
      const country = data.countryName || 'India';
      return {
        fullName: `${city}, ${state}`,
        city,
        state,
        country,
      };
    }
  } catch (e) {}

  return {
    fullName: `Farm (${lat.toFixed(2)}, ${lon.toFixed(2)})`,
    city: 'Local Farm',
    state: 'India',
    country: 'India',
  };
}

export interface AdvisoryItem {
  status: string;
  badge: string;
  title: string;
  advice: string;
}

export interface WeatherAiAdvisory {
  spraying: AdvisoryItem;
  irrigation: AdvisoryItem;
  fertilizer: AdvisoryItem;
}

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL as string) || 'http://localhost:8000';

export async function fetchAiWeatherAdvisory(params: {
  cropName: string;
  location: string;
  temperature: number;
  feelsLike: number;
  humidity: number;
  windSpeed: number;
  precipitationProb: number;
  condition: string;
  languageCode: string;
}): Promise<WeatherAiAdvisory | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/weather/ai-advisory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop_name: params.cropName,
        location: params.location,
        temperature: params.temperature,
        feels_like: params.feelsLike,
        humidity: params.humidity,
        wind_speed: params.windSpeed,
        precipitation_prob: params.precipitationProb,
        condition: params.condition,
        language_code: params.languageCode,
      }),
    });

    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn('Backend Gemini AI Weather Advisory error, falling back to local heuristic:', e);
  }
  return null;
}


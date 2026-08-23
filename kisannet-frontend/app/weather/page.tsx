"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { 
  CloudRain, CloudSun, MapPin, Search, Bell, Sun, Wind, Droplets, 
  Eye, Gauge, Sprout, TrendingDown, ArrowRight, SunDim, Moon, 
  Home as HomeIcon, MessageCircle, Landmark, TrendingUp as MarketIcon, TrendingUp,
  Cloud, UserCircle2, Phone, Facebook, Instagram, Youtube, Loader2
} from 'lucide-react';
import { IMAGES } from '@/lib/images';
import logo from '@/assets/image.png';
import { fetchLiveWeather, LiveWeatherData, autoDetectLocation } from '@/utils/weatherService';
import { useLanguage } from '@/context/LanguageContext';

const SIDEBAR_LINKS = [
  { href: "/", label: "Home", icon: HomeIcon },
  { href: "/advisory", label: "Advice", icon: MessageCircle },
  { href: "/schemes", label: "Schemes", icon: Landmark },
  { href: "/market", label: "Market Prices", icon: MarketIcon },
  { href: "/weather", label: "Weather", icon: Cloud },
  { href: "/profile", label: "Profile", icon: UserCircle2 },
];

function getLucideIcon(weatherType: string, isDay: boolean = true) {
  switch (weatherType) {
    case 'rain': return CloudRain;
    case 'cloudy': return CloudSun;
    case 'sunny': return isDay ? Sun : Moon;
    case 'night': return Moon;
    default: return Sun;
  }
}

export default function WeatherPage() {
  const pathname = usePathname();
  const { currentOption, setIsLanguageModalOpen, t } = useLanguage();
  const [weather, setWeather] = useState<LiveWeatherData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadWeather() {
      try {
        const loc = await autoDetectLocation();
        const data = await fetchLiveWeather(loc.lat, loc.lon, { 
          name: loc.name, city: loc.city, state: loc.state, country: loc.country 
        });
        setWeather(data);
      } catch (err) {
        console.warn("Location auto-detect failed, using default", err);
        const fallbackData = await fetchLiveWeather(16.5062, 80.6480, { 
          name: 'Vijayawada', city: 'Vijayawada', state: 'Andhra Pradesh', country: 'India' 
        });
        setWeather(fallbackData);
      } finally {
        setLoading(false);
      }
    }
    
    loadWeather();
  }, []);

  return (
    <div className="flex flex-col lg:flex-row min-h-screen lg:h-screen w-full bg-[#F9F7EF] text-[#2D3A32] font-sans">
      
      {/* ── LEFT SIDEBAR (Desktop Only) ── */}
      <aside className="hidden lg:flex w-44 shrink-0 flex-col bg-white border-r border-soil/10 shadow-soft z-20 h-full">
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-soil/10">
          <Image src={logo} alt="KisanNet" className="w-8 h-8 rounded-full object-contain" />
          <span className="font-display font-black text-paddy text-base">KisanNet</span>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {SIDEBAR_LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            const keyMap: Record<string, string> = { "Home": "home", "Advice": "advisory", "Schemes": "schemes", "Market Prices": "market", "Weather": "weatherInfo", "Profile": "profile" };
            const tKey = keyMap[label] || label.toLowerCase();
            return (
              <Link key={href} href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-2xl text-sm font-semibold transition-all ${active ? "bg-paddy/10 text-paddy font-bold" : "text-soil/60 hover:bg-husk hover:text-paddy"
                  }`}>
                <Icon size={18} strokeWidth={active ? 2.4 : 2} />
                <span>{t(tKey, label)}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 pb-6 mt-auto">
          <div className="bg-white rounded-2xl p-3 flex items-start gap-3 shadow-card border border-soil/10 mb-6">
            <div className="w-8 h-8 rounded-full bg-paddy/15 flex items-center justify-center shrink-0">
              <Phone size={14} className="text-paddy" />
            </div>
            <div>
              <p className="text-xs font-bold text-paddy-dark">{t('needHelpTitle', 'Need Help?')}</p>
              <p className="text-[10px] text-soil/60 font-medium">{t('needHelpDesc', 'Talk to an expert')}</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-paddy-dark">
            <MessageCircle size={16} />
            <Youtube size={16} />
            <Facebook size={16} />
            <Instagram size={16} />
          </div>
          <p className="text-left text-[10px] text-soil/40 font-medium mt-4">© 2025 KisanNet<br />All rights reserved</p>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-y-auto">
      
      {/* Top Header */}
      <header className="flex justify-between items-center p-4 lg:p-6 lg:pb-4 border-b lg:border-none border-[#E6DFCD]">
        <div className="flex items-center gap-4">
          <div onClick={() => setIsLanguageModalOpen(true)} className="bg-white border border-[#E6DFCD] rounded-full px-4 py-2 flex items-center gap-2 shadow-sm cursor-pointer hover:bg-gray-50">
            <GlobeIcon className="w-5 h-5 text-[#5C6F62]" />
            <span className="text-sm font-semibold text-[#245C35]">{currentOption.nativeName}</span>
            <ChevronDownIcon className="w-4 h-4 text-[#5C6F62]" />
          </div>
          <div className="hidden sm:flex bg-white border border-[#E6DFCD] rounded-full px-4 py-2 items-center gap-3 shadow-sm">
            {weather ? (
              <>
                {React.createElement(getLucideIcon(weather.weatherType, weather.isDay), { className: "w-5 h-5 text-amber-500" })}
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-[#1E4A32]">{weather.temperature}°C</span>
                  <span className="text-[10px] text-[#5C6F62] leading-tight truncate max-w-[80px]">{weather.conditionText}</span>
                </div>
              </>
            ) : (
              <Loader2 className="w-5 h-5 animate-spin text-[#5C6F62]" />
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="relative w-10 h-10 rounded-full bg-white border border-[#E6DFCD] flex items-center justify-center shadow-sm hover:bg-gray-50">
            <Bell className="w-5 h-5 text-[#5C6F62]" />
            <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
          </button>
          <div className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden shadow-sm border border-[#E6DFCD] cursor-pointer">
            <div className="w-full h-full bg-[#DDECD9] flex justify-center items-center">
              <UserIcon className="w-6 h-6 text-[#307042]" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-4 lg:p-6 flex flex-col gap-6 pb-12">
        
        {loading || !weather ? (
           <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
             <Loader2 className="w-10 h-10 animate-spin text-paddy mb-4" />
             <p className="font-semibold text-soil/70">{t('fetchingWeather', 'Fetching real-time weather...')}</p>
           </div>
        ) : (
          <>
          {/* Hero Weather Card */}
          <div className="relative w-full min-h-[320px] rounded-[2rem] overflow-hidden text-white shadow-xl bg-[#2c3e50]">
            <Image 
              src={IMAGES.greenFieldHero} 
              alt="Farm Weather" 
              fill 
              className="object-cover object-center grayscale-[20%] brightness-75"
              priority 
            />
            <div className="absolute inset-0 bg-black/40 bg-gradient-to-t from-black/80 to-transparent z-0"></div>
            
            <div className="relative z-10 p-6 lg:p-8 flex flex-col h-full min-h-[320px]">
              <div className="flex flex-col sm:flex-row sm:justify-between items-start sm:items-center gap-4 mb-8">
                <div className="flex items-center gap-2 text-white/90">
                  <MapPin className="w-5 h-5" />
                  <span className="font-medium text-lg text-white">{weather.locationName}</span>
                  <button className="ml-2 text-xs border border-white/30 rounded-full px-3 py-1 hover:bg-white/10 transition">{t('changeLocation', 'Change Location')}</button>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 border border-white/20 bg-white/10 rounded-full px-4 py-1.5 backdrop-blur-md">
                    <CalendarIcon className="w-4 h-4 text-white/80" />
                    <span className="text-sm font-medium">{new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  </div>
                  <div className="flex items-center gap-2 border border-white/20 bg-white/10 rounded-full px-4 py-1.5 backdrop-blur-md">
                    <ClockIcon className="w-4 h-4 text-white/80" />
                    <span className="text-sm font-medium">
                      {new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col lg:flex-row justify-between items-end lg:items-center mt-auto gap-8">
                <div className="flex flex-col">
                  <div className="flex items-center gap-4">
                    {React.createElement(getLucideIcon(weather.weatherType, weather.isDay), { className: "w-20 h-20 text-white" })}
                    <div className="flex items-start">
                      <span className="text-7xl lg:text-8xl font-bold tracking-tighter">{weather.temperature}</span>
                      <span className="text-3xl lg:text-4xl font-semibold mt-2">°C</span>
                    </div>
                  </div>
                  <h2 className="text-2xl font-semibold mt-2">{weather.conditionText}</h2>
                  <div className="flex items-center gap-4 mt-2 text-white/80 font-medium">
                    <span>{t('feelsLike', 'Feels like')} {weather.feelsLike}°C</span>
                    <span className="w-1 h-1 bg-white/50 rounded-full"></span>
                    <span>{t('highTemp', 'H:')} {weather.forecast[0]?.maxTemp ?? weather.temperature}°C</span>
                    <span>{t('lowTemp', 'L:')} {weather.forecast[0]?.minTemp ?? weather.temperature}°C</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 bg-white/10 backdrop-blur-lg border border-white/20 rounded-3xl p-6 w-full lg:w-auto">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/70 text-sm"><Droplets className="w-4 h-4 text-[#8DEB8D]"/> {t('humidity', 'Humidity')}</div>
                    <span className="text-xl font-semibold">{weather.humidity}%</span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/70 text-sm"><Wind className="w-4 h-4 text-[#8DEB8D]"/> {t('wind', 'Wind')}</div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-xl font-semibold">{weather.windSpeed}</span>
                      <span className="text-xs">{t('kmh', 'km/h')}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/70 text-sm"><CloudRain className="w-4 h-4 text-[#8DEB8D]"/> {t('rainChance', 'Rain Chance')}</div>
                    <span className="text-xl font-semibold">{weather.precipitationProb}%</span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/70 text-sm"><Sun className="w-4 h-4 text-amber-400"/> {t('uvIndex', 'UV Index')}</div>
                    <div className="flex flex-col">
                      <span className="text-xl font-semibold">{weather.uvIndex}</span>
                      <span className="text-xs text-white/80">{weather.uvIndex < 3 ? t('low', 'Low') : weather.uvIndex < 6 ? t('moderate', 'Moderate') : t('high', 'High')}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/70 text-sm"><Gauge className="w-4 h-4 text-[#8DEB8D]"/> {t('pressure', 'Pressure')}</div>
                    <span className="text-xl font-semibold">{weather.pressure} hPa</span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-white/70 text-sm"><Eye className="w-4 h-4 text-[#8DEB8D]"/> {t('rainMm', 'Rain (mm)')}</div>
                    <span className="text-xl font-semibold">{weather.precipitationMm} mm</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-20 lg:pb-0">
            <div className="lg:col-span-2 flex flex-col gap-6">
              
              {/* Rain Alert (Dynamic based on POP) */}
              {weather.precipitationProb > 40 && (
                <div className="bg-[#E6F0E3] rounded-2xl p-4 flex items-center justify-between border border-[#CDE3CA]">
                  <div className="flex items-center gap-4">
                    <CloudRain className="w-8 h-8 text-[#245C35]" />
                    <div>
                      <h3 className="font-bold text-[#1E4A32]">{t('rainAlertTitle', 'Rain Alert')}</h3>
                      <p className="text-sm text-[#3E5246]">{weather.precipitationProb}% {t('rainAlertDesc', 'chance of rain expected in your area.')}</p>
                    </div>
                  </div>
                  <button className="hidden sm:flex items-center gap-1 text-sm font-bold text-[#245C35] hover:underline">
                    {t('viewDetails', 'View Details')} <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Hourly Forecast */}
              <div className="bg-white rounded-2xl p-6 border border-[#E6DFCD] shadow-sm overflow-x-auto">
                <h3 className="font-bold text-[#1E4A32] mb-4">{t('hourlyForecast', 'Hourly Forecast')}</h3>
                <div className="flex justify-between gap-6 min-w-max">
                  {weather.hourly.slice(0, 10).map((item, i) => {
                    const HourlyIcon = getLucideIcon(weather.weatherType, item.isDay); // Simplified mapping
                    return (
                      <div key={i} className={`flex flex-col items-center gap-2 px-2 py-3 rounded-xl ${i === 0 ? 'bg-[#F0EAD8]' : ''}`}>
                        <span className="text-xs font-semibold text-[#5C6F62]">{item.hourLabel}</span>
                        <HourlyIcon className={`w-6 h-6 ${item.rainChance > 20 ? 'text-[#3A7CA5]' : 'text-[#8C9B90]'}`} />
                        <span className="font-bold text-[#1E4A32]">{item.temp}°</span>
                        {item.rainChance > 0 && <span className="text-[10px] font-bold text-[#3A7CA5]">{item.rainChance}%</span>}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="bg-white rounded-2xl p-6 border border-[#E6DFCD] shadow-sm flex flex-col">
                  <h3 className="font-bold text-[#1E4A32] mb-1 flex items-center gap-2">
                    <Sprout className="w-5 h-5 text-[#245C35]" /> {t('weatherForFarming', 'Weather for Farming')}
                  </h3>
                  <p className="text-sm text-[#5C6F62] mb-6">
                    {weather.temperature > 35 ? t('weatherExtremelyHot', 'Extremely hot. Avoid field work at noon.') :
                     weather.precipitationProb > 60 ? t('weatherHeavyRain', 'Heavy rain expected. Postpone spraying.') : 
                     t('weatherGoodConditions', 'Conditions are good for most crops.')}
                  </p>
                  <div className="flex justify-between mt-auto">
                    <div className="flex flex-col items-center gap-1">
                      <Droplets className={`w-6 h-6 ${weather.precipitationProb > 50 ? 'text-amber-500' : 'text-[#3A7CA5]'}`} />
                      <span className="text-[10px] font-semibold text-[#5C6F62] text-center">
                        {weather.precipitationProb > 50 ? t('skipIrrigation', 'Skip Irrigation') : t('goodForIrrigation', 'Good time for Irrigation')}
                      </span>
                    </div>
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-2xl">🌱</span>
                      <span className="text-[10px] font-semibold text-[#5C6F62] text-center">
                        {(weather.precipitationProb > 40 || weather.windSpeed > 20) ? <>{t('delayUrea', 'Delay Urea')}<br/>({t('runoffRisk', 'Runoff Risk')})</> : <>{t('fertilizer', 'Fertilizer')}<br/>{t('applyUrea', 'Apply Urea')}</>}
                      </span>
                    </div>
                    <div className="flex flex-col items-center gap-1">
                      {weather.humidity > 80 && weather.temperature > 25 ? (
                         <TrendingUp className="w-6 h-6 text-red-500" />
                      ) : (
                         <TrendingDown className="w-6 h-6 text-[#245C35]" />
                      )}
                      <span className="text-[10px] font-semibold text-[#5C6F62] text-center">
                        {t('pestRisk', 'Pest Risk')}<br/>
                        {weather.humidity > 80 && weather.temperature > 25 ? t('high', 'High') : weather.humidity > 60 ? t('moderate', 'Moderate') : t('low', 'Low')}
                      </span>
                    </div>
                  </div>
                  <button className="flex items-center justify-end gap-1 text-xs font-bold text-[#245C35] hover:underline mt-6">
                    {t('viewDetailedAdvice', 'View Detailed Advice')} <ArrowRight className="w-3 h-3" />
                  </button>
                </div>

                <div className="bg-white rounded-2xl p-6 border border-[#E6DFCD] shadow-sm flex flex-col relative overflow-hidden">
                  <h3 className="font-bold text-[#1E4A32] mb-4">{t('liveRadarMap', 'Live Radar Map')}</h3>
                  <div className="flex-1 rounded-xl bg-[#e3f2fd] border border-[#E6DFCD] overflow-hidden relative min-h-[200px]">
                     <iframe 
                       width="100%" 
                       height="100%" 
                       src={`https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=%C2%B0C&metricWind=km%2Fh&zoom=8&overlay=rain&product=ecmwf&level=surface&lat=${weather.latitude}&lon=${weather.longitude}`}
                       frameBorder="0"
                       className="absolute inset-0 w-full h-full"
                     ></iframe>
                  </div>
                  <button 
                    className="absolute bottom-8 right-8 bg-white/90 backdrop-blur border border-[#E6DFCD] px-3 py-1.5 rounded-lg text-xs font-bold text-[#1E4A32] flex items-center gap-1 shadow-sm hover:bg-white"
                    onClick={() => window.open(`https://www.windy.com/?${weather.latitude},${weather.longitude},8`, '_blank')}
                  >
                    {t('viewFullMap', 'View Full Map')} <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-6">
              <div className="bg-white rounded-2xl p-6 border border-[#E6DFCD] shadow-sm flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <SunDim className="w-8 h-8 text-amber-500" />
                  <div>
                    <p className="text-xs font-semibold text-[#5C6F62]">{t('sunrise', 'Sunrise')}</p>
                    <p className="font-bold text-[#1E4A32]">5:37 AM</p>
                  </div>
                </div>
                <div className="w-px h-10 bg-[#E6DFCD]"></div>
                <div className="flex items-center gap-4">
                  <Moon className="w-8 h-8 text-indigo-500" />
                  <div>
                    <p className="text-xs font-semibold text-[#5C6F62]">{t('sunset', 'Sunset')}</p>
                    <p className="font-bold text-[#1E4A32]">6:41 PM</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border border-[#E6DFCD] shadow-sm flex-1">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="font-bold text-[#1E4A32]">{t('7dayForecast', '7-Day Forecast')}</h3>
                  <button className="text-xs font-bold text-[#245C35] hover:underline flex items-center gap-1">
                    {t('viewAll', 'View All')} <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
                
                <div className="flex flex-col gap-4">
                  {weather.forecast.map((item, i) => {
                    const DailyIcon = getLucideIcon(item.weatherType, true);
                    return (
                      <div key={i} className="flex items-center justify-between py-2 border-b border-[#F0EAD8] last:border-0">
                        <div className="w-20">
                          <p className="font-bold text-sm text-[#1E4A32]">{item.dayName}</p>
                          <p className="text-[10px] text-[#5C6F62]">{item.date.slice(5)}</p>
                        </div>
                        <div className="w-8 flex justify-center">
                          <DailyIcon className={`w-5 h-5 ${item.weatherType === 'sunny' ? 'text-amber-500' : (item.rainChance > 20 ? 'text-[#3A7CA5]' : 'text-[#8C9B90]')}`} />
                        </div>
                        <div className="w-20 text-right flex gap-2 justify-end text-sm font-semibold text-[#1E4A32]">
                          <span>{item.maxTemp}°</span>
                          <span className="text-[#8C9B90]">/</span>
                          <span className="text-[#5C6F62]">{item.minTemp}°</span>
                        </div>
                        <div className="w-12 text-right">
                          <span className="text-[11px] font-bold text-[#3A7CA5]">{item.rainChance}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
          </>
        )}
      </div>
      </div>
    </div>
  );
}

// Simple Icon Components to match lucide-react if they don't exist exactly
function GlobeIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
  );
}

function ChevronDownIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="m6 9 6 6 6-6"/></svg>
  );
}

function UserIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  );
}

function CalendarIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
  );
}

function ClockIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
  );
}

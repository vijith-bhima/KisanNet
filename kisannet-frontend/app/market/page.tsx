"use client";
import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { 
  Home as HomeIcon, MessageCircle, Landmark, TrendingUp as MarketIcon, Cloud, 
  UserCircle2, Phone, Bell, Globe, Search, Download, 
  TrendingUp, TrendingDown, Minus, RefreshCw, Calendar, ChevronDown, 
  ArrowUpDown, ArrowUp, ArrowDown, X, Check, Filter, Sparkles,
  Youtube, Facebook, Instagram
} from 'lucide-react';
import { IMAGES } from '@/lib/images';
import logo from '@/assets/image.png';
import { fetchLiveWeather, LiveWeatherData, autoDetectLocation } from '@/utils/weatherService';
import { useLanguage } from '@/context/LanguageContext';
import { DEFAULT_CROP_IMAGE } from '@/lib/cropMetadata';

const SIDEBAR_LINKS = [
  { href: "/", label: "Home", labelTe: "హోమ్", icon: HomeIcon },
  { href: "/advisory", label: "Advice", labelTe: "సలహా", icon: MessageCircle },
  { href: "/schemes", label: "Schemes", labelTe: "పథకాలు", icon: Landmark },
  { href: "/market", label: "Market Prices", labelTe: "మార్కెట్ ధరలు", icon: MarketIcon },
  { href: "/weather", label: "Weather", labelTe: "వాతావరణం", icon: Cloud },
  { href: "/profile", label: "Profile", labelTe: "ప్రొఫైల్", icon: UserCircle2 },
];

export interface MandiRecord {
  id: string;
  cropNameTe: string;
  cropNameEn: string;
  rawCommodity: string;
  category: string;
  variety: string;
  imageUrl: string;
  currentPrice: number;
  modalPrice: number;
  minPrice: number;
  maxPrice: number;
  pricePerKg: number;
  minPricePerKg: number;
  maxPricePerKg: number;
  unit: string;
  unitKg: string;
  priceChange: number;
  trend: 'up' | 'down' | 'stable';
  trendTextTe: string;
  district: string;
  state: string;
  marketNameTe: string;
  marketNameEn: string;
  distanceKm: number;
  date: string;
  rawDate: string;
}

// Sparkline graph
const Sparkline = ({ trend }: { trend: 'up' | 'down' | 'stable' }) => {
  const points = Array.from({ length: 10 }, () => Math.floor(Math.random() * 20) + 10);
  if (trend === 'up') points.sort((a, b) => a - b);
  if (trend === 'down') points.sort((a, b) => b - a);
  
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;
  
  const path = points.map((p, i) => {
    const x = (i / (points.length - 1)) * 55;
    const y = 18 - ((p - min) / range) * 16;
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  const color = trend === 'up' ? '#10b981' : trend === 'down' ? '#ef4444' : '#64748b';

  return (
    <svg width="55" height="20" className="overflow-visible inline-block">
      <path d={path} fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

export default function MarketPage() {
  const [liveWeather, setLiveWeather] = useState<LiveWeatherData | null>(null);
  const { currentOption, setIsLanguageModalOpen, t, language } = useLanguage();
  const pathname = usePathname();
  
  const [marketData, setMarketData] = useState<MandiRecord[]>([]);
  const [loadingMarket, setLoadingMarket] = useState(true);
  const [lastUpdatedTime, setLastUpdatedTime] = useState<string>("");
  const [currentDateStr, setCurrentDateStr] = useState<string>("");
  
  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCommodity, setSelectedCommodity] = useState("ALL");
  const [selectedDistrict, setSelectedDistrict] = useState("ALL");
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [unitMode, setUnitMode] = useState<'both' | 'qtl' | 'kg'>('both');
  const [showAllMarkets, setShowAllMarkets] = useState(false);

  // Sorting
  const [sortField, setSortField] = useState<'crop' | 'market' | 'district' | 'modalPrice' | 'pricePerKg' | 'change'>('modalPrice');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Load Data
  const loadMarketPrices = () => {
    setLoadingMarket(true);
    fetch('/api/market')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data && data.data.length > 0) {
          setMarketData(data.data);
          setLastUpdatedTime(data.lastUpdated || new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
          setCurrentDateStr(data.currentDate || new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }));
        }
      })
      .catch(err => {
        console.error("Failed to load live prices", err);
      })
      .finally(() => setLoadingMarket(false));
  };

  useEffect(() => {
    // Current date initial
    setCurrentDateStr(new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }));
    setLastUpdatedTime(new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));

    // Weather
    autoDetectLocation()
      .then(loc => fetchLiveWeather(loc.lat, loc.lon, { name: loc.name, city: loc.city, state: loc.state, country: loc.country }))
      .then(data => setLiveWeather(data))
      .catch(() => {
        fetchLiveWeather(16.3067, 80.4365).then(setLiveWeather).catch(() => {});
      });

    loadMarketPrices();
  }, []);

  // Extract unique commodities and districts for dropdowns
  const availableCommodities = useMemo(() => {
    const set = new Set<string>();
    marketData.forEach(item => {
      if (item.cropNameEn) set.add(item.cropNameEn);
    });
    return Array.from(set).sort();
  }, [marketData]);

  const availableDistricts = useMemo(() => {
    const set = new Set<string>();
    marketData.forEach(item => {
      if (item.district) set.add(item.district);
    });
    return Array.from(set).sort();
  }, [marketData]);

  // Filtered and Sorted Data
  const filteredData = useMemo(() => {
    let result = marketData.filter(mandi => {
      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesName = mandi.cropNameEn.toLowerCase().includes(q) || 
                            mandi.cropNameTe.includes(q) ||
                            (mandi.rawCommodity && mandi.rawCommodity.toLowerCase().includes(q));
        const matchesMarket = mandi.marketNameEn.toLowerCase().includes(q) || 
                              (mandi.district && mandi.district.toLowerCase().includes(q));
        if (!matchesName && !matchesMarket) return false;
      }

      // Commodity Filter
      if (selectedCommodity !== "ALL" && mandi.cropNameEn !== selectedCommodity) {
        return false;
      }

      // District Filter
      if (selectedDistrict !== "ALL" && mandi.district !== selectedDistrict) {
        return false;
      }

      // Category Filter
      if (selectedCategory !== "ALL" && mandi.category !== selectedCategory) {
        return false;
      }

      return true;
    });

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      if (sortField === 'crop') {
        comparison = a.cropNameEn.localeCompare(b.cropNameEn);
      } else if (sortField === 'market') {
        comparison = a.marketNameEn.localeCompare(b.marketNameEn);
      } else if (sortField === 'district') {
        comparison = (a.district || '').localeCompare(b.district || '');
      } else if (sortField === 'modalPrice') {
        comparison = a.modalPrice - b.modalPrice;
      } else if (sortField === 'pricePerKg') {
        comparison = a.pricePerKg - b.pricePerKg;
      } else if (sortField === 'change') {
        comparison = a.priceChange - b.priceChange;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [marketData, searchQuery, selectedCommodity, selectedDistrict, selectedCategory, sortField, sortOrder]);

  // Unique top cards (group by crop name so top cards show 1 per crop)
  const uniqueCropCards = useMemo(() => {
    const seen = new Set<string>();
    const cards: MandiRecord[] = [];
    filteredData.forEach(item => {
      if (!seen.has(item.cropNameEn)) {
        seen.add(item.cropNameEn);
        cards.push(item);
      }
    });
    return cards;
  }, [filteredData]);

  // Toggle Sorting
  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // CSV Export
  const downloadCSV = () => {
    if (filteredData.length === 0) return;

    const headers = ["Commodity (English)", "Commodity (Telugu)", "Market", "District", "State", "Modal Price (Rs/Qtl)", "Price Per Kg (Rs/Kg)", "Min Price (Rs/Qtl)", "Max Price (Rs/Qtl)", "Arrival Date"];
    const rows = filteredData.map(item => [
      `"${item.cropNameEn}"`,
      `"${item.cropNameTe}"`,
      `"${item.marketNameEn}"`,
      `"${item.district}"`,
      `"${item.state}"`,
      item.modalPrice,
      item.pricePerKg,
      item.minPrice,
      item.maxPrice,
      `"${item.date}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `KisanNet_Market_Prices_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen lg:h-screen w-full bg-[#F9F7EF] text-[#2D3A32] font-sans">
      
      {/* ── LEFT SIDEBAR (Desktop Only) ── */}
      <aside className="hidden lg:flex w-48 shrink-0 flex-col bg-white border-r border-soil/10 shadow-soft z-20 h-full">
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-soil/10">
          <Image src={logo} alt="KisanNet" className="w-8 h-8 rounded-full object-contain" />
          <span className="font-display font-black text-paddy text-lg tracking-tight">KisanNet</span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {SIDEBAR_LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            const keyMap: Record<string, string> = { "Home": "home", "Advice": "advisory", "Schemes": "schemes", "Market Prices": "market", "Weather": "weatherInfo", "Profile": "profile" };
            const tKey = keyMap[label] || label.toLowerCase();
            return (
              <Link key={href} href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-2xl text-sm font-semibold transition-all ${
                  active ? "bg-paddy/10 text-paddy font-bold" : "text-soil/60 hover:bg-husk hover:text-paddy"
                }`}>
                <Icon size={18} strokeWidth={active ? 2.4 : 2} />
                <span>{t(tKey, label)}</span>
              </Link>
            );
          })}
        </nav>

        {/* Need Help Box */}
        <div className="p-4 pb-6 mt-auto">
          <div className="bg-[#FAF9F6] rounded-2xl p-3 flex items-start gap-3 border border-soil/10 mb-4 shadow-sm">
            <div className="w-8 h-8 rounded-full bg-paddy/15 flex items-center justify-center shrink-0">
              <Phone size={14} className="text-paddy" />
            </div>
            <div>
              <p className="text-xs font-bold text-paddy-dark">Need Help?</p>
              <p className="text-[10px] text-soil/60 font-medium">Talk to an expert</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-paddy-dark px-1">
            <MessageCircle size={16} className="cursor-pointer hover:text-paddy transition-colors" />
            <Youtube size={16} className="cursor-pointer hover:text-paddy transition-colors" />
            <Facebook size={16} className="cursor-pointer hover:text-paddy transition-colors" />
            <Instagram size={16} className="cursor-pointer hover:text-paddy transition-colors" />
          </div>
          <p className="text-left text-[10px] text-soil/40 font-medium mt-3 px-1">© 2026 KisanNet<br />Official APMC Live</p>
        </div>
      </aside>

      {/* ── MAIN AREA ── */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        
        {/* TOP NAVBAR */}
        <header className="shrink-0 flex items-center justify-between px-5 lg:px-8 py-3.5 bg-white border-b border-soil/10 z-10 sticky top-0 shadow-xs">
          <div className="flex items-center gap-3">
            <button onClick={() => setIsLanguageModalOpen(true)}
              className="flex items-center gap-1.5 border border-soil/15 rounded-full px-3 py-1.5 text-xs lg:text-sm font-semibold text-soil hover:bg-husk transition-colors cursor-pointer">
              <Globe size={15} /> {currentOption.nativeName} ▾
            </button>
            <div className="hidden sm:flex items-center gap-1.5 text-xs lg:text-sm font-medium text-soil/70 bg-[#FAF9F6] px-3 py-1 rounded-full border border-soil/10">
              <span className="text-base">{liveWeather?.conditionIcon || '🌤️'}</span>
              <span className="font-bold text-paddy-dark">{liveWeather ? `${liveWeather.temperature}°C` : '31°C'}</span>
              <span className="text-soil/50">{liveWeather?.conditionText || 'Partly Cloudy'}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={loadMarketPrices}
              title="Refresh Market Prices"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-soil/15 text-xs font-semibold text-soil/70 hover:text-paddy hover:bg-husk transition-colors">
              <RefreshCw size={13} className={loadingMarket ? "animate-spin text-paddy" : ""} />
              <span className="hidden sm:inline">Live Sync</span>
            </button>
            <div className="w-8 h-8 rounded-full overflow-hidden border-2 border-paddy/30 shadow-xs">
              <Image src={IMAGES.farmerPortrait} alt="Profile" width={32} height={32} className="object-cover w-full h-full" />
            </div>
          </div>
        </header>

        {/* PAGE CONTENT */}
        <div className="p-4 lg:p-8 flex flex-col gap-6 max-w-7xl mx-auto w-full pb-24 lg:pb-12">
          
          {/* Header Section */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold tracking-wide flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> {t('liveMandi', 'LIVE MANDI')}
                </span>
                <span className="text-xs font-medium text-soil/50">{t('officialAgmarknet', 'Official AGMARKNET')}</span>
              </div>
              <h1 className="text-2xl lg:text-3xl font-display font-black text-paddy-dark tracking-tight mt-1">{t('marketPricesTitle', 'Market Prices & Mandi Rates')}</h1>
              <p className="text-xs lg:text-sm text-soil/70 mt-0.5" dangerouslySetInnerHTML={{ __html: t('marketSubtitle', 'Real-time daily mandi rates per <strong>Quintal (100 kg)</strong> and per <strong>Kilo (Kg)</strong>') }}></p>
            </div>
            
            {/* Live Sync & Date Indicator */}
            <div className="flex items-center gap-3 self-start sm:self-auto bg-white px-3.5 py-2 rounded-xl border border-soil/15 shadow-xs">
              <Calendar size={15} className="text-paddy" />
              <div className="text-left">
                <p className="text-[11px] font-bold text-paddy-dark">{currentDateStr}</p>
                <p className="text-[10px] text-soil/50">{t('updated', 'Updated')}: {lastUpdatedTime || 'Today'}</p>
              </div>
            </div>
          </div>

          {/* ── FILTER & SEARCH TOOLBAR ── */}
          <div className="bg-white p-4 rounded-2xl border border-soil/15 shadow-sm flex flex-col gap-3">
            
            {/* Top row: Search + Dropdowns + Download */}
            <div className="flex flex-col lg:flex-row gap-3">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-soil/40" size={16} />
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('searchMarket', 'Search crop (e.g. Tomato, ఉల్లిపాయ, Cotton, Warangal)...')}
                  className="w-full h-11 pl-10 pr-10 rounded-xl border border-soil/15 text-sm bg-[#FAF9F6] focus:bg-white focus:outline-none focus:ring-2 focus:ring-paddy/20 focus:border-paddy transition-all" 
                />
                {searchQuery && (
                  <button 
                    onClick={() => setSearchQuery("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-soil/40 hover:text-soil p-1">
                    <X size={14} />
                  </button>
                )}
              </div>
              
              {/* Filter Dropdowns */}
              <div className="flex flex-wrap sm:flex-nowrap gap-2.5 items-center">
                {/* Commodity Dropdown */}
                <div className="relative min-w-[160px] flex-1 sm:flex-initial">
                  <select
                    value={selectedCommodity}
                    onChange={(e) => setSelectedCommodity(e.target.value)}
                    className="w-full h-11 pl-3.5 pr-8 rounded-xl border border-soil/15 bg-[#FAF9F6] text-xs font-bold text-paddy-dark focus:outline-none focus:ring-2 focus:ring-paddy/20 focus:border-paddy appearance-none cursor-pointer">
                    <option value="ALL">{t('allCrops', 'All Crops')} ({availableCommodities.length})</option>
                    {availableCommodities.map(comm => (
                      <option key={comm} value={comm}>{comm}</option>
                    ))}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-soil/40 pointer-events-none" />
                </div>

                {/* District Dropdown */}
                <div className="relative min-w-[150px] flex-1 sm:flex-initial">
                  <select
                    value={selectedDistrict}
                    onChange={(e) => setSelectedDistrict(e.target.value)}
                    className="w-full h-11 pl-3.5 pr-8 rounded-xl border border-soil/15 bg-[#FAF9F6] text-xs font-bold text-paddy-dark focus:outline-none focus:ring-2 focus:ring-paddy/20 focus:border-paddy appearance-none cursor-pointer">
                    <option value="ALL">{t('allDistricts', 'All Districts')} ({availableDistricts.length})</option>
                    {availableDistricts.map(dist => (
                      <option key={dist} value={dist}>{dist}</option>
                    ))}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-soil/40 pointer-events-none" />
                </div>

                {/* Price Display Mode Toggle */}
                <div className="flex items-center bg-[#FAF9F6] rounded-xl p-1 border border-soil/15 shrink-0">
                  <button 
                    onClick={() => setUnitMode('both')}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                      unitMode === 'both' ? 'bg-paddy text-white shadow-xs' : 'text-soil/60 hover:text-paddy'
                    }`}>
                    {t('bothUnits', 'Both')}
                  </button>
                  <button 
                    onClick={() => setUnitMode('kg')}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                      unitMode === 'kg' ? 'bg-paddy text-white shadow-xs' : 'text-soil/60 hover:text-paddy'
                    }`}>
                    {t('perKg', '₹/Kg')}
                  </button>
                  <button 
                    onClick={() => setUnitMode('qtl')}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                      unitMode === 'qtl' ? 'bg-paddy text-white shadow-xs' : 'text-soil/60 hover:text-paddy'
                    }`}>
                    {t('perQtl', '₹/Qtl')}
                  </button>
                </div>

                {/* CSV Download Button */}
                <button 
                  onClick={downloadCSV}
                  title="Download filtered prices as CSV"
                  className="h-11 px-4 rounded-xl border-2 border-paddy bg-paddy/5 text-xs font-bold text-paddy flex items-center gap-2 shrink-0 hover:bg-paddy hover:text-white transition-all cursor-pointer">
                  <Download size={15} /> <span className="hidden sm:inline">{t('exportCsv', 'Export CSV')}</span>
                </button>
              </div>
            </div>

            {/* Bottom row: Category filter chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs hide-scrollbar border-t border-soil/10 pt-2.5">
              <span className="text-[11px] font-bold text-soil/40 uppercase tracking-wider mr-1">{t('categories', 'Categories')}:</span>
              {['ALL', 'Vegetables', 'Grains', 'Pulses', 'Spices', 'Fruits', 'Commercial', 'Oilseeds'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1 rounded-full font-semibold transition-all shrink-0 cursor-pointer ${
                    selectedCategory === cat 
                      ? 'bg-paddy text-white shadow-xs' 
                      : 'bg-[#FAF9F6] text-soil/70 hover:bg-husk hover:text-paddy border border-soil/10'
                  }`}>
                  {cat === 'ALL' ? t('allCommodities', 'All Commodities') : cat}
                </button>
              ))}

              {(searchQuery || selectedCommodity !== 'ALL' || selectedDistrict !== 'ALL' || selectedCategory !== 'ALL') && (
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedCommodity("ALL");
                    setSelectedDistrict("ALL");
                    setSelectedCategory("ALL");
                  }}
                  className="text-xs font-bold text-red-500 hover:underline ml-auto flex items-center gap-1 shrink-0 cursor-pointer">
                  <X size={12} /> {t('clearFilters', 'Clear Filters')}
                </button>
              )}
            </div>
          </div>

          {/* ── TOP COMMODITY CARDS (WITH BOTH QUINTAL AND PER KG PRICES!) ── */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-paddy-dark flex items-center gap-1.5">
                <Sparkles size={15} className="text-amber-500" /> {t('featuredDailyPrices', 'Featured Daily Prices')}
              </h2>
              <span className="text-xs font-medium text-soil/50">
                {t('showing', 'Showing')} {Math.min(uniqueCropCards.length, showAllMarkets ? uniqueCropCards.length : 10)} {t('of', 'of')} {uniqueCropCards.length} {t('crops', 'crops')}
              </span>
            </div>

            <div className="flex overflow-x-auto gap-3.5 pb-2 -mx-4 px-4 lg:mx-0 lg:px-0 lg:grid lg:grid-cols-5 snap-x hide-scrollbar">
              {loadingMarket ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="min-w-[200px] lg:min-w-0 bg-white rounded-2xl p-4 shadow-sm border border-soil/10 flex flex-col items-center text-center animate-pulse">
                    <div className="w-16 h-16 bg-soil/10 rounded-xl mb-3"></div>
                    <div className="h-4 w-24 bg-soil/10 rounded mb-2"></div>
                    <div className="h-6 w-28 bg-soil/10 rounded mb-2"></div>
                    <div className="h-4 w-16 bg-soil/10 rounded"></div>
                  </div>
                ))
              ) : uniqueCropCards.length === 0 ? (
                <div className="col-span-5 bg-white rounded-2xl p-8 text-center text-soil/50 border border-soil/10">
                  {t('noCropsMatching', 'No crops matching your search filter.')}
                </div>
              ) : (
                (showAllMarkets ? uniqueCropCards : uniqueCropCards.slice(0, 10)).map((mandi) => (
                  <div key={mandi.id} className="min-w-[210px] lg:min-w-0 bg-white rounded-2xl p-4 shadow-sm border border-soil/10 flex flex-col items-center text-center snap-start hover:shadow-md transition-shadow relative overflow-hidden group">
                    
                    {/* Image with robust fallback */}
                    <div className="w-16 h-16 relative mb-2.5 rounded-xl overflow-hidden shadow-xs bg-husk/50">
                      <img 
                        src={mandi.imageUrl} 
                        alt={mandi.cropNameEn} 
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" 
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src = DEFAULT_CROP_IMAGE;
                        }}
                      />
                    </div>

                    {/* Crop Name */}
                    <h3 className="text-sm font-bold text-paddy-dark leading-tight line-clamp-1" title={mandi.cropNameEn}>
                      {mandi.cropNameEn}
                    </h3>
                    <p className="text-xs font-semibold text-paddy mt-0.5">
                      {mandi.cropNameTe}
                    </p>

                    {/* DUAL PRICING: PER KG & PER QUINTAL */}
                    <div className="mt-2.5 w-full bg-[#FAF9F6] py-1.5 px-2 rounded-xl border border-soil/10">
                      {unitMode !== 'qtl' && (
                        <div className="font-display text-base lg:text-lg font-black text-paddy-dark">
                          ₹{mandi.pricePerKg} <span className="text-xs font-bold text-emerald-700">/ kg</span>
                        </div>
                      )}
                      {unitMode !== 'kg' && (
                        <div className={`text-[11px] font-semibold text-soil/70 ${unitMode === 'both' ? 'mt-0.5' : 'font-display text-base font-bold text-paddy-dark'}`}>
                          ₹{mandi.modalPrice.toLocaleString()} <span className="text-[10px] font-normal text-soil/50">/ quintal</span>
                        </div>
                      )}
                    </div>

                    {/* Trend */}
                    <div className={`mt-2 flex items-center justify-center gap-1 text-[11px] font-bold ${
                      mandi.trend === 'up' ? 'text-emerald-600' : mandi.trend === 'down' ? 'text-red-500' : 'text-slate-500'
                    }`}>
                      {mandi.trend === 'up' ? <TrendingUp size={12} /> : mandi.trend === 'down' ? <TrendingDown size={12} /> : <Minus size={12} />}
                      {mandi.currentPrice > 0 ? Math.abs((mandi.priceChange / mandi.currentPrice) * 100).toFixed(1) : 0}%
                      <span className="text-[10px] font-normal text-soil/40 ml-0.5">{t('today', 'today')}</span>
                    </div>

                    {/* Market & Date Subtext */}
                    <p className="text-[10px] text-soil/50 truncate max-w-[180px] mt-1.5" title={mandi.marketNameEn}>
                      📍 {mandi.marketNameEn}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ── DETAILED DATA TABLE ── */}
          <div className="bg-white rounded-2xl border border-soil/15 shadow-sm overflow-hidden flex flex-col">
            
            {/* Table Header Controls */}
            <div className="p-4 border-b border-soil/10 bg-[#FAF9F6] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-paddy-dark">{t('allMandiRecords', 'All Mandi Market Records')} ({filteredData.length} {t('entries', 'entries')})</h3>
                <p className="text-xs text-soil/50">{t('sortHint', 'Click on any column header to sort ascending/descending')}</p>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-soil/60">
                <span>{t('displaying', 'Displaying')}:</span>
                <span className="bg-white px-2.5 py-1 rounded-lg border border-soil/15 font-bold text-paddy">
                  {unitMode === 'both' ? t('bothUnitsLabel', '₹ / Quintal & ₹ / Kg') : unitMode === 'kg' ? t('perKg', '₹ / Kg') : t('perQtl', '₹ / Quintal')}
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-[#FAF9F6] border-b border-soil/15 text-[11px] font-bold text-soil/60 uppercase tracking-wider select-none">
                  <tr>
                    {/* Commodity */}
                    <th onClick={() => handleSort('crop')} className="px-5 py-3.5 cursor-pointer hover:text-paddy transition-colors">
                      <div className="flex items-center gap-1">
                        <span>{t('commodity', 'Commodity')}</span>
                        {sortField === 'crop' ? (sortOrder === 'asc' ? <ArrowUp size={12} className="text-paddy" /> : <ArrowDown size={12} className="text-paddy" />) : <ArrowUpDown size={12} className="opacity-40" />}
                      </div>
                    </th>

                    {/* Market */}
                    <th onClick={() => handleSort('market')} className="px-5 py-3.5 cursor-pointer hover:text-paddy transition-colors">
                      <div className="flex items-center gap-1">
                        <span>{t('marketMandi', 'Market (Mandi)')}</span>
                        {sortField === 'market' ? (sortOrder === 'asc' ? <ArrowUp size={12} className="text-paddy" /> : <ArrowDown size={12} className="text-paddy" />) : <ArrowUpDown size={12} className="opacity-40" />}
                      </div>
                    </th>

                    {/* District */}
                    <th onClick={() => handleSort('district')} className="px-5 py-3.5 cursor-pointer hover:text-paddy transition-colors">
                      <div className="flex items-center gap-1">
                        <span>{t('district', 'District')}</span>
                        {sortField === 'district' ? (sortOrder === 'asc' ? <ArrowUp size={12} className="text-paddy" /> : <ArrowDown size={12} className="text-paddy" />) : <ArrowUpDown size={12} className="opacity-40" />}
                      </div>
                    </th>

                    {/* Price per KG */}
                    <th onClick={() => handleSort('pricePerKg')} className="px-5 py-3.5 text-right cursor-pointer hover:text-paddy transition-colors bg-emerald-50/50">
                      <div className="flex items-center justify-end gap-1">
                        <span>{t('pricePerKilo', 'Price / Kilo')}</span>
                        <span className="text-[9px] font-bold text-emerald-700 lowercase">(₹/kg)</span>
                        {sortField === 'pricePerKg' ? (sortOrder === 'asc' ? <ArrowUp size={12} className="text-paddy" /> : <ArrowDown size={12} className="text-paddy" />) : <ArrowUpDown size={12} className="opacity-40" />}
                      </div>
                    </th>

                    {/* Modal Price */}
                    <th onClick={() => handleSort('modalPrice')} className="px-5 py-3.5 text-right cursor-pointer hover:text-paddy transition-colors">
                      <div className="flex items-center justify-end gap-1">
                        <span>{t('modalPrice', 'Modal Price')}</span>
                        <span className="text-[9px] normal-case text-soil/40">(₹/qtl)</span>
                        {sortField === 'modalPrice' ? (sortOrder === 'asc' ? <ArrowUp size={12} className="text-paddy" /> : <ArrowDown size={12} className="text-paddy" />) : <ArrowUpDown size={12} className="opacity-40" />}
                      </div>
                    </th>

                    {/* Min / Max Range */}
                    <th className="px-5 py-3.5 text-right">
                      <span>{t('minMax', 'Min - Max')}</span>
                      <span className="text-[9px] block text-soil/40 normal-case">(₹ / quintal)</span>
                    </th>

                    {/* Change */}
                    <th onClick={() => handleSort('change')} className="px-5 py-3.5 cursor-pointer hover:text-paddy transition-colors">
                      <div className="flex items-center gap-1">
                        <span>{t('priceChange', 'Change')}</span>
                        {sortField === 'change' ? (sortOrder === 'asc' ? <ArrowUp size={12} className="text-paddy" /> : <ArrowDown size={12} className="text-paddy" />) : <ArrowUpDown size={12} className="opacity-40" />}
                      </div>
                    </th>

                    {/* Trend Graph */}
                    <th className="px-5 py-3.5 text-center">{t('trend', 'Trend')}</th>

                    {/* Date */}
                    <th className="px-5 py-3.5 text-right">{t('arrivalDate', 'Arrival Date')}</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-soil/10 text-paddy-dark">
                  {loadingMarket ? (
                    Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i} className="animate-pulse bg-white">
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-28"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-24"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-20"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-16 ml-auto"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-16 ml-auto"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-20 ml-auto"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-12"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-14 mx-auto"></div></td>
                        <td className="px-5 py-3.5"><div className="h-4 bg-soil/10 rounded w-16 ml-auto"></div></td>
                      </tr>
                    ))
                  ) : filteredData.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-5 py-12 text-center text-soil/50 bg-white">
                        <p className="font-bold text-base text-soil/70">No Mandi Records Found</p>
                        <p className="text-xs text-soil/40 mt-1">Try clearing your search query or selecting &quot;All Commodities&quot;.</p>
                      </td>
                    </tr>
                  ) : (
                    filteredData.map((mandi) => (
                      <tr key={mandi.id} className="hover:bg-husk/25 transition-colors">
                        {/* Commodity with thumbnail */}
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-3">
                            <img 
                              src={mandi.imageUrl} 
                              alt={mandi.cropNameEn} 
                              className="w-9 h-9 rounded-xl object-cover shrink-0 border border-soil/10 shadow-xs" 
                              onError={(e) => {
                                e.currentTarget.onerror = null;
                                e.currentTarget.src = DEFAULT_CROP_IMAGE;
                              }}
                            />
                            <div>
                              <div className="font-bold text-paddy-dark leading-tight" title={mandi.cropNameEn}>
                                {mandi.cropNameEn}
                              </div>
                              <div className="text-[11px] font-semibold text-paddy">
                                {mandi.cropNameTe}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Market Name */}
                        <td className="px-5 py-3 text-soil font-medium truncate max-w-[140px]" title={mandi.marketNameEn}>
                          {mandi.marketNameEn}
                        </td>

                        {/* District */}
                        <td className="px-5 py-3 text-soil/80 font-medium truncate max-w-[120px]" title={mandi.district}>
                          <span className="bg-soil/5 px-2 py-0.5 rounded-md text-xs font-semibold text-soil/70 border border-soil/10">
                            {mandi.district}
                          </span>
                        </td>

                        {/* Price per KG (High Visibility) */}
                        <td className="px-5 py-3 text-right bg-emerald-50/30">
                          <span className="inline-block px-2 py-0.5 rounded-md bg-emerald-100/80 text-emerald-800 font-display font-black text-sm">
                            ₹{mandi.pricePerKg.toFixed(1)} <span className="text-[10px] font-bold text-emerald-700">/kg</span>
                          </span>
                        </td>

                        {/* Modal Price */}
                        <td className="px-5 py-3 text-right font-display font-black text-sm text-paddy-dark">
                          ₹{mandi.modalPrice.toLocaleString()}
                        </td>

                        {/* Min / Max Range */}
                        <td className="px-5 py-3 text-right text-xs font-medium text-soil/60">
                          ₹{mandi.minPrice.toLocaleString()} - ₹{mandi.maxPrice.toLocaleString()}
                        </td>

                        {/* Change */}
                        <td className="px-5 py-3">
                          <span className={`inline-flex items-center gap-1 text-xs font-bold ${
                            mandi.trend === 'up' ? 'text-emerald-600' : mandi.trend === 'down' ? 'text-red-500' : 'text-slate-500'
                          }`}>
                            {mandi.trend === 'up' ? <TrendingUp size={12} /> : mandi.trend === 'down' ? <TrendingDown size={12} /> : <Minus size={12} />}
                            {mandi.currentPrice > 0 ? Math.abs((mandi.priceChange / mandi.currentPrice) * 100).toFixed(1) : 0}%
                          </span>
                        </td>

                        {/* Sparkline Trend */}
                        <td className="px-5 py-3 text-center">
                          <Sparkline trend={mandi.trend} />
                        </td>

                        {/* Arrival Date */}
                        <td className="px-5 py-3 text-right text-xs font-medium text-soil/60">
                          {mandi.date}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            
            {/* Table Footer */}
            <div className="bg-[#FAF9F6] border-t border-soil/15 px-5 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs text-soil/60">
                <div className="w-4 h-4 rounded-full border border-soil/20 flex items-center justify-center font-serif italic text-[10px] bg-white text-paddy shrink-0">i</div>
                <span>{t('mandiNote', 'Note: 1 Quintal = 100 Kilograms. Prices are officially sourced from AGMARKNET / State Agriculture Marketing Boards.')}</span>
              </div>
              
              <button 
                onClick={() => setShowAllMarkets(!showAllMarkets)}
                className="text-xs font-bold text-paddy hover:text-paddy-dark hover:underline flex items-center gap-1 cursor-pointer bg-transparent border-none shrink-0">
                {showAllMarkets ? t('showTop10', 'Show Top 10 Only ➔') : `${t('showAll', 'Show All')} ${uniqueCropCards.length} ${t('crops', 'Crops ➔')}`}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

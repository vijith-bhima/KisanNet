"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { 
  Home as HomeIcon, MessageCircle, Landmark, TrendingUp as MarketIcon, Cloud, 
  UserCircle2, Phone, Bell, Globe, Search, Youtube, Facebook, Instagram,
  ChevronDown, ArrowRight, Grid, IndianRupee, Sprout, Droplets, Shield,
  Bird, MoreHorizontal, Users, Calendar, CheckCircle2, Headset
} from 'lucide-react';
import { IMAGES } from '@/lib/images';
import logo from '@/assets/image.png';
import { fetchLiveWeather, LiveWeatherData, autoDetectLocation } from '@/utils/weatherService';
import { useLanguage } from '@/context/LanguageContext';

const SIDEBAR_LINKS = [
  { href: "/", label: "Home", labelTe: "హోమ్", icon: HomeIcon },
  { href: "/advisory", label: "Advice", labelTe: "సలహా", icon: MessageCircle },
  { href: "/schemes", label: "Schemes", labelTe: "పథకాలు", icon: Landmark },
  { href: "/market", label: "Market Prices", labelTe: "మార్కెట్ ధరలు", icon: MarketIcon },
  { href: "/weather", label: "Weather", labelTe: "వాతావరణం", icon: Cloud },
  { href: "/profile", label: "Profile", labelTe: "ప్రొఫైల్", icon: UserCircle2 },
];

const CATEGORIES = [
  { id: 'all', label: 'All Schemes', icon: Grid, active: true },
  { id: 'income', label: 'Income Support', icon: IndianRupee },
  { id: 'crop', label: 'Crop Support', icon: Sprout },
  { id: 'irrigation', label: 'Irrigation', icon: Droplets },
  { id: 'insurance', label: 'Insurance', icon: Shield },
  { id: 'livestock', label: 'Livestock', icon: Bird },
  { id: 'more', label: 'More', icon: MoreHorizontal },
];

const POPULAR_SCHEMES = [
  {
    title: "PM-KISAN Samman Nidhi Yojana",
    desc: "అర్హులైన రైతులకు ప్రతి సంవత్సరానికి ₹6,000 ఆర్థిక సహాయం.",
    icon: IndianRupee,
    iconColor: "text-emerald-600",
    iconBg: "bg-emerald-100",
    link: "https://pmkisan.gov.in/",
    tags: [{ label: "Income Support", color: "text-emerald-600 bg-emerald-50" }, { label: "Central Scheme", color: "text-blue-600 bg-blue-50" }]
  },
  {
    title: "Pradhan Mantri Krishi Sinchayee Yojana",
    desc: "సాగునీటి సౌకర్యాలు మరియు నీటి సంరక్షణ కల్పించడం.",
    icon: Droplets,
    iconColor: "text-blue-500",
    iconBg: "bg-blue-100",
    link: "https://pmksy.gov.in/",
    tags: [{ label: "Irrigation", color: "text-blue-500 bg-blue-50" }, { label: "Central Scheme", color: "text-blue-600 bg-blue-50" }]
  },
  {
    title: "PM Fasal Bima Yojana",
    desc: "పంట నష్టానికి బీమా సాయం అందించడం.",
    icon: Shield,
    iconColor: "text-purple-600",
    iconBg: "bg-purple-100",
    link: "https://pmfby.gov.in/",
    tags: [{ label: "Insurance", color: "text-purple-600 bg-purple-50" }, { label: "Central Scheme", color: "text-blue-600 bg-blue-50" }]
  },
  {
    title: "eNAM (National Agriculture Market)",
    desc: "ఆన్‌లైన్ ద్వారా దేశవ్యాప్తంగా మార్కెట్‌లో అమ్ముకునే అవకాశం.",
    icon: Sprout,
    iconColor: "text-orange-500",
    iconBg: "bg-orange-100",
    link: "https://enam.gov.in/",
    tags: [{ label: "Market Access", color: "text-orange-500 bg-orange-50" }, { label: "Central Scheme", color: "text-blue-600 bg-blue-50" }]
  },
  {
    title: "Pashu Kisan Credit Card Yojana",
    desc: "పశుపోషణకు రుణ సదుపాయం అందిస్తుంది.",
    icon: Bird,
    iconColor: "text-amber-700",
    iconBg: "bg-amber-100",
    link: "https://www.myscheme.gov.in/schemes/pks",
    tags: [{ label: "Livestock", color: "text-amber-700 bg-amber-50" }, { label: "Central Scheme", color: "text-blue-600 bg-blue-50" }]
  },
  {
    title: "Rythu Samanvaya Abhivruddhi Scheme",
    desc: "రైతు సంఘాల అభివృద్ధికి ఆర్థిక సహాయం.",
    icon: Users,
    iconColor: "text-rose-500",
    iconBg: "bg-rose-100",
    link: "https://www.myscheme.gov.in/",
    tags: [{ label: "Others", color: "text-rose-500 bg-rose-50" }, { label: "State Scheme", color: "text-purple-600 bg-purple-50" }]
  }
];

export default function SchemesPage() {
  const [liveWeather, setLiveWeather] = useState<LiveWeatherData | null>(null);
  const [schemes, setSchemes] = useState(POPULAR_SCHEMES);
  const [isLiveLoading, setIsLiveLoading] = useState(true);
  const [liveSchemes, setLiveSchemes] = useState<any[]>([]);
  const { currentOption, setIsLanguageModalOpen, t, language } = useLanguage();
  const pathname = usePathname();

  useEffect(() => {
    autoDetectLocation()
      .then(loc => fetchLiveWeather(loc.lat, loc.lon, { name: loc.name, city: loc.city, state: loc.state, country: loc.country }))
      .then(data => setLiveWeather(data))
      .catch(err => {
        // Fallback
        fetchLiveWeather(16.3067, 80.4365).then(setLiveWeather).catch(() => {});
      });

    // Fetch real schemes from backend
    const fetchRealSchemes = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/schemes");
        if (res.ok) {
          const data = await res.json();
          // Transform backend data to match UI layout format
          const formattedSchemes = data.map((item: any) => ({
            title: item.name,
            desc: item.description,
            icon: Landmark, // default icon for fetched schemes
            iconColor: item.isLive ? "text-red-500" : "text-blue-600",
            iconBg: item.isLive ? "bg-red-100" : "bg-blue-100",
            isLive: item.isLive,
            link: item.source_url || "https://www.myscheme.gov.in/",
            tags: [
              { label: item.isLive ? "Alert" : "Government", color: item.isLive ? "text-red-600 bg-red-50" : "text-blue-600 bg-blue-50" },
              { label: "Central Scheme", color: "text-emerald-600 bg-emerald-50" }
            ]
          }));
          setSchemes(prev => {
            // Keep the beautiful default UI cards, but inject any new real-time/live schemes at the very top!
            const newLiveSchemes = formattedSchemes.filter((s: any) => s.isLive);
            return [...newLiveSchemes, ...prev];
          });
          setIsLiveLoading(false);
        }
      } catch (err) {
        console.error("Error fetching real schemes:", err);
      }
    };
    
    fetchRealSchemes();
  }, []);

  return (
    <div className="flex flex-col lg:flex-row h-[100dvh] w-full bg-[#F9F7EF] text-[#2D3A32] font-sans overflow-hidden">
      
      {/* ── LEFT SIDEBAR (Desktop Only) ── */}
      <aside className="hidden lg:flex w-44 shrink-0 flex-col bg-white border-r border-soil/10 shadow-soft z-20 h-full">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-soil/10">
          <Image src={logo} alt="KisanNet" className="w-8 h-8 rounded-full object-contain" />
          <span className="font-display font-black text-paddy text-base">KisanNet</span>
        </div>

        {/* Nav links */}
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

        {/* Need Help */}
        <div className="p-4 pb-6 mt-auto">
          <div className="bg-white rounded-2xl p-3 flex items-start gap-3 shadow-card border border-soil/10 mb-6">
            <div className="w-8 h-8 rounded-full bg-paddy/15 flex items-center justify-center shrink-0">
              <Phone size={14} className="text-paddy" />
            </div>
            <div>
              <p className="text-xs font-bold text-paddy-dark">Need Help?</p>
              <p className="text-[10px] text-soil/60 font-medium">Talk to an expert</p>
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

      {/* ── MAIN AREA ── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        
        {/* TOP NAVBAR */}
        <header className="shrink-0 flex items-center justify-between px-4 lg:px-7 py-2 lg:py-2.5 bg-white border-b border-soil/10 z-10 sticky top-0">
          <div className="flex items-center gap-3">
            {/* Language selector */}
            <button onClick={() => setIsLanguageModalOpen(true)}
              className="flex items-center gap-1.5 border border-soil/15 rounded-full px-3 py-1.5 text-sm font-semibold text-soil hover:bg-husk transition-colors">
              <Globe size={16} /> {currentOption.nativeName} ▾
            </button>
            <div className="hidden sm:flex items-center gap-1.5 text-sm font-medium text-soil/70">
              <span className="text-base">{liveWeather?.conditionIcon || '🌤️'}</span>
              <span className="font-bold text-paddy-dark">{liveWeather ? `${liveWeather.temperature}°C` : '30°C'}</span>
              <span className="text-soil/50">{liveWeather?.conditionText || 'Overcast Sky'}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="w-9 h-9 rounded-full border border-soil/10 flex items-center justify-center hover:bg-husk transition-colors relative">
              <Bell size={18} className="text-soil/60" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
            </button>
            <div className="w-9 h-9 rounded-full overflow-hidden border-2 border-paddy/30">
              <Image src={IMAGES.farmerPortrait} alt="Profile" width={36} height={36} className="object-cover w-full h-full" />
            </div>
          </div>
        </header>

        {/* SCROLLABLE PAGE CONTENT */}
        <div className="flex-1 overflow-y-auto bg-white/50">
          <div className="max-w-7xl mx-auto p-4 lg:p-8">
            
            {/* Header section */}
            <div className="mb-6">
              <h1 className="text-3xl lg:text-4xl font-black text-paddy-dark font-display tracking-tight mb-2">{t('schemes')}</h1>
              <p className="text-soil/70 font-medium">{t('schemesSubtitle', "Government schemes and programs for farmers' welfare and development.")}</p>
            </div>

            {/* Category Filters */}
            <div className="flex items-center gap-3 overflow-x-auto pb-4 mb-2 scrollbar-hide">
              {CATEGORIES.map(cat => (
                <button key={cat.id} className={`flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap text-sm font-bold border transition-colors ${cat.active ? 'bg-paddy-dark text-white border-paddy-dark shadow-sm' : 'bg-white border-soil/15 text-soil hover:border-paddy hover:text-paddy'}`}>
                  <cat.icon size={16} />
                  {cat.label}
                </button>
              ))}
            </div>

            {/* MAIN GRID LAYOUT */}
            <div className="flex flex-col xl:flex-row gap-6 items-start mt-2">
              
              {/* LEFT COLUMN (70%) */}
              <div className="w-full xl:w-[68%] flex flex-col gap-8">
                
                {/* Featured Scheme Hero Card */}
                <div className="relative rounded-[2rem] bg-gradient-to-r from-[#E6F3EA] to-[#F3F8F2] border border-paddy/20 overflow-hidden shadow-sm flex flex-col sm:flex-row min-h-[320px]">
                  {/* Text Content */}
                  <div className="p-8 lg:p-10 flex-1 relative z-10 flex flex-col justify-center max-w-lg">
                    <span className="inline-flex items-center gap-1.5 bg-paddy text-white text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full w-max mb-4">
                      <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> {t('featuredScheme', 'FEATURED SCHEME')}
                    </span>
                    <h2 className="text-2xl lg:text-3xl font-black text-paddy-dark font-display mb-3 leading-tight">{t('pmKisanTitle', 'PM-KISAN Samman Nidhi Yojana')}</h2>
                    <p className="text-soil font-medium mb-6">
                      {t('pmKisanDesc', 'అర్హులైన రైతులకు ప్రతి సంవత్సరం ₹6,000 ఆర్థిక సహాయం 3 విడతలుగా నేరుగా వారి బ్యాంక్ ఖాతాలో జమ చేయబడుతుంది.')}
                    </p>
                    
                    <div className="flex flex-wrap items-center gap-6 lg:gap-10 mb-8">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-paddy/10 flex items-center justify-center text-paddy">
                          <Users size={18} />
                        </div>
                        <div>
                          <p className="text-[11px] font-bold text-soil/60 uppercase tracking-wide">{t('eligibility', 'అర్హత')}</p>
                          <p className="text-sm font-bold text-paddy-dark">{t('smallFarmers', 'సన్న, చిన్న రైతులు')}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-turmeric/10 flex items-center justify-center text-turmeric-dark">
                          <IndianRupee size={18} />
                        </div>
                        <div>
                          <p className="text-[11px] font-bold text-soil/60 uppercase tracking-wide">{t('assistanceAmount', 'సాయం మొత్తం')}</p>
                          <p className="text-sm font-bold text-paddy-dark">{t('pmKisanAmount', '₹6,000 / సంవత్సరం')}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                          <Calendar size={18} />
                        </div>
                        <div>
                          <p className="text-[11px] font-bold text-soil/60 uppercase tracking-wide">{t('installments', 'విడతలు')}</p>
                          <p className="text-sm font-bold text-paddy-dark">{t('pmKisanInstallments', 'ప్రతి 4 నెలలకు ఒకసారి')}</p>
                        </div>
                      </div>
                    </div>

                    <button onClick={() => window.open("https://pmkisan.gov.in/", "_blank")} className="bg-paddy-dark hover:bg-paddy text-white rounded-2xl px-6 py-3 font-bold text-sm w-max flex items-center gap-2 transition-all shadow-md hover:-translate-y-0.5">
                      {t('viewDetails', 'View Details')} <ArrowRight size={16} />
                    </button>
                  </div>
                  
                  {/* Image Background for Desktop/Tablet */}
                  <div className="hidden sm:block absolute right-0 top-0 bottom-0 w-1/2 overflow-hidden mask-image-gradient">
                    <img 
                      src="https://images.unsplash.com/photo-1595804595237-727533036814?auto=format&fit=crop&q=80&w=1200" 
                      alt="Farmers" 
                      className="w-full h-full object-cover object-left"
                    />
                    <div className="absolute inset-0 bg-gradient-to-r from-[#E6F3EA] via-transparent to-transparent"></div>
                  </div>
                </div>

                {/* Popular Schemes */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-paddy-dark font-display">{t('popularSchemes', 'Popular Schemes')}</h3>
                    <a href="#" className="text-sm font-bold text-paddy flex items-center gap-1 hover:underline">
                      {t('viewAllSchemes', 'View All Schemes')} <ArrowRight size={14} />
                    </a>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-5">
                    {[...liveSchemes, ...schemes].map((scheme, i) => (
                      <div key={i} className={`bg-white rounded-[1.5rem] p-5 shadow-card border ${scheme.isLive ? 'border-red-400/50 relative overflow-hidden' : 'border-soil/5'} flex flex-col h-full hover:border-paddy/30 transition-all hover:shadow-md cursor-pointer group`}>
                        {scheme.isLive && (
                          <div className="absolute top-0 right-0 bg-red-500 text-white text-[9px] font-bold px-3 py-1 rounded-bl-xl uppercase tracking-widest flex items-center gap-1.5 shadow-sm">
                            <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
                            {t('liveUpdate', 'Live Update')}
                          </div>
                        )}
                        <div className="flex items-start gap-4 mb-4">
                          <div className={`w-12 h-12 rounded-2xl ${scheme.iconBg} ${scheme.iconColor} flex items-center justify-center shrink-0`}>
                            <scheme.icon size={22} />
                          </div>
                          <div className="pt-1">
                            <h4 className="font-bold text-paddy-dark leading-snug group-hover:text-paddy transition-colors pr-2">{scheme.title}</h4>
                            <p className="text-[13px] text-soil/70 mt-1">{scheme.desc}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 mb-5 mt-auto">
                          {scheme.tags.map((tag: any, j: number) => (
                            <span key={j} className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${tag.color}`}>
                              {tag.label}
                            </span>
                          ))}
                        </div>

                        <div className="flex items-center gap-3 pt-4 border-t border-soil/5">
                          <button 
                            onClick={() => window.open(scheme.link || 'https://www.myscheme.gov.in/', '_blank')}
                            className="flex-1 py-2.5 text-sm font-bold text-soil hover:text-paddy flex items-center justify-center gap-1.5 transition-colors"
                          >
                            {t('viewDetails', 'View Details')} <ArrowRight size={14} />
                          </button>
                          <button 
                            onClick={() => window.open(scheme.link || 'https://www.myscheme.gov.in/', '_blank')}
                            className="flex-1 py-2.5 text-sm font-bold text-paddy-dark border border-soil/15 rounded-xl hover:bg-paddy-dark hover:text-white hover:border-paddy-dark transition-all"
                          >
                            {t('applyNow', 'Apply Now')}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>

              {/* RIGHT COLUMN (30%) */}
              <div className="w-full xl:w-[32%] flex flex-col gap-6">
                
                {/* Find Schemes for You Widget */}
                <div className="bg-paddy-dark rounded-[1.5rem] p-6 shadow-md text-white relative overflow-hidden">
                  {/* Decorative background circle */}
                  <div className="absolute -top-24 -right-24 w-48 h-48 bg-white/5 rounded-full blur-2xl"></div>
                  
                  <h3 className="text-lg font-bold font-display mb-1 relative z-10">{t('findSchemes', 'Find Schemes for You')}</h3>
                  <p className="text-sm text-white/70 mb-6 relative z-10">{t('getSchemesProfile', 'Get schemes based on your profile')}</p>

                  <div className="space-y-3 relative z-10">
                    <div className="bg-white rounded-xl flex items-center px-4 py-3 cursor-pointer hover:shadow-md transition-shadow">
                      <Landmark className="text-soil/40 w-5 h-5 mr-3" />
                      <span className="text-soil/80 font-bold text-sm flex-1">{t('selectState', 'Select State')}</span>
                      <ChevronDown className="text-soil/50 w-4 h-4" />
                    </div>
                    <div className="bg-white rounded-xl flex items-center px-4 py-3 cursor-pointer hover:shadow-md transition-shadow">
                      <HomeIcon className="text-soil/40 w-5 h-5 mr-3" />
                      <span className="text-soil/80 font-bold text-sm flex-1">{t('selectDistrict', 'Select District')}</span>
                      <ChevronDown className="text-soil/50 w-4 h-4" />
                    </div>
                    <div className="bg-white rounded-xl flex items-center px-4 py-3 cursor-pointer hover:shadow-md transition-shadow">
                      <Grid className="text-soil/40 w-5 h-5 mr-3" />
                      <span className="text-soil/80 font-bold text-sm flex-1">{t('selectCategory', 'Select Category')}</span>
                      <ChevronDown className="text-soil/50 w-4 h-4" />
                    </div>

                    <button className="w-full bg-[#E6F3EA] text-paddy-dark hover:bg-white hover:shadow-lg font-bold py-3.5 rounded-xl mt-3 flex items-center justify-center gap-2 transition-all">
                      <Search size={18} /> {t('findSchemes', 'Find Schemes')}
                    </button>
                  </div>
                </div>

                {/* How to Apply Widget */}
                <div className="bg-[#FEF9F0] border border-turmeric/20 rounded-[1.5rem] p-6">
                  <h3 className="text-lg font-bold text-paddy-dark font-display mb-6">{t('howToApply', 'How to Apply?')}</h3>
                  
                  <div className="relative border-l-2 border-turmeric/30 ml-3 space-y-7">
                    <div className="relative pl-6">
                      <div className="absolute -left-[11px] top-0 w-5 h-5 rounded-full bg-[#FEF9F0] border-2 border-turmeric flex items-center justify-center text-[10px] font-bold text-turmeric-dark shadow-sm">1</div>
                      <h4 className="font-bold text-paddy-dark text-[13px]">{t('checkEligibility', 'Check Eligibility')}</h4>
                      <p className="text-xs text-soil/60 mt-1">{t('checkEligibilityDesc', 'Check if you are eligible for the scheme')}</p>
                    </div>
                    <div className="relative pl-6">
                      <div className="absolute -left-[11px] top-0 w-5 h-5 rounded-full bg-[#FEF9F0] border-2 border-turmeric flex items-center justify-center text-[10px] font-bold text-turmeric-dark shadow-sm">2</div>
                      <h4 className="font-bold text-paddy-dark text-[13px]">{t('applyOnlineOffline', 'Apply Online / Offline')}</h4>
                      <p className="text-xs text-soil/60 mt-1">{t('applyOnlineOfflineDesc', 'Submit the application online or at nearest center')}</p>
                    </div>
                    <div className="relative pl-6">
                      <div className="absolute -left-[11px] top-0 w-5 h-5 rounded-full bg-[#FEF9F0] border-2 border-turmeric flex items-center justify-center text-[10px] font-bold text-turmeric-dark shadow-sm">3</div>
                      <h4 className="font-bold text-paddy-dark text-[13px]">{t('trackApplication', 'Track Application')}</h4>
                      <p className="text-xs text-soil/60 mt-1">{t('trackApplicationDesc', 'Track your application status online')}</p>
                    </div>
                    <div className="relative pl-6">
                      <div className="absolute -left-[11px] top-0 w-5 h-5 rounded-full bg-[#FEF9F0] border-2 border-turmeric flex items-center justify-center text-[10px] font-bold text-turmeric-dark shadow-sm">4</div>
                      <h4 className="font-bold text-paddy-dark text-[13px]">{t('getBenefits', 'Get Benefits')}</h4>
                      <p className="text-xs text-soil/60 mt-1">{t('getBenefitsDesc', 'Receive benefits directly')}</p>
                    </div>
                  </div>

                  <a href="#" className="inline-flex items-center gap-1.5 text-sm font-bold text-turmeric-dark hover:text-paddy-dark mt-6 pl-3 transition-colors">
                    {t('viewGuide', 'View Guide')} <ArrowRight size={14} />
                  </a>
                </div>

                {/* Need Help Card */}
                <div className="bg-[#EEF5EF] rounded-[1.5rem] p-6 flex flex-col justify-center border border-paddy/10">
                  <div className="flex gap-4 items-center">
                    <div className="w-14 h-14 rounded-full bg-paddy-dark flex items-center justify-center overflow-hidden shrink-0 shadow-md">
                      <Headset className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-paddy-dark mb-0.5 text-sm">{t('needHelpTitle', 'సహాయం కావాలా?')}</h3>
                      <p className="text-xs text-soil/70 leading-relaxed font-medium">{t('needHelpDesc', 'మా సపోర్ట్ బృందం మీకు సహాయం చేయడానికి సిద్ధంగా ఉంది.')}</p>
                    </div>
                  </div>
                  <a href="tel:1800123456" className="flex items-center justify-center gap-2 bg-white text-paddy-dark border border-paddy/20 px-4 py-3 rounded-xl text-sm font-bold mt-5 hover:border-paddy shadow-sm transition-all hover:bg-[#F9F7EF]">
                    <Phone size={14} /> 1800 123 456
                  </a>
                  <p className="text-[10px] text-center text-soil/50 font-bold mt-3">{t('supportHours', '(ఉదయం 9 AM - సాయంత్రం 6 PM)')}</p>
                </div>

              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
}

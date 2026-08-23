"use client";
import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { auth } from '@/lib/firebase';
import { onAuthStateChanged, User } from 'firebase/auth';
import {
  Home as HomeIcon, MessageCircle, Landmark, TrendingUp as MarketIcon, Cloud,
  UserCircle2, Phone, Bell, Mic, CloudSun, Stethoscope,
  BadgeIndianRupee, Volume2, VolumeX, TrendingUp, TrendingDown, Minus,
  Newspaper, ChevronRight, Users, Store, FileText, Facebook, Instagram, Youtube, Globe
} from "lucide-react";
import VoiceOrb from "@/components/VoiceOrb";
import QuickCard from "@/components/QuickCard";
import { IMAGES } from "@/lib/images";
import logo from "@/assets/image.png";
import { MANDI_PRICES } from "@/lib/farmData";
import { fetchLiveWeather, LiveWeatherData, autoDetectLocation } from "@/utils/weatherService";
import { VoiceAssistantModal } from "@/components/VoiceAssistantModal";
import { useLanguage } from "@/context/LanguageContext";
import { speakInLanguage, stopSpeech } from "@/utils/speech";

const SIDEBAR_LINKS = [
  { href: "/", label: "Home", labelTe: "హోమ్", icon: HomeIcon },
  { href: "/advisory", label: "Advice", labelTe: "సలహా", icon: MessageCircle },
  { href: "/schemes", label: "Schemes", labelTe: "పథకాలు", icon: Landmark },
  { href: "/market", label: "Market Prices", labelTe: "మార్కెట్ ధరలు", icon: MarketIcon },
  { href: "/weather", label: "Weather", labelTe: "వాతావరణం", icon: Cloud },
  { href: "/profile", label: "Profile", labelTe: "ప్రొఫైల్", icon: UserCircle2 },
];

export default function Home() {
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [voicePrompt, setVoicePrompt] = useState("");
  const [liveWeather, setLiveWeather] = useState<LiveWeatherData | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [isGuest, setIsGuest] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const { language, setIsLanguageModalOpen, currentOption, t } = useLanguage();
  const pathname = usePathname();
  const router = useRouter();
  const topMandi = MANDI_PRICES[0];

  useEffect(() => {
    setIsGuest(localStorage.getItem('kissannet_auth') === 'guest');

    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      if (currentUser) {
        setUser(currentUser);
        setIsGuest(false);
      }
    });

    autoDetectLocation()
      .then(loc => fetchLiveWeather(loc.lat, loc.lon, { name: loc.name, city: loc.city, state: loc.state, country: loc.country }))
      .then(data => setLiveWeather(data))
      .catch(err => {
        fetchLiveWeather(16.3067, 80.4365).then(setLiveWeather).catch(() => {});
      });
  }, [router]);

  const openVoice = (prompt?: string) => {
    setVoicePrompt(prompt || "");
    setIsVoiceModalOpen(true);
  };

  const handlePlayVoice = (id: string, text: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (playingId === id) { stopSpeech(); setPlayingId(null); }
    else { setPlayingId(id); speakInLanguage(text, language, () => setPlayingId(id), () => setPlayingId(null)); }
  };

  return (
    <div className="relative">

      {/* ══════════════════════════════════════
          MOBILE LAYOUT (hidden on lg+)
      ══════════════════════════════════════ */}
      <div className="lg:hidden">
        {/* Hero */}
        <section className="relative h-72 w-full overflow-hidden sm:h-80">
          <Image src={IMAGES.sunsetFieldHero} alt="A lush green farm field" fill priority sizes="100vw" className="object-cover object-center" />
          <div className="absolute inset-0 bg-gradient-to-t from-white via-white/80 to-black/20" />
          <div className="relative z-10 flex h-full flex-col justify-between p-5">
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold text-white backdrop-blur-sm flex items-center gap-2">
                <Image src={logo} alt="" className="w-5 h-5 rounded-full" />
                🌾 KisanNet
              </span>
              <div className="flex items-center gap-2">
                <button onClick={() => setIsLanguageModalOpen(true)} className="rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold text-white backdrop-blur-sm hover:bg-white/25 transition-colors">
                  {currentOption.flag} {currentOption.nativeName} ▾
                </button>
                <span className="rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold text-white backdrop-blur-sm">
                  {liveWeather?.conditionIcon || '🌤️'} {liveWeather ? `${liveWeather.temperature}°C` : '31°C'}
                </span>
              </div>
            </div>
            <div className="text-center pb-4">
              <h1 className="font-display text-4xl font-extrabold leading-tight text-white drop-shadow-md">{t('greetingTitle')}</h1>
              <p className="mt-2 text-white/90 text-sm max-w-sm mx-auto">
                {liveWeather ? `${t('weatherInfo')} ${liveWeather.temperature}°C — ${liveWeather.conditionText}. ${t('greetingSubtitle')}` : t('greetingSubtitle')}
              </p>
            </div>
          </div>
        </section>
        <section className="-mt-2 flex justify-center px-5 py-6"><VoiceOrb onTrigger={() => openVoice()} /></section>
        <section className="px-5">
          <h2 className="mb-3 font-display text-lg font-bold text-paddy">{t('todayNeeds', 'ఈ రోజు ఏం కావాలి?')}</h2>
          <div className="grid grid-cols-2 gap-3">
            <QuickCard href="/advisory" label={t('cropDoctor')} sublabel={t('cropDoctorDesc')} image={IMAGES.farmerGrainDrying} icon={Stethoscope} />
            <QuickCard href="/schemes" label={t('schemes', 'ప్రభుత్వ పథకాలు')} sublabel={t('schemesDesc', 'అర్హత చూడండి')} image={IMAGES.paddyAerial} icon={Landmark} />
            <QuickCard href="/weather" label={t('weatherInfo')} sublabel={t('weatherInfoDesc')} image={IMAGES.greenRiceField} icon={CloudSun} />
            <QuickCard href="/market" label={t('mandiRates')} sublabel={t('mandiRatesDesc')} image={IMAGES.farmerSunrise} icon={BadgeIndianRupee} />
          </div>
        </section>
        <section className="mt-6 px-5">
          <h2 className="mb-3 font-display text-lg font-bold text-paddy">తాజా మండి ధర 💰</h2>
          <div className="flex items-center justify-between gap-3 rounded-4xl bg-white p-4 shadow-card border border-soil/10">
            <div className="flex items-center gap-3">
              <img src={topMandi.imageUrl} alt={topMandi.cropNameEn} className="w-14 h-14 rounded-2xl object-cover border border-soil/10 shrink-0" />
              <div>
                <span className="font-display text-sm font-bold text-paddy">{topMandi.cropNameTe}</span>
                <p className="text-xs text-soil/70 mt-0.5">{topMandi.marketNameTe}</p>
                <p className="font-display text-lg font-bold text-paddy-dark mt-0.5">₹{topMandi.currentPrice.toLocaleString()} <span className="text-xs font-normal text-soil/60">/{topMandi.unit.split(' ')[0]}</span></p>
              </div>
            </div>
            <Link href="/market" className="text-xs font-bold text-paddy hover:underline whitespace-nowrap">అన్ని ధరలు →</Link>
          </div>
        </section>
        <section className="mt-6 px-5 pb-8">
          <h2 className="mb-3 font-display text-lg font-bold text-paddy">తాజా సలహా</h2>
          <div className="flex items-center gap-3 rounded-4xl bg-white p-3 shadow-card">
            <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-2xl">
              <Image src={IMAGES.farmerPortrait} alt="" fill sizes="64px" className="object-cover" />
            </div>
            <div className="flex-1">
              <p className="font-display text-sm font-bold text-paddy">మిర్చి ఆకు ముడుత — నిన్న</p>
              <p className="text-sm text-soil/70">సాయంత్రం వేళ వేప నూనె పిచికారీ చేయండి.</p>
            </div>
          </div>
        </section>
      </div>

      {/* ══════════════════════════════════════
          DESKTOP LAYOUT (lg and above)
          Matches the screenshot exactly:
          - Fixed left sidebar
          - Top navbar
          - Hero card with farmer image + voice bar
          - 4 quick cards row
          - 3-column bottom: mandi | advisory | news
          - Stats footer bar
      ══════════════════════════════════════ */}
      <div className="hidden lg:flex lg:w-full lg:h-screen">

        {/* ── LEFT SIDEBAR ── */}
        <aside className="w-44 shrink-0 flex flex-col bg-white border-r border-soil/10 shadow-soft z-20">
          {/* Brand */}
          <div className="flex items-center gap-2.5 px-5 py-5 border-b border-soil/10">
            <Image src={logo} alt="KisanNet" className="w-8 h-8 rounded-full object-contain" />
            <span className="font-display font-black text-paddy text-base">KisanNet</span>
          </div>

          {/* Nav links */}
          <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
            {SIDEBAR_LINKS.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              // Simple key mapping from label
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
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* TOP NAVBAR */}
          <header className="shrink-0 flex items-center justify-between px-7 py-3.5 bg-white border-b border-soil/10 z-10">
            <div className="flex items-center gap-3">
              {/* Language selector */}
              <button onClick={() => setIsLanguageModalOpen(true)}
                className="flex items-center gap-1.5 border border-soil/15 rounded-full px-3 py-1.5 text-sm font-semibold text-soil hover:bg-husk transition-colors">
                <Globe size={16} /> {currentOption.nativeName} ▾
              </button>
              <div className="flex items-center gap-1.5 text-sm font-medium text-soil/70">
                <span className="text-base">{liveWeather?.conditionIcon || '🌤️'}</span>
                <span className="font-bold text-paddy-dark">{liveWeather ? `${liveWeather.temperature}°C` : '30°C'}</span>
                <span className="text-soil/50">{liveWeather?.conditionText || 'Overcast Sky'}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button className="w-9 h-9 rounded-full border border-soil/10 flex items-center justify-center hover:bg-husk transition-colors">
                <Bell size={18} className="text-soil/60" />
              </button>
              {isGuest && !user ? (
                <button 
                  onClick={() => router.push('/signup')}
                  className="px-4 py-2 rounded-full bg-paddy/10 text-paddy text-sm font-bold hover:bg-paddy/20 transition-colors"
                >
                  Sign Up
                </button>
              ) : (
                <Link href="/profile" className="w-10 h-10 rounded-full overflow-hidden border-2 border-paddy/30 block cursor-pointer">
                  {user?.photoURL ? (
                    <img src={user.photoURL} alt="Profile" className="object-cover w-full h-full" referrerPolicy="no-referrer" />
                  ) : (
                    <Image src={IMAGES.farmerPortrait} alt="Profile" width={40} height={40} className="object-cover w-full h-full" />
                  )}
                </Link>
              )}
            </div>
          </header>

          <main className="flex-1 overflow-y-auto px-7 py-6 space-y-6 bg-husk/40">

            {/* ── HERO CARD ── */}
            <div className="relative w-full h-64 shrink-0 rounded-3xl overflow-hidden shadow-soft">
              <Image src={IMAGES.sunsetFieldHero} alt="Sunset Farm" fill sizes="100vw" className="object-cover object-center" priority />
              <div className="absolute inset-0 bg-black/30" />
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4">
                <h1 className="font-display text-4xl font-extrabold text-white leading-tight drop-shadow-md">
                  {t('greetingTitle')}
                </h1>
                <p className="text-sm text-white/90 mt-2 max-w-md drop-shadow-sm">
                  {liveWeather
                    ? `${t('weatherInfo')} ${liveWeather.temperature}°C — ${liveWeather.conditionText}. ${t('greetingSubtitle')}`
                    : t('greetingSubtitle')}
                </p>
                {/* Voice bar */}
                <button onClick={() => openVoice()}
                  className="mt-6 flex items-center gap-4 bg-white rounded-full shadow-lg px-2 py-2 pr-8 hover:shadow-xl transition-all active:scale-[0.99] w-full max-w-md group">
                  <div className="w-14 h-14 rounded-full bg-paddy-dark flex items-center justify-center shrink-0 shadow-sm transition-colors border-[4px] border-white">
                    <Mic size={24} className="text-white" />
                  </div>
                  <div className="flex-1 text-left ml-2">
                    <p className="text-sm text-soil/70 mt-1">or say &ldquo;Namaste KisanNet&rdquo;</p>
                  </div>
                  {/* Waveform indicator */}
                  <div className="flex items-center gap-0.5 shrink-0">
                    {[3, 5, 7, 5, 8, 5, 7, 4, 6].map((h, i) => (
                      <div key={i} className="w-0.5 rounded-full bg-paddy/40 animate-pulse" style={{ height: `${h}px`, animationDelay: `${i * 80}ms` }} />
                    ))}
                  </div>
                </button>
              </div>
            </div>

            {/* ── 4 QUICK CARDS ROW ── */}
            <div className="shrink-0">
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-display text-base font-bold text-paddy-dark">{t('todayNeeds', 'ఈ రోజు ఏం కావాలి?')}</h2>
                <Link href="/advisory" className="text-xs font-bold text-paddy flex items-center gap-1 hover:underline">
                  {t('viewAll', 'View All')} <ChevronRight size={14} />
                </Link>
              </div>
              <div className="grid grid-cols-4 gap-3">
                <QuickCard href="/advisory" label={t('cropDoctor')} sublabel={t('cropDoctorDesc')} image={IMAGES.farmerGrainDrying} icon={Stethoscope} />
                <QuickCard href="/schemes" label={t('schemes', 'ప్రభుత్వ పథకాలు')} sublabel={t('schemesDesc', 'అర్హత చూడండి')} image={IMAGES.paddyAerial} icon={Landmark} />
                <QuickCard href="/weather" label={t('weatherInfo')} sublabel={t('weatherInfoDesc')} image={IMAGES.greenRiceField} icon={CloudSun} />
                <QuickCard href="/market" label={t('mandiRates')} sublabel={t('mandiRatesDesc')} image={IMAGES.farmerSunrise} icon={BadgeIndianRupee} />
              </div>
            </div>

            {/* ── 3-COLUMN BOTTOM ROW ── */}
            <div className="grid grid-cols-3 gap-4 pb-6">

              {/* Mandi Price */}
              <div className="bg-white rounded-3xl p-4 shadow-card border border-soil/10">
                <h3 className="font-display text-sm font-bold text-paddy mb-3">{t('latestMandiRates', 'తాజా మండి ధర')} 💰</h3>
                <div className="flex items-center gap-3">
                  <img src={topMandi.imageUrl} alt={topMandi.cropNameEn} className="w-14 h-14 rounded-2xl object-cover border border-soil/10 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-display text-sm font-bold text-paddy-dark truncate">{language === 'en' ? topMandi.cropNameEn : topMandi.cropNameTe}</p>
                    <span className={`inline-flex items-center gap-0.5 text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 ${topMandi.trend === 'up' ? 'bg-emerald-100 text-emerald-700' :
                        topMandi.trend === 'down' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'
                      }`}>
                      {topMandi.trend === 'up' ? <TrendingUp className="w-2.5 h-2.5" /> : topMandi.trend === 'down' ? <TrendingDown className="w-2.5 h-2.5" /> : <Minus className="w-2.5 h-2.5" />}
                      {language === 'en' ? topMandi.trendTextEn || topMandi.trendTextTe : topMandi.trendTextTe}
                    </span>
                    <p className="text-[10px] text-soil/60 mt-0.5 truncate">{language === 'en' ? topMandi.marketNameEn || topMandi.marketNameTe : topMandi.marketNameTe}</p>
                  </div>
                  <button onClick={(e) => handlePlayVoice('mandi', `ఖమ్మంలో తేజ మిర్చి క్వింటాలుకు ₹${topMandi.currentPrice} ఉంది.`, e)}
                    className="w-7 h-7 rounded-full bg-husk border border-soil/10 flex items-center justify-center text-paddy hover:bg-husk-dark transition-colors shrink-0 cursor-pointer">
                    {playingId === 'mandi' ? <VolumeX size={12} /> : <Volume2 size={12} />}
                  </button>
                </div>
                <div className="mt-3 flex items-baseline justify-between">
                  <span className="font-display text-2xl font-black text-paddy-dark">
                    ₹{topMandi.currentPrice.toLocaleString()}
                    <span className="text-xs font-normal text-soil/50 ml-1">/ {topMandi.unit.split(' ')[0]}</span>
                  </span>
                  <Link href="/market" className="text-xs font-bold text-paddy hover:underline whitespace-nowrap">
                    {t('allPrices', 'అన్ని ధరలు')} →
                  </Link>
                </div>
              </div>

              {/* Recent Advisory */}
              <div className="bg-white rounded-3xl p-4 shadow-card border border-soil/10">
                <h3 className="font-display text-sm font-bold text-paddy mb-3">{t('recentAdvisory', 'తాజా సలహా')}</h3>
                <div className="flex items-start gap-3">
                  <div className="relative w-14 h-14 rounded-2xl overflow-hidden shrink-0 border border-soil/10">
                    <Image src={IMAGES.farmerPortrait} alt="" fill sizes="56px" className="object-cover" />
                  </div>
                  <div className="flex-1">
                    <p className="font-display text-sm font-bold text-paddy-dark">{t('advisorySampleTitle', 'మిర్చి ఆకు ముడుత — నిన్న')}</p>
                    <p className="text-xs text-soil/60 mt-1 leading-relaxed">
                      {t('advisorySampleDesc', 'సాయంత్రం వేళ వేప నూనె పిచికారీ చేయండి, మధ్యాహ్నం వేడిలో వద్దు.')}
                    </p>
                  </div>
                </div>
                <Link href="/advisory" className="mt-3 flex items-center justify-center w-full py-2 rounded-2xl bg-paddy/8 text-paddy text-xs font-bold hover:bg-paddy/15 transition-colors">
                  {t('read', 'చదవండి')}
                </Link>
              </div>

              {/* Farmer News */}
              <div className="bg-white rounded-3xl p-4 shadow-card border border-soil/10">
                <h3 className="font-display text-sm font-bold text-paddy mb-3 flex items-center gap-1.5">
                  <Newspaper size={15} /> {t('farmerNews', 'రైతు న్యూస్')}
                </h3>
                <p className="text-xs text-soil/70 leading-relaxed">
                  {t('newsSample', 'రాష్ట్రంలో రాబోయే వారం వరకు తేలికపాటి వర్షాలు కొనసాగుతున్నాయి. రైతులు పిచికారీ వాయిదా వేయాలి.')}
                </p>
                <p className="text-[10px] text-soil/40 font-medium mt-2">{t('hoursAgo', '2 గంటల క్రితం')}</p>
                <Link href="/advisory" className="mt-3 flex items-center gap-1 text-xs font-bold text-paddy hover:underline">
                  {t('readMore', 'మరింత చదవండి')} <ChevronRight size={13} />
                </Link>
              </div>
            </div>

            {/* ── STATS BAR ── */}
            <div className="grid grid-cols-4 gap-3 pb-2 shrink-0">
              {[
                { icon: <Users size={20} className="text-paddy-dark" />, value: '12.5K+', label: t('statsCommunity', 'సంఘాలు రైతులు') },
                { icon: <Store size={20} className="text-paddy-dark" />, value: '256+', label: t('statsMarkets', 'మార్కెట్ యార్డ్లు') },
                { icon: <FileText size={20} className="text-paddy-dark" />, value: '48+', label: t('statsSchemes', 'ప్రభుత్వ పథకాలు') },
                { icon: <Mic size={20} className="text-paddy-dark" />, value: '24/7', label: t('statsVoice', 'వాయిస్ సహాయం') },
              ].map((stat) => (
                <div key={stat.label} className="bg-white rounded-2xl p-4 shadow-card border border-soil/10 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-paddy/10 flex items-center justify-center shrink-0">
                    {stat.icon}
                  </div>
                  <div>
                    <p className="font-display text-lg font-black text-paddy">{stat.value}</p>
                    <p className="text-[11px] text-soil/60 font-semibold">{stat.label}</p>
                  </div>
                </div>
              ))}
            </div>

          </main>
        </div>
      </div>

      {/* ─── Voice Modal (shared) ─── */}
      {isVoiceModalOpen && (
        <div className="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center animate-fadeIn">
          <div className="w-full h-full sm:h-[95vh] sm:max-h-[900px] sm:max-w-4xl">
            <VoiceAssistantModal
              isOpen={isVoiceModalOpen}
              onClose={() => setIsVoiceModalOpen(false)}
              initialPrompt={voicePrompt}
              initialMode="voice"
              onNavigate={() => setIsVoiceModalOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

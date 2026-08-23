"use client";
import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Image from "next/image";
import logo from "@/assets/image.png";
import { Sprout, TrendingUp, Landmark, CloudRain, Bot, Leaf } from "lucide-react";

export default function SplashScreen() {
  const pathname = usePathname();
  const [fade, setFade] = useState(false);
  const [mounted, setMounted] = useState(true);

  useEffect(() => {
    // 2-second initial delay, then trigger fade out
    const timer = setTimeout(() => {
      setFade(true);
      setTimeout(() => {
        setMounted(false);
      }, 500); // 500ms fade transition
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  // Do not show splash screen on auth pages (login/signup)
  if (pathname === '/login' || pathname === '/signup') return null;

  if (!mounted) return null;


  return (
    <div className={`fixed inset-0 z-[100] flex flex-col justify-between bg-[#FDFCF8] text-[#2D3A32] font-sans transition-opacity duration-500 overflow-hidden ${fade ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
      
      {/* Subtle background styling to simulate the farm horizon */}
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-40 mix-blend-multiply pointer-events-none"></div>
      <div className="absolute bottom-0 w-full h-[45vh] bg-gradient-to-t from-[#E6F0E3] to-transparent pointer-events-none"></div>
      
      <div className="absolute bottom-0 w-full flex justify-center opacity-30 pointer-events-none pointer-events-none translate-y-12">
          {/* Abstract SVG curves to represent rolling hills since we don't have the specific image asset */}
          <svg viewBox="0 0 1440 320" className="w-[150vw] h-auto min-w-[1440px] text-[#CDE3CA]">
            <path fill="currentColor" fillOpacity="1" d="M0,224L60,213.3C120,203,240,181,360,192C480,203,600,245,720,245.3C840,245,960,203,1080,186.7C1200,171,1320,181,1380,186.7L1440,192L1440,320L1380,320C1320,320,1200,320,1080,320C960,320,840,320,720,320C600,320,480,320,360,320C240,320,120,320,60,320L0,320Z"></path>
          </svg>
      </div>

      {/* Center Content */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10 px-4 mt-8">
        
        {/* Animated Logo */}
        <div className="w-48 h-48 sm:w-64 sm:h-64 mb-6 relative animate-[pulse_3s_ease-in-out_infinite]">
           <Image src={logo} alt="KisanNet Logo" fill className="object-contain drop-shadow-md" priority />
        </div>
        
        <h1 className="text-3xl sm:text-[40px] font-display font-black text-[#1E4A32] tracking-tight mb-3">
          Welcome to KisanNet
        </h1>
        <p className="text-[#5C6F62] text-sm sm:text-base font-medium max-w-sm text-center mb-16">
          Your trusted partner for smart farming and better tomorrow.
        </p>

        {/* Custom Circular Spinner mimicking the screenshot */}
        <div className="flex flex-col items-center gap-5">
          <div className="relative flex items-center justify-center w-[84px] h-[84px]">
            {/* Background track */}
            <svg className="absolute w-full h-full text-[#E6DFCD]/60" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="46" fill="none" strokeWidth="5" stroke="currentColor" />
            </svg>
            {/* Spinning arc */}
            <svg className="absolute w-full h-full text-[#245C35] animate-[spin_1.5s_linear_infinite]" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="46" fill="none" strokeWidth="5.5" stroke="currentColor" strokeDasharray="80 210" strokeLinecap="round" />
            </svg>
            {/* Leaf inside */}
            <Leaf className="w-7 h-7 text-[#245C35] -rotate-12" strokeWidth={2.5} />
          </div>
          <span className="text-[15px] font-medium text-[#1E4A32]">Loading...</span>
        </div>
      </div>

      {/* Features Grid at Bottom (Matches the design exactly) */}
      <div className="relative z-10 pb-16 px-4 w-full max-w-[1000px] mx-auto hidden md:block">
        <div className="grid grid-cols-5 divide-x divide-[#E6DFCD]">
          {[
            { icon: Sprout, label: "Farming", desc: "Expert advice for\nbetter crop growth", color: "text-[#245C35]", bg: "bg-[#E6F0E3]" },
            { icon: TrendingUp, label: "Market Prices", desc: "Live market rates\nand trends", color: "text-[#D97706]", bg: "bg-[#FEF3C7]" },
            { icon: Landmark, label: "Schemes", desc: "Government schemes\nand subsidies", color: "text-[#6D28D9]", bg: "bg-[#EDE9FE]" },
            { icon: CloudRain, label: "Weather", desc: "Accurate weather\nupdates", color: "text-[#0369A1]", bg: "bg-[#E0F2FE]" },
            { icon: Bot, label: "AI Advice", desc: "Ask anything,\nget smart answers", color: "text-[#047857]", bg: "bg-[#D1FAE5]" },
          ].map((feature, i) => (
            <div key={i} className="flex flex-col items-center text-center px-4">
              <div className={`w-[52px] h-[52px] rounded-full flex items-center justify-center mb-4 shadow-sm ${feature.bg}`}>
                <feature.icon className={`w-[26px] h-[26px] ${feature.color}`} strokeWidth={2} />
              </div>
              <h3 className="font-bold text-[#1E4A32] text-[15px] mb-1.5">{feature.label}</h3>
              <p className="text-[12px] text-[#5C6F62] leading-relaxed whitespace-pre-line">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

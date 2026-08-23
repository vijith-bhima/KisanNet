"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mic, MessageCircleHeart, Landmark, UserCircle2, LineChart, CloudSun, PhoneCall } from "lucide-react";

const TABS = [
  { href: "/", label: "Home", icon: Mic },
  { href: "/advisory", label: "Advice", icon: MessageCircleHeart },
  { href: "/schemes", label: "Schemes", icon: Landmark },
  { href: "/market", label: "Market Prices", icon: LineChart },
  { href: "/weather", label: "Weather", icon: CloudSun },
  { href: "/profile", label: "Profile", icon: UserCircle2 },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 flex-col bg-[#F9F7EF] border-r border-[#E6DFCD] h-full py-6 shrink-0 relative z-10">
      {/* Logo */}
      <div className="flex items-center gap-3 px-8 mb-10">
        <div className="w-10 h-10 rounded-full bg-white overflow-hidden p-1 shadow-sm border border-[#E6DFCD]">
          <img src="/kisannet_logo.png" alt="KisanNet" className="w-full h-full object-contain scale-110" />
        </div>
        <h1 className="text-2xl font-black text-[#245C35] tracking-tight">KisanNet</h1>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 px-4 space-y-2">
        {TABS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-4 px-4 py-3 rounded-2xl transition-all ${
                active
                  ? "bg-[#E6F0E3] text-[#245C35] font-bold shadow-sm"
                  : "text-[#5C6F62] hover:bg-[#F0EAD8] hover:text-[#245C35] font-semibold"
              }`}
            >
              <Icon size={22} className={active ? "text-[#307042]" : "text-[#5C6F62]"} strokeWidth={active ? 2.5 : 2} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Need Help Widget */}
      <div className="px-6 mb-6">
        <div className="bg-white border border-[#E6DFCD] rounded-2xl p-4 flex items-center gap-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
          <div className="w-10 h-10 rounded-full bg-[#E6F0E3] flex items-center justify-center shrink-0">
            <PhoneCall size={20} className="text-[#307042]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#245C35]">Need Help?</h3>
            <p className="text-[11px] text-[#5C6F62] mt-0.5 leading-tight">Talk to an expert<br/><span className="font-bold text-[#4A5D4E]">1800-123-4567</span></p>
          </div>
        </div>
      </div>

      {/* Footer text */}
      <div className="px-8 mt-auto flex flex-col gap-2">
        <p className="text-[11px] font-semibold text-[#8C9B90]">
          © 2025 KisanNet<br/>All rights reserved
        </p>
        <div className="flex gap-3 text-[#5C6F62]">
          <div className="w-4 h-4 rounded-full bg-[#DDECD9]"></div>
          <div className="w-4 h-4 rounded-full bg-[#DDECD9]"></div>
          <div className="w-4 h-4 rounded-full bg-[#DDECD9]"></div>
          <div className="w-4 h-4 rounded-full bg-[#DDECD9]"></div>
        </div>
      </div>
    </aside>
  );
}

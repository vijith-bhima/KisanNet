"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mic, MessageCircleHeart, Landmark, UserCircle2, LineChart, CloudSun } from "lucide-react";

const TABS = [
  { href: "/", label: "Home", icon: Mic },
  { href: "/advisory", label: "Advice", icon: MessageCircleHeart },
  { href: "/schemes", label: "Schemes", icon: Landmark },
  { href: "/market", label: "Market Prices", icon: LineChart },
  { href: "/weather", label: "Weather", icon: CloudSun },
  { href: "/profile", label: "Profile", icon: UserCircle2 },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main navigation"
      className="fixed inset-x-0 bottom-0 z-40 mx-auto w-full border-t border-soil/10 bg-husk/95 backdrop-blur-md lg:hidden overflow-x-auto"
    >
      <ul className="flex items-center justify-between min-w-max px-2">
        {TABS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <li key={href} className="shrink-0">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className="flex flex-col items-center gap-1 py-3 px-4 transition-colors"
              >
                <span
                  className={`flex h-11 w-11 items-center justify-center rounded-2xl transition-all ${active
                      ? "bg-paddy text-turmeric shadow-soft scale-105"
                      : "text-soil/50"
                    }`}
                >
                  <Icon size={24} strokeWidth={active ? 2.4 : 2} aria-hidden="true" />
                </span>
                <span
                  className={`font-display text-[13px] font-semibold ${active ? "text-paddy" : "text-soil/50"
                    }`}
                >
                  {label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

import Image from "next/image";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";

export default function QuickCard({
  href,
  label,
  sublabel,
  image,
  icon: Icon,
}: {
  href: string;
  label: string;
  sublabel: string;
  image: string;
  icon: LucideIcon;
}) {
  return (
    <Link
      href={href}
      className="group relative flex h-32 flex-col justify-end overflow-hidden rounded-4xl shadow-card active:scale-[0.98] transition-transform"
    >
      <Image
        src={image}
        alt=""
        fill
        sizes="200px"
        className="object-cover transition-transform duration-500 group-hover:scale-110"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-paddy-dark/90 via-paddy-dark/30 to-transparent" />
      <span className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-husk/90">
        <Icon size={18} className="text-paddy" aria-hidden="true" />
      </span>
      <div className="relative z-10 px-3 pb-3">
        <p className="font-display text-base font-bold leading-tight text-white">
          {label}
        </p>
        <p className="text-xs text-white/80">{sublabel}</p>
      </div>
    </Link>
  );
}

"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Phone, MapPin, Sprout, ChevronRight, LogIn } from "lucide-react";
import { IMAGES } from "@/lib/images";
import { useLanguage } from "@/context/LanguageContext";
import { auth } from "@/lib/firebase";
import { signOut, onAuthStateChanged, User } from "firebase/auth";

export default function Profile() {
  const [isGuest, setIsGuest] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const { language, setLanguage, languages } = useLanguage();

  useEffect(() => {
    setIsGuest(localStorage.getItem('kissannet_auth') === 'guest');
    
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      if (currentUser) {
        setUser(currentUser);
        setIsGuest(false);
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="pt-6 relative pb-10">
      {/* Sign Up / Login button for guests */}
      {isGuest && (
        <button 
          onClick={() => router.push('/login')}
          className="absolute top-4 left-4 flex items-center gap-2 bg-paddy/10 text-paddy font-bold px-4 py-2 rounded-full text-sm hover:bg-paddy/20 transition-colors shadow-sm"
        >
          <LogIn size={16} />
          Sign In
        </button>
      )}

      <section className="flex flex-col items-center px-5 mt-10 lg:mt-0">
        <div className="relative h-24 w-24 overflow-hidden rounded-full border-4 border-turmeric shadow-soft bg-white flex items-center justify-center">
          {isGuest ? (
            <span className="text-4xl">🧑‍🌾</span>
          ) : user?.photoURL ? (
            <img
              src={user.photoURL}
              alt="Your profile photo"
              className="object-cover w-full h-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <Image
              src={IMAGES.farmerPortrait}
              alt="Your profile photo"
              fill
              sizes="96px"
              className="object-cover"
            />
          )}
        </div>
        <h1 className="mt-3 font-display text-2xl font-extrabold text-paddy text-center">
          {isGuest ? "Guest Farmer" : (user?.displayName || "Farmer")}
        </h1>
        <p className="flex items-center gap-1 text-sm text-soil/70 mt-1">
          <MapPin size={14} aria-hidden="true" />
          {isGuest ? "Location unknown" : "India"}
        </p>
      </section>

      <section className="mt-8 px-5">
        <h2 className="mb-4 font-display text-base font-bold text-paddy">
          Choose your language
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {languages.map((lang) => {
            const isActive = language === lang.code;
            return (
              <button
                key={lang.code}
                onClick={() => setLanguage(lang.code)}
                type="button"
                className={`rounded-3xl border-2 py-4 text-center transition-colors ${
                  isActive
                    ? "border-paddy bg-paddy text-white shadow-soft"
                    : "border-soil/15 bg-white text-paddy hover:border-paddy/30"
                }`}
              >
                <span className="block font-display text-xl font-bold">
                  {lang.nativeName}
                </span>
                <span
                  className={`text-xs mt-1 block ${isActive ? "text-white/70" : "text-soil/50"}`}
                >
                  {lang.name}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="mt-8 px-5">
        <h2 className="mb-3 font-display text-base font-bold text-paddy">
          My farm
        </h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3 rounded-3xl bg-white p-4 shadow-card border border-soil/5">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-paddy/10">
              <Sprout size={20} className="text-paddy" aria-hidden="true" />
            </span>
            <div className="flex-1">
              <p className="font-display text-sm font-bold text-paddy-dark">
                {isGuest ? "Add your crop" : "Chilli, 2.5 acres"}
              </p>
              <p className="text-xs text-soil/60">
                {isGuest ? "Get personalized advisory" : "Kharif season"}
              </p>
            </div>
            <ChevronRight size={20} className="text-soil/40" aria-hidden="true" />
          </div>
          
          <div className="flex items-center gap-3 rounded-3xl bg-white p-4 shadow-card border border-soil/5">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-monsoon/10">
              <Phone size={20} className="text-monsoon" aria-hidden="true" />
            </span>
            <div className="flex-1 overflow-hidden">
              <p className="font-display text-sm font-bold text-paddy-dark truncate">
                {isGuest ? "Not connected" : (user?.email || "No email provided")}
              </p>
              <p className="text-xs text-soil/60">
                {isGuest ? "Sign in to connect account" : "Google Account"}
              </p>
            </div>
            <ChevronRight size={20} className="text-soil/40" aria-hidden="true" />
          </div>
        </div>
      </section>

      {/* Sign Out Button (Only for authenticated users) */}
      {!isGuest && (
        <section className="mt-8 px-5 flex justify-center">
          <button 
            onClick={async () => {
              try {
                await signOut(auth);
                localStorage.removeItem('kissannet_auth');
                router.push('/login');
              } catch (error) {
                console.error("Error signing out:", error);
              }
            }}
            className="text-red-500 font-bold text-sm hover:underline"
          >
            Sign Out
          </button>
        </section>
      )}
    </div>
  );
}

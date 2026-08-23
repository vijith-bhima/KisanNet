"use client";

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from '@/lib/firebase';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // 1. Always allow access to the login and signup pages
    if (pathname === '/login' || pathname === '/signup') {
      setIsReady(true);
      return;
    }

    // 2. Check if the user bypassed auth via "Skip Sign In"
    const guestStatus = typeof window !== 'undefined' ? localStorage.getItem('kissannet_auth') : null;
    if (guestStatus === 'guest') {
      setIsReady(true);
      return;
    }

    // 3. Set a safety fallback timer: if Firebase auth check takes too long or is unconfigured,
    // default new users directly to the sign-in page.
    let resolved = false;
    const fallbackTimer = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        router.replace('/login');
      }
    }, 800);

    // 4. Listen for Firebase authentication state
    try {
      const unsubscribe = onAuthStateChanged(
        auth,
        (user) => {
          if (resolved) return;
          resolved = true;
          clearTimeout(fallbackTimer);
          if (user) {
            setIsReady(true);
          } else {
            router.replace('/login');
          }
        },
        (error) => {
          console.warn("Firebase Auth listener error, redirecting to login:", error);
          if (resolved) return;
          resolved = true;
          clearTimeout(fallbackTimer);
          router.replace('/login');
        }
      );

      return () => {
        clearTimeout(fallbackTimer);
        unsubscribe();
      };
    } catch (err) {
      console.warn("Firebase Auth unavailable, redirecting to login:", err);
      clearTimeout(fallbackTimer);
      router.replace('/login');
    }
  }, [pathname, router]);

  // Prevent flash of unauthenticated content
  if (!isReady) return null;

  return <>{children}</>;
}


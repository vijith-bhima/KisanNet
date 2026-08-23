import type { Metadata, Viewport } from "next";
import "./globals.css";
import BottomNav from "@/components/BottomNav";
import SplashScreen from "@/components/SplashScreen";
import LanguageModal from "@/components/LanguageModal";
import AuthGuard from "@/components/AuthGuard";
import { LanguageProvider } from '../context/LanguageContext';

export const metadata: Metadata = {
  title: "KisanNet — Your Farming Voice",
  description: "Voice-first agricultural advisory for every farmer.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "KisanNet",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#1E4A32",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Baloo+Tammudu+2:wght@500;600;700;800&family=Hind+Guntur:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body antialiased bg-husk">
        <LanguageProvider>
          <AuthGuard>
            <SplashScreen />
            <LanguageModal />
            {/* max-w-screen-lg makes it full-width on laptop, centered with padding */}
            <div className="mx-auto flex min-h-dvh w-full max-w-screen-lg flex-col bg-husk shadow-2xl lg:max-w-full lg:h-screen lg:overflow-hidden">
              <main className="flex-1 pb-24 lg:pb-0 overflow-y-auto">{children}</main>
              <BottomNav />
            </div>
          </AuthGuard>
        </LanguageProvider>
      </body>
    </html>
  );
}

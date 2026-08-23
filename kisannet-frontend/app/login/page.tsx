"use client";

import React, { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { 
  LineChart, Landmark, CloudSun, MessageCircle, 
  ShieldCheck, CheckCircle2, Users, Smartphone, Loader2
} from 'lucide-react';
import { IMAGES } from '@/lib/images';
import logo from '@/assets/image.png';
import { auth } from '@/lib/firebase';
import { RecaptchaVerifier, signInWithPhoneNumber, ConfirmationResult, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [mobile, setMobile] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);

  const handleSkip = () => {
    localStorage.setItem('kissannet_auth', 'guest');
    router.replace('/');
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      router.replace('/');
    } catch (error) {
      console.error("Error with Google Sign-In:", error);
      alert("Failed to sign in with Google. Please try again.");
      setLoading(false);
    }
  };

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mobile.length < 10) return;
    setLoading(true);
    
    try {
      if (!(window as any).recaptchaVerifier) {
        (window as any).recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
          size: 'invisible'
        });
      }
      const appVerifier = (window as any).recaptchaVerifier;
      const phoneNumber = '+91' + mobile;
      const confirmation = await signInWithPhoneNumber(auth, phoneNumber, appVerifier);
      setConfirmationResult(confirmation);
      setStep(2);
    } catch (error) {
      console.error("Error sending OTP:", error);
      alert("Failed to send OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    const otpCode = otp.join('');
    if (otpCode.length < 6 || !confirmationResult) return;
    
    setLoading(true);
    try {
      await confirmationResult.confirm(otpCode);
      // Firebase auth state listener in AuthGuard will handle redirect
      router.replace('/');
    } catch (error) {
      console.error("Error verifying OTP:", error);
      alert("Invalid OTP code.");
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    // Auto focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex flex-col lg:flex-row bg-[#F9F7EF] font-sans">
      
      {/* ── LEFT SIDE (Hero) ── */}
      <div className="relative w-full lg:w-[55%] xl:w-[60%] flex flex-col p-6 lg:p-12 overflow-hidden bg-gradient-to-br from-[#E6F3EA] to-[#F3F8F2]">
        <Image 
          src={IMAGES.sunsetFieldHero} 
          alt="Farm Background" 
          fill 
          priority 
          className="object-cover object-center opacity-30 mix-blend-overlay"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#E6F3EA] via-transparent to-transparent opacity-80" />
        
        <div className="relative z-10 flex-1 flex flex-col">
          {/* Brand */}
          <div className="flex items-center gap-3 mb-12">
            <Image src={logo} alt="KisanNet" className="w-10 h-10 rounded-full object-contain" />
            <span className="font-display font-black text-[#1E4A32] text-2xl tracking-tight">KisanNet</span>
          </div>

          {/* Hero Content */}
          <div className="max-w-lg mt-auto lg:mt-24 mb-16">
            <h1 className="font-display font-black text-4xl lg:text-6xl text-[#1E4A32] leading-[1.1] mb-6">
              Smart farming<br />starts here
              <span className="inline-block ml-3 text-3xl">🌱</span>
            </h1>
            <p className="text-lg text-[#3A5243] font-medium leading-relaxed max-w-md">
              Get market prices, schemes, expert advice, weather updates and more – all in one place.
            </p>
          </div>

          {/* Feature Cards Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-auto">
            <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-sm border border-white flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-[#E6F3EA] flex items-center justify-center text-[#307042] mb-3">
                <LineChart size={20} />
              </div>
              <h3 className="font-bold text-[#1E4A32] text-[13px] mb-1">Market Prices</h3>
              <p className="text-[10px] text-[#5C6F62] leading-tight">Live mandi prices and trends</p>
            </div>
            <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-sm border border-white flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-[#E6F3EA] flex items-center justify-center text-[#307042] mb-3">
                <Landmark size={20} />
              </div>
              <h3 className="font-bold text-[#1E4A32] text-[13px] mb-1">Government Schemes</h3>
              <p className="text-[10px] text-[#5C6F62] leading-tight">Find schemes you're eligible for</p>
            </div>
            <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-sm border border-white flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-[#E6F3EA] flex items-center justify-center text-[#307042] mb-3">
                <CloudSun size={20} />
              </div>
              <h3 className="font-bold text-[#1E4A32] text-[13px] mb-1">Weather Updates</h3>
              <p className="text-[10px] text-[#5C6F62] leading-tight">Accurate local weather forecast</p>
            </div>
            <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-sm border border-white flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-[#E6F3EA] flex items-center justify-center text-[#307042] mb-3">
                <MessageCircle size={20} />
              </div>
              <h3 className="font-bold text-[#1E4A32] text-[13px] mb-1">Expert Advice</h3>
              <p className="text-[10px] text-[#5C6F62] leading-tight">Get expert tips and solutions</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── RIGHT SIDE (Auth Form) ── */}
      <div className="w-full lg:w-[45%] xl:w-[40%] flex flex-col bg-[#F9F7EF] lg:bg-transparent">
        
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
          
          {/* Auth Card */}
          <div className="w-full max-w-md bg-white rounded-[2rem] p-8 lg:p-10 shadow-2xl border border-gray-100 relative">
            
            <button 
              onClick={handleSkip}
              className="absolute top-6 right-6 flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs font-bold text-gray-500 hover:bg-gray-50 transition-colors"
            >
              <Users size={14} /> Skip Sign In <span className="text-[10px]">›</span>
            </button>

            <div className="text-center mt-6 mb-8">
              <h2 className="text-2xl font-display font-bold text-[#1E4A32] mb-2">Welcome to <span className="text-[#8B5A2B]">KisanNet</span></h2>
              <p className="text-sm text-gray-500 font-medium">Sign in to continue</p>
              
              <div className="flex justify-center mt-4 mb-2">
                <span className="text-[#307042] opacity-60">🌿</span>
              </div>
            </div>

            {step === 1 ? (
              <form onSubmit={handleSendOTP} className="space-y-6 animate-fadeIn">
                
                <button 
                  type="button" 
                  onClick={handleGoogleSignIn}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 rounded-2xl py-3.5 text-sm font-bold text-gray-700 hover:bg-gray-50 transition-all active:scale-[0.98]"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/><path fill="none" d="M1 1h22v22H1z"/></svg>
                  {loading ? 'Connecting...' : 'Continue with Google'}
                </button>

                <div className="relative flex items-center">
                  <div className="flex-grow border-t border-gray-200"></div>
                  <span className="flex-shrink-0 mx-4 text-[11px] uppercase tracking-wider text-gray-400 font-bold">or</span>
                  <div className="flex-grow border-t border-gray-200"></div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-2">Mobile Number</label>
                  <div className="relative flex items-center">
                    <span className="absolute left-4 text-gray-500 font-bold text-sm">+91</span>
                    <input 
                      type="tel"
                      maxLength={10}
                      value={mobile}
                      disabled
                      onChange={(e) => setMobile(e.target.value.replace(/\D/g, ''))}
                      placeholder="Enter mobile number"
                      className="w-full pl-12 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl text-sm font-bold text-[#1E4A32] placeholder-gray-400 focus:outline-none opacity-50 cursor-not-allowed transition-all"
                    />
                    <Smartphone className="absolute right-4 w-5 h-5 text-gray-400" />
                  </div>
                </div>

                <button 
                  type="button"
                  disabled
                  className="w-full bg-gray-300 text-gray-500 rounded-2xl py-3.5 text-sm font-bold shadow-none cursor-not-allowed flex justify-center items-center h-[52px]"
                >
                  Mobile Login (Coming Soon)
                </button>

                <p className="text-center text-[11px] font-medium text-gray-500 pt-2">
                  Don't have an account? <span onClick={() => router.push('/signup')} className="font-bold text-[#307042] cursor-pointer hover:underline">Sign Up</span>
                </p>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP} className="space-y-6 animate-slideUp">
                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-1">Enter OTP</label>
                  <p className="text-xs text-gray-400 mb-4">Code sent to +91 {mobile} <span onClick={() => setStep(1)} className="text-[#307042] font-bold cursor-pointer hover:underline ml-1">Edit</span></p>
                  
                  <div className="flex justify-between gap-2">
                    {otp.map((digit, i) => (
                      <input
                        key={i}
                        id={`otp-${i}`}
                        type="text"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOtpChange(i, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(i, e)}
                        className="w-12 h-14 bg-gray-50 border border-gray-200 rounded-xl text-center text-lg font-black text-[#1E4A32] focus:outline-none focus:border-[#307042] focus:ring-1 focus:ring-[#307042] transition-all"
                      />
                    ))}
                  </div>
                </div>

                <button 
                  type="submit"
                  disabled={otp.join('').length < 6 || loading}
                  className="w-full bg-[#307042] text-white rounded-2xl py-3.5 text-sm font-bold shadow-md hover:bg-[#1E4A32] hover:shadow-lg transition-all active:scale-[0.98] disabled:opacity-70 disabled:active:scale-100 flex justify-center items-center h-[52px]"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Verify & Sign In'}
                </button>

                <p className="text-center text-[11px] font-medium text-gray-500 pt-2">
                  Didn't receive the code? <span onClick={handleSendOTP} className="font-bold text-[#307042] cursor-pointer hover:underline">Resend OTP</span>
                </p>
              </form>
            )}
            
            <div id="recaptcha-container"></div>
          </div>
        </div>

        {/* Trust Badges */}
        <div className="pb-8 px-6 lg:px-12 w-full">
          <div className="flex items-center justify-center divide-x divide-gray-300 w-full max-w-md mx-auto">
            <div className="flex items-center gap-2 px-4 flex-1 justify-center">
              <ShieldCheck className="w-5 h-5 text-[#307042]" />
              <div>
                <p className="text-[10px] font-bold text-[#1E4A32]">100% Secure</p>
                <p className="text-[8px] text-gray-500">Your data is safe</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 flex-1 justify-center">
              <CheckCircle2 className="w-5 h-5 text-[#307042]" />
              <div>
                <p className="text-[10px] font-bold text-[#1E4A32]">Verified</p>
                <p className="text-[8px] text-gray-500">Trusted platform</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 flex-1 justify-center">
              <Users className="w-5 h-5 text-[#307042]" />
              <div>
                <p className="text-[10px] font-bold text-[#1E4A32]">For Farmers</p>
                <p className="text-[8px] text-gray-500">Built for you</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

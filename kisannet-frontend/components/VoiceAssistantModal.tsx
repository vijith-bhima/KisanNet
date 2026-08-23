"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Mic, X, Square, Phone } from 'lucide-react';
import { Room, RoomEvent, Track, RemoteTrack } from 'livekit-client';
import { VoiceMessage } from '../types';
import { useLanguage } from '../context/LanguageContext';
import { speakInLanguage, stopSpeech } from '../utils/speech';
import { auth } from '@/lib/firebase';

interface VoiceAssistantProps {
  isOpen?: boolean;
  onClose?: () => void;
  initialPrompt?: string;
  onNavigate?: (tab: string) => void;
  initialMode?: 'voice' | 'chat';
}

export const VoiceAssistantModal: React.FC<VoiceAssistantProps> = ({
  isOpen = false,
  onClose,
  initialPrompt = '',
  onNavigate,
  initialMode = 'voice',
}) => {
  const { t, language, currentOption, setIsLanguageModalOpen } = useLanguage();
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const roomRef = useRef<Room | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const [timer, setTimer] = useState(0);

  // Timer logic for when speaking
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isConnected || isConnecting) {
      interval = setInterval(() => {
        setTimer((prev) => prev + 1);
      }, 1000);
    } else {
      setTimer(0);
    }
    return () => clearInterval(interval);
  }, [isConnected, isConnecting]);

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // Clean up LiveKit room on unmount or modal close
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
        roomRef.current = null;
      }
      stopSpeech();
    };
  }, []);

  const connectToLiveKit = async () => {
    setConnectionError(null);
    setIsConnecting(true);
    setIsUserSpeaking(true); // Simulate listening state first

    try {
      // Get the real user name if authenticated
      const user = auth.currentUser;
      const participantName = user?.displayName ? encodeURIComponent(user.displayName) : "farmer";

      // 1. Fetch token from FastAPI backend
      const res = await fetch(`http://localhost:8000/api/v1/voice/token?language=${currentOption.code}&participant_name=${participantName}`);
      if (!res.ok) {
        throw new Error(`Token request failed: ${res.statusText}`);
      }
      const { token, url } = await res.json();

      if (!token || !url) {
        throw new Error('LiveKit credentials missing from server response.');
      }

      // 2. Create LiveKit Room
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      roomRef.current = room;

      // 3. Setup event listeners
      room.on(RoomEvent.TrackSubscribed, (track: RemoteTrack, publication, participant) => {
        if (track.kind === Track.Kind.Audio) {
          if (audioElRef.current) {
            track.attach(audioElRef.current);
          }
        }
      });

      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const localId = room.localParticipant?.identity;
        const agentSpeaking = speakers.some((s) => s.identity !== localId);
        const userSpeaking = speakers.some((s) => s.identity === localId);
        setIsAgentSpeaking(agentSpeaking);
        setIsUserSpeaking(!agentSpeaking && userSpeaking);
      });

      room.on(RoomEvent.Disconnected, (reason) => {
        setIsConnected(false);
        setIsConnecting(false);
        setIsAgentSpeaking(false);
        setIsUserSpeaking(false);
      });

      // 4. Connect to WebRTC Room & Enable Microphone
      await room.connect(url, token);
      await room.localParticipant.setMicrophoneEnabled(true);

      setIsConnected(true);
      setIsConnecting(false);
      setIsMuted(false);
    } catch (err: any) {
      setConnectionError('Unable to connect to LiveKit Voice Agent.');
      setIsConnecting(false);
      setIsConnected(false);
    }
  };

  const disconnectFromLiveKit = () => {
    if (roomRef.current) {
      roomRef.current.disconnect();
      roomRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    setIsAgentSpeaking(false);
    setIsUserSpeaking(false);
    setTimer(0);
  };

  const toggleAction = () => {
    if (isConnected || isConnecting) {
      disconnectFromLiveKit();
    } else {
      connectToLiveKit();
    }
  };

  // Determine state for UI rendering
  const isActive = isConnected || isConnecting;
  // If agent is speaking, it's the "Speaking..." state in the mockup (right side)
  // If not agent speaking (and active), it's the "Listening..." state in the mockup (left side)
  const isAgentMode = isAgentSpeaking; 

  return (
    <div className="flex flex-col h-full overflow-hidden relative bg-[#1B3A27] text-white w-full h-full font-sans">
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes orb-pulse {
          0% { box-shadow: 0 0 0 0 rgba(144, 238, 144, 0.4); }
          70% { box-shadow: 0 0 0 60px rgba(144, 238, 144, 0); }
          100% { box-shadow: 0 0 0 0 rgba(144, 238, 144, 0); }
        }
        @keyframes visualizer {
          0% { height: 4px; }
          50% { height: 24px; }
          100% { height: 4px; }
        }
        .visualizer-bar {
          width: 3px;
          background-color: #8DEB8D;
          border-radius: 9999px;
          animation: visualizer 1s infinite ease-in-out;
        }
        .visualizer-bar:nth-child(1) { animation-delay: 0.1s; }
        .visualizer-bar:nth-child(2) { animation-delay: 0.3s; }
        .visualizer-bar:nth-child(3) { animation-delay: 0.6s; }
        .visualizer-bar:nth-child(4) { animation-delay: 0.2s; }
        .visualizer-bar:nth-child(5) { animation-delay: 0.8s; }
        .visualizer-bar:nth-child(6) { animation-delay: 0.4s; }
        .visualizer-bar:nth-child(7) { animation-delay: 0.7s; }
        .visualizer-bar:nth-child(8) { animation-delay: 0.5s; }
        
        .bg-landscape {
           background: linear-gradient(to top, #0A150F 0%, transparent 40%),
                       url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="%230F2516" fill-opacity="1" d="M0,288L48,272C96,256,192,224,288,213.3C384,203,480,213,576,213.3C672,213,768,203,864,208C960,213,1056,235,1152,245.3C1248,256,1344,256,1392,256L1440,256L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path><path fill="%230A150F" fill-opacity="1" d="M0,256L48,245.3C96,235,192,213,288,218.7C384,224,480,256,576,256C672,256,768,224,864,202.7C960,181,1056,171,1152,181.3C1248,192,1344,224,1392,240L1440,256L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path></svg>');
           background-size: cover;
           background-position: bottom;
           background-repeat: no-repeat;
        }
      `}} />

      <audio ref={audioElRef} autoPlay />

      {/* Background with slight gradient and trees/landscape silhouette at bottom */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#183522] via-[#20452C] to-[#122A1A] z-0" />
      <div className="absolute bottom-0 left-0 right-0 h-64 bg-landscape z-0 opacity-80" />

      {/* Top Header */}
      <div className="relative z-10 flex items-center justify-between p-6">
        <button onClick={onClose} className="text-white/70 hover:text-white transition-colors" aria-label="Close">
          <X className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full overflow-hidden">
            <img src="/kisannet_logo.png" alt="KisanNet" className="w-full h-full object-contain" />
          </div>
          <span className="font-bold text-lg tracking-wide text-white">KisanNet</span>
        </div>
        <div className="w-6" /> {/* Spacer to center the logo */}
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-start pt-10 px-6">
        
        {/* Greetings Text */}
        <h1 className="text-4xl font-bold text-white mb-4">{t('greetingTitle', 'Hello Farmer! 🙏')}</h1>
        <p className="text-[#A4C4AD] text-center max-w-sm text-lg leading-relaxed whitespace-pre-wrap">
          {isAgentMode 
            ? t('agentPreparing', 'Preparing an answer for you...') 
            : isActive ? t('listening', 'Listening to you...') : t('welcomeVoice', 'I am your voice assistant.\nAsk your farming question...')}
        </p>

        {/* Central Orb */}
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          <div className="relative flex items-center justify-center mb-16">
            
            {/* Audio Visualizer (Left side for Speaking state) */}
            {isAgentMode && (
              <div className="absolute -left-20 flex items-center gap-[3px] h-10">
                {[1,2,3,4,5,6].map(i => <div key={i} className="visualizer-bar" />)}
              </div>
            )}

            {/* Glowing rings */}
            <div className={`absolute w-[280px] h-[280px] rounded-full border border-[#8DEB8D]/20 bg-[#8DEB8D]/5 ${isActive ? 'animate-[orb-pulse_2s_infinite]' : ''}`} />
            <div className={`absolute w-[220px] h-[220px] rounded-full border border-[#8DEB8D]/30 bg-[#8DEB8D]/10 ${isActive ? 'animate-[orb-pulse_2.5s_infinite]' : ''}`} />
            <div className="absolute w-[160px] h-[160px] rounded-full border border-[#8DEB8D]/50 bg-[#8DEB8D]/20 shadow-[0_0_40px_rgba(141,235,141,0.3)]" />

            {/* Core Button */}
            <button 
              onClick={toggleAction}
              className={`relative z-20 w-24 h-24 rounded-full flex items-center justify-center shadow-2xl transition-all cursor-pointer ${
                isAgentMode ? 'bg-[#183522]' : 'bg-[#F4F1E5]'
              }`}
            >
              {isAgentMode ? (
                <Mic className="w-10 h-10 text-white" />
              ) : (
                <Phone className="w-10 h-10 text-[#307042] fill-[#307042]" />
              )}
            </button>

            {/* Audio Visualizer (Right side for Speaking state) */}
            {isAgentMode && (
              <div className="absolute -right-20 flex items-center gap-[3px] h-10">
                {[1,2,3,4,5,6].map(i => <div key={i} className="visualizer-bar" />)}
              </div>
            )}

          </div>

          {/* Bottom Status & Controls */}
          <div className="flex flex-col items-center">
            {connectionError && (
              <p className="text-red-400 mb-4">{connectionError}</p>
            )}

            <h2 className="text-xl font-medium text-white mb-2">
              {isAgentMode ? t('speaking', 'Speaking...') : isActive ? t('listening', 'Listening...') : t('ready', 'Ready')}
            </h2>
            
            {isAgentMode ? (
              <p className="text-[#A4C4AD] mb-8">{formatTimer(timer)}</p>
            ) : (
              <button onClick={disconnectFromLiveKit} className="text-[#A4C4AD] hover:text-white transition-colors mb-8 cursor-pointer">
                {t('tapToCancel', 'Tap to cancel')}
              </button>
            )}

            {/* Visualizer for Listening state at bottom */}
            {!isAgentMode && isActive && (
              <div className="flex items-center gap-1.5 h-12 mb-8">
                {[1,2,3,4,5,6,7,8,9,10,11,12].map(i => <div key={i} className="visualizer-bar" />)}
              </div>
            )}

            {/* Tap to stop button for Speaking state */}
            {isAgentMode && (
              <button 
                onClick={disconnectFromLiveKit}
                className="flex items-center gap-2 bg-[#12281B] hover:bg-[#1A3826] border border-[#234A31] px-5 py-2.5 rounded-full text-sm text-[#A4C4AD] transition-colors cursor-pointer"
              >
                <div className="w-3 h-3 bg-[#FF4C4C] rounded-sm" />
                {t('tapToStop', 'Tap to stop')}
              </button>
            )}
            
            {/* Start button if not active */}
            {!isActive && (
               <button 
               onClick={connectToLiveKit}
               className="flex items-center gap-2 bg-[#8DEB8D] hover:bg-[#7BD97B] text-[#0A150F] font-bold px-6 py-3 rounded-full transition-colors cursor-pointer"
             >
               {t('startListening', 'Start Listening')}
             </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};


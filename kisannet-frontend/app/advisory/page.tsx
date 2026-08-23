"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from 'next/link';
import Image from "next/image";
import { usePathname } from 'next/navigation';
import { 
  Home as HomeIcon, MessageCircle, Landmark, TrendingUp as MarketIcon, Cloud, 
  UserCircle2, Phone, Bell, Globe, Search, Youtube, Facebook, Instagram,
  Bot, Clock, Paperclip, Mic, Send, 
  Leaf, Bug, CloudRain, FlaskConical, Droplets, Sprout, 
  Camera, ChevronRight, Info, RefreshCw, Check, Sparkles, X, Plus
} from "lucide-react";
import { IMAGES } from "@/lib/images";
import logo from "@/assets/image.png";
import { fetchLiveWeather, LiveWeatherData, autoDetectLocation } from '@/utils/weatherService';
import { useLanguage } from '@/context/LanguageContext';

const SIDEBAR_LINKS = [
  { href: "/", label: "Home", labelTe: "హోమ్", icon: HomeIcon },
  { href: "/advisory", label: "Advice", labelTe: "సలహా", icon: MessageCircle },
  { href: "/schemes", label: "Schemes", labelTe: "పథకాలు", icon: Landmark },
  { href: "/market", label: "Market Prices", labelTe: "మార్కెట్ ధరలు", icon: MarketIcon },
  { href: "/weather", label: "Weather", labelTe: "వాతావరణం", icon: Cloud },
  { href: "/profile", label: "Profile", labelTe: "ప్రొఫైల్", icon: UserCircle2 },
];

export default function AdvisoryPage() {
  const [liveWeather, setLiveWeather] = useState<LiveWeatherData | null>(null);
  const { currentOption, setIsLanguageModalOpen } = useLanguage();
  const pathname = usePathname();

  useEffect(() => {
    autoDetectLocation()
      .then(loc => fetchLiveWeather(loc.lat, loc.lon, { name: loc.name, city: loc.city, state: loc.state, country: loc.country }))
      .then(data => setLiveWeather(data))
      .catch(err => {
        fetchLiveWeather(16.3067, 80.4365).then(setLiveWeather).catch(() => {});
      });
  }, []);

  const [messages, setMessages] = useState<Array<{ role: 'user' | 'ai', content: string }>>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState<Array<{ id: string, date: string, title: string, messages: any[] }>>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  useEffect(() => {
    const saved = localStorage.getItem('kisanNetChatSessions');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.length > 0) {
          setSessions(parsed);
          const latest = parsed[0];
          setMessages(latest.messages);
          setCurrentSessionId(latest.id);
          return;
        }
      } catch (e) {}
    }
    
    // Fallback if no sessions
    const initialId = Date.now().toString();
    setCurrentSessionId(initialId);
    setMessages([
      {
        role: 'ai',
        content: 'Hello! I am KisanNet AI. How can I help you today?\n\nYou can ask me about:\n- 🌾 Crop Diseases & Treatments\n- 📈 Market Prices\n- 🏛️ Government Schemes'
      }
    ]);
  }, []);

  useEffect(() => {
    if (messages.length > 0 && currentSessionId) {
      setSessions(prev => {
        const existingIdx = prev.findIndex(s => s.id === currentSessionId);
        const title = messages.find(m => m.role === 'user')?.content.substring(0, 30) + '...' || 'New Chat';
        
        const newSession = {
          id: currentSessionId,
          date: new Date().toLocaleDateString(),
          title: title,
          messages: messages
        };

        let updated;
        if (existingIdx >= 0) {
          updated = [...prev];
          updated[existingIdx] = newSession;
        } else {
          updated = [newSession, ...prev];
        }
        localStorage.setItem('kisanNetChatSessions', JSON.stringify(updated));
        return updated;
      });
    }
  }, [messages, currentSessionId]);

  const startNewChat = () => {
    setCurrentSessionId(Date.now().toString());
    setMessages([
      {
        role: 'ai',
        content: 'Hello! I am KisanNet AI. How can I help you today?\n\nYou can ask me about:\n- 🌾 Crop Diseases & Treatments\n- 📈 Market Prices\n- 🏛️ Government Schemes'
      }
    ]);
    setShowHistory(false);
  };

  const loadSession = (id: string) => {
    const session = sessions.find(s => s.id === id);
    if (session) {
      setCurrentSessionId(session.id);
      setMessages(session.messages);
      setShowHistory(false);
    }
  };
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    const newMessages = [...messages, { role: 'user' as const, content: userMsg }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: newMessages })
        });
        
        if (!response.body) throw new Error("No response body");
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        setMessages([...newMessages, { role: 'ai', content: '' }]);
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const text = decoder.decode(value, { stream: true });
            setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1].content += text;
                return updated;
            });
        }
    } catch (error) {
        console.error("Chat error:", error);
    } finally {
        setLoading(false);
    }
  };

  const formatMessage = (content: string) => {
    let formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-paddy-dark bg-yellow-100 px-1 rounded">$1</strong>');
    return <div className="text-[15px] leading-relaxed text-soil whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  return (
    <div className="flex h-[100dvh] w-full bg-husk overflow-hidden">
      
      {/* ── LEFT SIDEBAR (Desktop Only) ── */}
      <aside className="hidden lg:flex w-44 shrink-0 flex-col bg-white border-r border-soil/10 shadow-soft z-20 h-full">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-soil/10">
          <Image src={logo} alt="KisanNet" className="w-8 h-8 rounded-full object-contain" />
          <span className="font-display font-black text-paddy text-base">KisanNet</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 flex flex-col gap-1.5">
          {SIDEBAR_LINKS.map((link, idx) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <a
                key={idx}
                href={link.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
                  isActive 
                    ? "bg-paddy-light text-paddy-dark shadow-sm" 
                    : "text-soil/70 hover:bg-husk hover:text-paddy"
                }`}
              >
                <Icon className={`w-[18px] h-[18px] transition-transform duration-300 ${
                  isActive ? "scale-110" : "group-hover:scale-110 group-hover:rotate-3"
                }`} />
                <span className={`font-semibold text-sm ${isActive ? "" : ""}`}>{link.label}</span>
              </a>
            );
          })}
        </nav>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <div className="flex-1 flex flex-col h-full bg-white relative z-10 w-full overflow-hidden">
        
        {/* MOBILE HEADER */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-soil/10 sticky top-0 z-30 shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-display font-black text-paddy-dark">AI Advisory</h1>
          </div>
          <button className="p-2 rounded-xl text-soil hover:bg-husk relative">
             <Bell className="w-5 h-5" />
             <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-paddy rounded-full border border-white"></span>
          </button>
        </header>

        {/* MAIN CONTENT AREA */}
        <div className="flex-1 flex flex-col overflow-hidden h-full w-full">
            
            {/* CHAT INTERFACE */}
            <div className="flex-1 bg-white flex flex-col overflow-hidden h-full">
              
              {/* Chat Header */}
              <div className="shrink-0 flex items-center justify-between px-4 lg:px-6 py-2.5 border-b border-soil/10 bg-gradient-to-r from-white to-husk/30">
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#E8F3EA] to-[#C3DFC9] flex items-center justify-center shadow-sm relative border border-paddy/20">
                    <Bot className="w-6 h-6 text-paddy-dark" />
                    <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 border-2 border-white rounded-full animate-pulse"></div>
                  </div>
                  <div>
                    <h2 className="font-bold text-paddy-dark text-lg flex items-center gap-1.5">
                      KisanNet AI <Sparkles className="w-4 h-4 text-turmeric-dark" />
                    </h2>
                    <span className="text-xs font-semibold text-emerald-600">Online & Ready to help</span>
                  </div>
                </div>
                <button 
                  onClick={() => setShowHistory(true)}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-soil/70 border border-soil/20 rounded-xl hover:bg-husk transition-colors shadow-sm bg-white">
                  <Clock className="w-4 h-4" />
                  History
                </button>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-[#F9F7EF]/50 relative">
                
                {messages.map((msg, idx) => (
                  msg.role === 'user' ? (
                    <div key={idx} className="flex justify-end gap-3 group">
                      <div className="flex flex-col items-end">
                        <div className="bg-paddy text-white rounded-2xl rounded-tr-sm px-5 py-4 max-w-[85%] shadow-md">
                          <p className="text-[15px] leading-relaxed font-medium whitespace-pre-wrap">
                            {msg.content}
                          </p>
                        </div>
                      </div>
                      <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0 border-2 border-paddy/20 shadow-sm">
                        <Image src={IMAGES.farmerProfile} alt="User" width={40} height={40} className="object-cover h-full w-full" />
                      </div>
                    </div>
                  ) : (
                    <div key={idx} className="flex justify-start gap-3 group">
                      <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#E8F3EA] to-[#C3DFC9] flex items-center justify-center flex-shrink-0 shadow-sm border border-paddy/20 mt-1">
                        <Bot className="w-5 h-5 text-paddy-dark" />
                      </div>
                      <div className="flex flex-col items-start max-w-[85%]">
                        <div className="bg-white rounded-3xl rounded-tl-sm px-6 py-5 shadow-card border border-soil/10">
                          {formatMessage(msg.content)}
                        </div>
                      </div>
                    </div>
                  )
                ))}

                {loading && (
                   <div className="flex justify-start gap-3">
                     <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#E8F3EA] to-[#C3DFC9] flex items-center justify-center flex-shrink-0 shadow-sm border border-paddy/20 mt-1">
                       <Bot className="w-5 h-5 text-paddy-dark animate-pulse" />
                     </div>
                     <div className="bg-white rounded-3xl rounded-tl-sm px-6 py-5 shadow-card border border-soil/10 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-paddy animate-bounce"></div>
                        <div className="w-2 h-2 rounded-full bg-paddy animate-bounce delay-100"></div>
                        <div className="w-2 h-2 rounded-full bg-paddy animate-bounce delay-200"></div>
                     </div>
                   </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Area */}
              <div className="shrink-0 p-4 lg:p-5 bg-white border-t border-soil/10 relative z-10 pb-20 lg:pb-5">
                <div className="flex items-end gap-2 bg-white border-2 border-soil/15 focus-within:border-paddy rounded-3xl p-2 shadow-sm transition-colors relative">
                  <button 
                    onClick={() => alert("Attachment feature coming soon!")}
                    className="p-3 text-soil/50 hover:text-paddy hover:bg-husk rounded-full transition-colors flex-shrink-0">
                    <Paperclip className="w-5 h-5" />
                  </button>
                  <textarea 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit();
                      }
                    }}
                    placeholder="మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి (Type your question)..." 
                    className="flex-1 bg-transparent border-none outline-none focus:ring-0 focus:outline-none text-soil placeholder-soil/40 py-3 min-h-[48px] max-h-[120px] resize-none font-medium text-[15px]"
                    rows={1}
                  />
                  <div className="flex items-center gap-2 p-1 flex-shrink-0">
                    <button 
                      onClick={() => alert("Voice recording coming soon!")}
                      className="w-12 h-12 rounded-full border-2 border-soil/10 flex items-center justify-center text-soil/60 hover:bg-husk hover:text-paddy transition-colors">
                      <Mic className="w-5 h-5" />
                    </button>
                    <button 
                      onClick={handleSubmit}
                      disabled={loading || !input.trim()}
                      className="w-12 h-12 rounded-full bg-paddy flex items-center justify-center text-white hover:bg-paddy-dark shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                      <Send className="w-5 h-5 ml-1" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 mt-4 text-[10px] text-soil/50 justify-center text-center font-medium">
                  <Info className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>AI సూచనలు సాధారణ మార్గదర్శకాలు మాత్రమే. ఖచ్చితమైన సలహా కోసం నిపుణులను సంప్రదించండి.</span>
                </div>
              </div>
            </div>

            {/* History Slide-over Sidebar */}
            {showHistory && (
              <div className="absolute inset-0 z-50 flex justify-end">
                {/* Backdrop */}
                <div 
                  className="absolute inset-0 bg-soil/20 backdrop-blur-sm" 
                  onClick={() => setShowHistory(false)}
                />
                
                {/* Sidebar */}
                <div className="relative w-80 max-w-[80vw] h-full bg-white shadow-2xl flex flex-col border-l border-soil/10 transform transition-transform duration-300">
                  <div className="p-4 border-b border-soil/10 flex items-center justify-between bg-husk/30">
                    <h3 className="font-bold text-paddy-dark flex items-center gap-2">
                      <Clock className="w-5 h-5" /> Chat History
                    </h3>
                    <button 
                      onClick={() => setShowHistory(false)}
                      className="p-2 text-soil/50 hover:text-paddy hover:bg-husk rounded-full transition-colors">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  
                  <div className="p-4 border-b border-soil/10">
                    <button 
                      onClick={startNewChat}
                      className="w-full py-2.5 px-4 bg-paddy hover:bg-paddy-dark text-white rounded-xl font-bold text-sm transition-colors shadow-sm flex items-center justify-center gap-2">
                      <Plus className="w-4 h-4" /> New Chat
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {sessions.length === 0 ? (
                      <div className="text-center text-sm text-soil/50 mt-10">No chat history found.</div>
                    ) : (
                      sessions.map(session => (
                        <button
                          key={session.id}
                          onClick={() => loadSession(session.id)}
                          className={`w-full text-left p-3 rounded-xl transition-colors border ${
                            currentSessionId === session.id 
                              ? 'bg-paddy-light/50 border-paddy/30' 
                              : 'bg-white border-soil/10 hover:border-paddy/30 hover:bg-husk'
                          }`}
                        >
                          <div className="font-semibold text-soil text-sm truncate pr-2">
                            {session.title === 'New Chat' ? 'New Conversation' : session.title}
                          </div>
                          <div className="text-xs text-soil/50 mt-1.5 font-medium">{session.date}</div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}

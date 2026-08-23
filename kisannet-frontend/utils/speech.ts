// Multi-Language Speech Synthesis Utility for KisanNet
// Supports Telugu, English, Hindi, Tamil, Kannada, and Marathi

let activeUtterance: SpeechSynthesisUtterance | null = null;

const LANG_VOICE_MAP: Record<string, { voiceQuery: string[]; fallback: string }> = {
  te: { voiceQuery: ['te-IN', 'te', 'telugu'], fallback: 'te-IN' },
  en: { voiceQuery: ['en-IN', 'en-GB', 'en-US', 'en'], fallback: 'en-IN' },
  hi: { voiceQuery: ['hi-IN', 'hi', 'hindi'], fallback: 'hi-IN' },
  ta: { voiceQuery: ['ta-IN', 'ta', 'tamil'], fallback: 'ta-IN' },
  kn: { voiceQuery: ['kn-IN', 'kn', 'kannada'], fallback: 'kn-IN' },
  mr: { voiceQuery: ['mr-IN', 'mr', 'marathi'], fallback: 'mr-IN' },
};

export const speakInLanguage = (
  text: string,
  langCode: string = 'te',
  onStart?: () => void,
  onEnd?: () => void
): void => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    if (onStart) onStart();
    setTimeout(() => {
      if (onEnd) onEnd();
    }, 2500);
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Clean text: strip markdown symbols or excessive punctuation
  const cleanText = text
    .replace(/[#*`_~]/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (!cleanText) {
    if (onEnd) onEnd();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  const langConfig = LANG_VOICE_MAP[langCode] || LANG_VOICE_MAP.te;

  // Locate best matching voice
  const voices = window.speechSynthesis.getVoices();
  let preferredVoice: SpeechSynthesisVoice | undefined;

  for (const query of langConfig.voiceQuery) {
    preferredVoice = voices.find(
      (v) =>
        v.lang.toLowerCase().includes(query.toLowerCase()) ||
        v.name.toLowerCase().includes(query.toLowerCase())
    );
    if (preferredVoice) break;
  }

  // Fallbacks: Indian English or general voice
  if (!preferredVoice) {
    preferredVoice =
      voices.find((v) => v.lang.includes('en-IN')) ||
      voices.find((v) => v.lang.includes('hi')) ||
      voices[0];
  }

  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  utterance.lang = preferredVoice?.lang || langConfig.fallback;
  utterance.rate = 0.88; // Relaxed pace for clear comprehension for rural farmers
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    if (onStart) onStart();
  };

  utterance.onend = () => {
    activeUtterance = null;
    if (onEnd) onEnd();
  };

  utterance.onerror = () => {
    activeUtterance = null;
    if (onEnd) onEnd();
  };

  activeUtterance = utterance;
  window.speechSynthesis.speak(utterance);
};

// Legacy backward-compatibility alias
export const speakTelugu = (text: string, onStart?: () => void, onEnd?: () => void): void => {
  speakInLanguage(text, 'te', onStart, onEnd);
};

export const stopSpeech = (): void => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  activeUtterance = null;
};

export const stopTeluguSpeech = stopSpeech;

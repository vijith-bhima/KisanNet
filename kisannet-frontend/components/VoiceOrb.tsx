"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Mic, Square } from "lucide-react";

export default function VoiceOrb({ onTrigger }: { onTrigger?: () => void }) {
  const [listening, setListening] = useState(false);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative flex h-52 w-52 items-center justify-center">
        {listening && (
          <>
            <span className="absolute h-full w-full rounded-full bg-turmeric/40 animate-pulse-ring" />
            <span className="absolute h-full w-full rounded-full bg-turmeric/40 animate-pulse-ring-delay" />
          </>
        )}
        <motion.button
          type="button"
          onClick={() => {
            setListening(false);
            if (onTrigger) onTrigger();
          }}
          whileTap={{ scale: 0.94 }}
          aria-pressed={listening}
          aria-label={listening ? "Stop listening" : "Speak to KisanNet"}
          className={`relative flex h-40 w-40 items-center justify-center rounded-full shadow-soft transition-colors duration-300 ${
            listening
              ? "bg-chili"
              : "bg-gradient-to-br from-turmeric to-turmeric-dark"
          }`}
        >
          <span className="absolute inset-2 rounded-full border-2 border-white/30" />
          {listening ? (
            <Square size={44} className="text-white" fill="white" aria-hidden="true" />
          ) : (
            <Mic size={56} className="text-paddy-dark" strokeWidth={2.2} aria-hidden="true" />
          )}
        </motion.button>
      </div>
      <p className="font-display text-lg font-semibold text-paddy" aria-live="polite">
        {listening ? "Listening… speak now" : "Tap and ask your question"}
      </p>
      <p className="text-sm text-soil/70">or say "Namaste KisanNet"</p>
    </div>
  );
}

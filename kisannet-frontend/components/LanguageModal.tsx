"use client";
import React from 'react';
import { useLanguage } from '@/context/LanguageContext';

export default function LanguageModal() {
  const { 
    isLanguageModalOpen, 
    setIsLanguageModalOpen, 
    languages, 
    language, 
    setLanguage 
  } = useLanguage();

  if (!isLanguageModalOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-white rounded-3xl p-6 w-full max-w-md shadow-2xl relative">
        <button 
          onClick={() => setIsLanguageModalOpen(false)}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
        >
          ✕
        </button>
        
        <h2 className="text-xl font-bold text-[#1E4A32] mb-4">Select Language</h2>
        
        <div className="grid grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLanguage(lang.code);
                setIsLanguageModalOpen(false);
              }}
              className={`flex flex-col items-start p-4 rounded-2xl border transition-all ${
                language === lang.code 
                  ? 'border-[#307042] bg-[#307042]/10 shadow-sm' 
                  : 'border-[#E6DFCD] hover:border-[#307042]/30 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">{lang.flag}</span>
                <span className={`font-bold ${language === lang.code ? 'text-[#1E4A32]' : 'text-[#2D3A32]'}`}>
                  {lang.nativeName}
                </span>
              </div>
              <span className="text-xs text-[#5C6F62] font-medium ml-8">{lang.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

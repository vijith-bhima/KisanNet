export type WeatherType = 'sunny' | 'cloudy' | 'rain' | 'evening' | 'night';

export type CropType = 'paddy' | 'chilli' | 'tomato' | 'cotton' | 'onion' | 'wheat';

export interface CropInfo {
  id: string;
  nameTe: string;
  nameEn: string;
  variety: string;
  daysPlanted: number;
  stageTe: string;
  stageEn: string;
  healthStatus: 'healthy' | 'warning' | 'critical';
  healthMessageTe: string;
  healthMessageEn: string;
  soilMoisturePercent: number;
  soilMoistureStatusTe: string;
  irrigationAdviceTe: string;
  imageUrl: string;
  acreage: number;
  nextTaskTe: string;
}

export interface DiseaseResult {
  id: string;
  cropNameTe: string;
  cropNameEn: string;
  diseaseNameTe: string;
  diseaseNameEn: string;
  confidenceScore: number;
  confidenceLevel: 'high' | 'medium' | 'low';
  severity: 'mild' | 'moderate' | 'severe';
  imageUrl: string;
  affectedAreaDescriptionTe: string;
  affectedAreaDescriptionEn: string;
  symptomsTe: string[];
  organicTreatmentTe: {
    title: string;
    items: string[];
    costPerAcre: number;
  };
  chemicalTreatmentTe: {
    title: string;
    items: string[];
    costPerAcre: number;
  };
  voiceAudioScriptTe: string;
  detailedTextTe: string;
  preventionTe: string[];
}

export interface MandiItem {
  id: string;
  cropNameTe: string;
  cropNameEn: string;
  rawCommodity?: string;
  category?: string;
  variety: string;
  imageUrl: string;
  currentPrice: number;
  modalPrice?: number;
  unit: string;
  unitKg?: string;
  pricePerKg?: number;
  minPricePerKg?: number;
  maxPricePerKg?: number;
  priceChange: number; // +2, -1, 0
  trend: 'up' | 'down' | 'stable';
  trendTextTe: string;
  trendTextEn?: string;
  marketNameTe: string;
  marketNameEn: string;
  district?: string;
  state?: string;
  distanceKm: number;
  minPrice: number;
  maxPrice: number;
  date: string;
  rawDate?: string;
}

export interface JournalEntry {
  id: string;
  timestamp: string;
  timeTe: string;
  dateTe: string;
  locationTe: string;
  voiceTranscriptTe: string;
  category: 'observation' | 'irrigation' | 'fertilizer' | 'pest' | 'harvest';
  categoryTe: string;
  audioDurationSec?: number;
  autoSaved: boolean;
  notesTe?: string;
  cropType: CropType;
}

export interface PeerFarmer {
  id: string;
  nameTe: string;
  nameEn: string;
  villageTe: string;
  cropTe: string;
  experienceYears: number;
  imageUrl: string;
  solvedIssueTe: string;
  successRatePercent: number;
  phone?: string;
  adviceQuoteTe: string;
}

export interface SeedVarietyInfo {
  id: string;
  nameTe: string;
  nameEn: string;
  cropTe: string;
  cropType: CropType;
  durationDays: string;
  avgYieldPerAcre: string;
  resistanceFeaturesTe: string[];
  bestSeasonTe: string;
  pricePerBag: number;
  imageUrl: string;
}

export interface VoiceMessage {
  id: string;
  sender: 'user' | 'assistant';
  textTe: string;
  textEn?: string;
  voiceScriptTe?: string;
  timestamp: string;
  audioPlaying?: boolean;
  needsEscalation?: boolean;
  topic?: 'disease' | 'weather' | 'mandi' | 'irrigation' | 'general';
}

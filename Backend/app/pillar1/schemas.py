from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class FarmJournalBase(BaseModel):
    channel: str = Field(default="BROWSER", description="Channel source: BROWSER, MOBILE, PHONE")
    crop: Optional[str] = None
    disease_symptom: Optional[str] = None
    region: Optional[str] = None
    season: Optional[str] = None

class AudioIngestBase64Request(BaseModel):
    audio_base64: str = Field(description="Base64 encoded audio string")
    channel: str = Field(default="BROWSER", description="Channel type: BROWSER, MOBILE, PHONE")
    language_code: Optional[str] = Field(default="en-US", description="Farmer spoken language code")
    latitude: Optional[float] = Field(default=None, description="Optional GPS latitude")
    longitude: Optional[float] = Field(default=None, description="Optional GPS longitude")

class FarmJournalResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    channel: str
    transcription: str
    confidence: float
    detected_language: str
    crop: Optional[str] = None
    disease_symptom: Optional[str] = None
    region: Optional[str] = None
    season: Optional[str] = None
    advice_text: Optional[str] = None
    advice_source: Optional[str] = None
    cost_benefit: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_fully_processed: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JournalStatusResponse(BaseModel):
    id: UUID
    is_fully_processed: bool
    transcription: str
    advice_text: Optional[str] = None
    advice_source: Optional[str] = None
    cost_benefit: Optional[str] = None
    tts_prompt: Optional[str] = None
    audio_base64: Optional[str] = None

class VoiceTalkRequest(BaseModel):
    text: Optional[str] = Field(default=None, description="Direct spoken transcript text (e.g. from browser Web Speech API)")
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded audio string")
    channel: str = Field(default="BROWSER", description="Channel type: BROWSER, MOBILE, PHONE")
    language_code: Optional[str] = Field(default="en-US", description="Farmer spoken language code")
    latitude: Optional[float] = Field(default=None, description="Optional GPS latitude")
    longitude: Optional[float] = Field(default=None, description="Optional GPS longitude")

class VoiceTalkResponse(BaseModel):
    journal_id: UUID
    transcription: str
    confidence: float
    detected_language: str
    crop: Optional[str] = None
    disease_symptom: Optional[str] = None
    region: Optional[str] = None
    season: Optional[str] = None
    confirmation_text: str  # e.g., "Logged: Farmer Patil in Jalgaon reported pink bollworm..."
    advice_text: str        # fallback/main advice
    advice_short: str       # short dual-mode voice advice
    advice_detailed: str    # detailed dual-mode text advice
    advice_source: str
    cost_benefit: str
    tts_prompt: str
    audio_base64: Optional[str] = None
    is_fully_processed: bool = True


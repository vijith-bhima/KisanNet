from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class KnowledgeBaseIngestRequest(BaseModel):
    title: str = Field(description="Advisory / research paper title")
    content: str = Field(description="Body text of agricultural recommendation")
    crop: Optional[str] = Field(default=None, description="Target crop e.g. Paddy, Wheat")
    disease_symptom: Optional[str] = Field(default=None, description="Target disease or pest symptom")
    region: Optional[str] = Field(default=None, description="Applicable region e.g. Punjab, South India")
    season: Optional[str] = Field(default=None, description="Applicable season e.g. Kharif")
    source: str = Field(description="KVK / ICAR / University scientific source reference")
    cost_per_acre: Optional[str] = Field(default=None, description="Optional cost per acre in INR")
    time_to_effect: Optional[str] = Field(default=None, description="Optional time to effect (e.g. 3 days)")

class KnowledgeBaseResponse(BaseModel):
    id: UUID
    title: str
    content: str
    crop: Optional[str] = None
    disease_symptom: Optional[str] = None
    region: Optional[str] = None
    season: Optional[str] = None
    source: str
    cost_per_acre: Optional[str] = None
    time_to_effect: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdviceGenerationRequest(BaseModel):
    journal_id: UUID = Field(description="Target farm_journals UUID to process")

class AdviceGenerationResponse(BaseModel):
    journal_id: UUID
    advice_text: str
    advice_short: str
    advice_detailed: str
    advice_source: str
    cost_benefit: str
    tts_prompt: str
    audio_base64: Optional[str] = None
    is_fully_processed: bool
    confirmation_text: Optional[str] = None

class PushSubscriptionRequest(BaseModel):
    webhook_url: str = Field(description="Push target URL for immediate advisory delivery")
    farmer_id: Optional[UUID] = None

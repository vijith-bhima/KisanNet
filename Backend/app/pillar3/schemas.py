from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class VoiceFeedbackTextRequest(BaseModel):
    journal_id: UUID = Field(description="Farm journal UUID for which feedback is given")
    advice_identifier: str = Field(description="Identifier or citation source of the advice")
    feedback_text: str = Field(description="Spoken feedback transcript")
    language_code: Optional[str] = Field(default="en-US", description="Language code e.g. hi-IN, en-US, pt-BR")

class FeedbackResponse(BaseModel):
    id: UUID
    journal_id: UUID
    farmer_id: UUID
    advice_identifier: str
    feedback_intent: str
    score: float
    retry_count: int
    needs_human_review: bool
    calculated_wilson_score: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdviceTrustMetricsResponse(BaseModel):
    advice_identifier: str
    total_feedback_count: int
    positive_count: int
    negative_count: int
    clarification_count: int
    retry_count: int
    human_review_count: int
    wilson_lower_bound: float
    bayesian_mean_score: float

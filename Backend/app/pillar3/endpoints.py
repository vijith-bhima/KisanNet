import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Response, status

from app.config import settings
from app.auth import get_current_farmer, FarmerUser
from app.redis_client import redis_client
from app.google_speech import google_speech_client
from app.pillar3.intent_classifier import voice_intent_classifier
from app.bigquery_client import bq_client
from app.pillar3.schemas import (
    VoiceFeedbackTextRequest,
    FeedbackResponse,
    AdviceTrustMetricsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pillar3", tags=["Pillar 3: Community Trust Scores"])

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_voice_feedback(
    journal_id: str = Form(...),
    advice_identifier: str = Form(...),
    language_code: str = Form("en-US"),
    file: Optional[UploadFile] = File(None),
    feedback_text: Optional[str] = Form(None),
    farmer: FarmerUser = Depends(get_current_farmer)
):
    """
    Submits voice feedback (audio upload or transcribed text) for an agricultural advisory to BigQuery.
    """
    farmer_id = farmer.farmer_id

    retry_count = await redis_client.increment_retry_count(str(journal_id), str(farmer_id))
    needs_human_review = retry_count > settings.MAX_FEEDBACK_RETRIES

    transcript = feedback_text or ""
    if file:
        audio_bytes = await file.read()
        stt_res = await google_speech_client.transcribe_audio(audio_bytes, language_code=language_code)
        transcript = stt_res.get("transcription", "")

    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Audio or feedback_text must be provided")

    intent, intent_confidence = voice_intent_classifier.classify_intent(transcript, language_code)
    
    # BigQuery feedback value: 1 = worked, 2 = didn't work
    numeric_feedback = 1 if intent == "POSITIVE" else 2

    # Insert feedback into BigQuery
    try:
        bq_client.insert_feedback(journal_id, farmer_id, numeric_feedback, transcript, intent_confidence)
    except Exception as e:
        logger.error(f"Failed to insert feedback to BigQuery: {e}")

    # Fetch updated trust score from BigQuery materialized view
    score_data = bq_client.get_trust_score(advice_identifier)
    w_bound_pct = 0.0
    if score_data:
        w_bound_raw = score_data.get("wilson_lower_bound", 0.0)
        w_bound_pct = w_bound_raw * 100.0 if w_bound_raw <= 1.0 else w_bound_raw

    # Convert journal_id string to UUID if possible for the response
    try:
        journal_uuid = uuid.UUID(journal_id)
    except Exception:
        journal_uuid = uuid.uuid4()

    return FeedbackResponse(
        id=uuid.uuid4(),
        journal_id=journal_uuid,
        farmer_id=uuid.UUID(farmer_id),
        advice_identifier=advice_identifier,
        feedback_intent=intent,
        score=1.0 if intent == "POSITIVE" else 0.0,
        retry_count=retry_count,
        needs_human_review=needs_human_review,
        calculated_wilson_score=w_bound_pct,
        created_at=None
    )

@router.post("/feedback-json", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_voice_feedback_json(
    payload: VoiceFeedbackTextRequest,
    farmer: FarmerUser = Depends(get_current_farmer)
):
    """
    JSON payload endpoint for feedback text submission to BigQuery.
    """
    farmer_id = farmer.farmer_id
    journal_id_str = str(payload.journal_id)
    
    retry_count = await redis_client.increment_retry_count(journal_id_str, str(farmer_id))
    needs_human_review = retry_count > settings.MAX_FEEDBACK_RETRIES

    intent, _ = voice_intent_classifier.classify_intent(payload.feedback_text, payload.language_code or "en-US")
    numeric_feedback = 1 if intent == "POSITIVE" else 2

    try:
        bq_client.insert_feedback(journal_id_str, farmer_id, numeric_feedback, payload.feedback_text, 0.99)
    except Exception as e:
        logger.error(f"Failed to insert feedback to BigQuery: {e}")

    score_data = bq_client.get_trust_score(payload.advice_identifier)
    w_bound_pct = 0.0
    if score_data:
        w_bound_raw = score_data.get("wilson_lower_bound", 0.0)
        w_bound_pct = w_bound_raw * 100.0 if w_bound_raw <= 1.0 else w_bound_raw

    return FeedbackResponse(
        id=uuid.uuid4(),
        journal_id=payload.journal_id,
        farmer_id=uuid.UUID(farmer_id),
        advice_identifier=payload.advice_identifier,
        feedback_intent=intent,
        score=1.0 if intent == "POSITIVE" else 0.0,
        retry_count=retry_count,
        needs_human_review=needs_human_review,
        calculated_wilson_score=w_bound_pct,
        created_at=None
    )

@router.post("/twilio/feedback-webhook")
async def twilio_phone_feedback_webhook(
    SpeechResult: Optional[str] = Form(None),
    Digits: Optional[str] = Form(None),
    JournalId: Optional[str] = Form(None),
    AdviceIdentifier: Optional[str] = Form("KVK-ADVISORY-STD"),
    From: Optional[str] = Form(None)
):
    """
    Stateless Twilio Voice Webhook for feedback phone calls using BigQuery.
    """
    if (Digits or SpeechResult) and JournalId:
        farmer_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, From or "phone-caller"))

        if Digits:
            dig = Digits.strip()
            if dig == "1":
                numeric_feedback = 1
                transcript = "[DTMF Press 1 - POSITIVE]"
            elif dig == "2":
                numeric_feedback = 2
                transcript = "[DTMF Press 2 - NEGATIVE]"
            else:
                numeric_feedback = 2
                transcript = f"[DTMF Press {dig}]"
        else:
            intent, _ = voice_intent_classifier.classify_intent(SpeechResult, "en-US")
            numeric_feedback = 1 if intent == "POSITIVE" else 2
            transcript = SpeechResult

        try:
            bq_client.insert_feedback(str(JournalId), farmer_id, numeric_feedback, transcript, 0.99)
        except Exception as e:
            logger.error(f"Failed to insert feedback to BigQuery: {e}")

        score_data = bq_client.get_trust_score(AdviceIdentifier)
        w_bound_pct = 0.0
        if score_data:
            w_bound_pct = score_data.get("wilson_lower_bound", 0.0) * 100.0

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you. Your feedback has been recorded. Current community trust score is {round(w_bound_pct)} percent.</Say>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    else:
        twiml_prompt = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="dtmf speech" numDigits="1" timeout="5" action="/api/v1/pillar3/twilio/feedback-webhook?JournalId={JournalId or ''}&amp;AdviceIdentifier={AdviceIdentifier or ''}" method="POST">
        <Say>Press 1 if this worked. Press 2 if it did not. Or speak your feedback now.</Say>
    </Gather>
</Response>"""
        return Response(content=twiml_prompt, media_type="application/xml")

@router.get("/scores/{advice_identifier}", response_model=AdviceTrustMetricsResponse)
async def get_advice_trust_metrics(advice_identifier: str):
    """
    Returns full trust score metrics breakdown from BigQuery.
    """
    score_data = bq_client.get_trust_score(advice_identifier)
    if not score_data:
        return AdviceTrustMetricsResponse(
            advice_identifier=advice_identifier,
            total_feedback_count=0,
            positive_feedback_count=0,
            negative_feedback_count=0,
            wilson_lower_bound=0.0,
            bayesian_mean_score=0.5
        )

    return AdviceTrustMetricsResponse(
        advice_identifier=advice_identifier,
        total_feedback_count=score_data.get("total_unique_farmers", 0),
        positive_feedback_count=score_data.get("positive_votes", 0),
        negative_feedback_count=score_data.get("negative_votes", 0),
        wilson_lower_bound=score_data.get("wilson_lower_bound", 0.0),
        bayesian_mean_score=score_data.get("bayesian_score", 0.5)
    )

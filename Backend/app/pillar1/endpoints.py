import base64
import uuid
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Response, status

from app.auth import get_current_farmer, FarmerUser
from app.google_speech import google_speech_client
from app.google_llm import google_llm_client
from app.google_tts import google_tts_client
from app.firestore_client import firestore_client
from app.bigquery_client import bq_client
from app.pillar5.escalation import escalate_to_human_expert
from app.pillar4.matching_engine import SIMILARITY_THRESHOLD
from app.pillar1.schemas import (
    FarmJournalResponse,
    AudioIngestBase64Request,
    JournalStatusResponse,
    VoiceTalkRequest,
    VoiceTalkResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Pillar 1: Hands-Free Farm Documentation"])

@router.get("/debug-gemini")
async def debug_gemini():
    import httpx
    api_key = google_llm_client.get_active_api_key()
    
    candidates = []
    if google_llm_client.model_name:
        candidates.append(google_llm_client.model_name)
    for c in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
        if c not in candidates:
            candidates.append(c)

    results = []
    for model_candidate in candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Say ok."}]}]
        }
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post(url, json=payload)
                results.append({
                    "model": model_candidate,
                    "status_code": resp.status_code,
                    "response": resp.json() if resp.status_code == 200 else resp.text
                })
        except Exception as e:
            results.append({
                "model": model_candidate,
                "error": str(e)
            })

    return {
        "api_key_configured": bool(api_key),
        "api_key_preview": api_key[:8] + "..." if api_key else None,
        "results": results,
        "kb_count": "Moved to BigQuery",
        "kb_samples": []
    }


import math

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

async def _get_farmer_profile_info(farmer_id_str: str):
    """Retrieves farmer name and region from Firestore with defaults."""
    farmer_name = "Patil"
    farmer_region = "Jalgaon"
    # Placeholder for Firestore fetch if needed
    return farmer_name, farmer_region


@router.post("/pillar1/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_audio(
    file: Optional[UploadFile] = File(None),
    channel: str = Form("BROWSER"),
    language_code: str = Form("en-US"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    farmer: FarmerUser = Depends(get_current_farmer)
):
    if file is None:
        raise HTTPException(status_code=400, detail="Audio file must be provided in form data")

    audio_bytes = await file.read()
    stt_result = await google_speech_client.transcribe_audio(audio_bytes=audio_bytes, language_code=language_code)

    transcription = stt_result.get("transcription")
    if not transcription:
        raise HTTPException(status_code=422, detail="Audio transcription failed.")

    confidence = stt_result["confidence"]
    detected_lang = stt_result["detected_language"]

    extracted = await google_llm_client.extract_journal_fields(transcription)
    farmer_name, farmer_region = await _get_farmer_profile_info(farmer.farmer_id)
    final_region = extracted.get("region") or farmer_region

    journal_data = {
        "farmer_id": farmer.farmer_id,
        "channel": channel,
        "transcription": transcription,
        "confidence": confidence,
        "detected_language": detected_lang,
        "crop": extracted.get("crop"),
        "disease_symptom": extracted.get("disease_symptom"),
        "region": final_region,
        "season": extracted.get("season"),
        "latitude": latitude,
        "longitude": longitude,
        "is_fully_processed": False,
        "created_at": datetime.now().isoformat()
    }
    
    journal_id = firestore_client.create_journal(journal_data)
    journal_data["id"] = journal_id
    return journal_data


@router.post("/pillar1/ingest-json", status_code=status.HTTP_201_CREATED)
async def ingest_audio_json(
    payload: AudioIngestBase64Request,
    farmer: FarmerUser = Depends(get_current_farmer)
):
    try:
        audio_bytes = base64.b64decode(payload.audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 audio content")

    stt_result = await google_speech_client.transcribe_audio(audio_bytes=audio_bytes, language_code=payload.language_code or "en-US")
    transcription = stt_result.get("transcription")
    if not transcription:
        raise HTTPException(status_code=422, detail="Audio transcription failed.")

    confidence = stt_result["confidence"]
    detected_lang = stt_result["detected_language"]

    extracted = await google_llm_client.extract_journal_fields(transcription)
    farmer_name, farmer_region = await _get_farmer_profile_info(farmer.farmer_id)
    final_region = extracted.get("region") or farmer_region

    journal_data = {
        "farmer_id": farmer.farmer_id,
        "channel": payload.channel,
        "transcription": transcription,
        "confidence": confidence,
        "detected_language": detected_lang,
        "crop": extracted.get("crop"),
        "disease_symptom": extracted.get("disease_symptom"),
        "region": final_region,
        "season": extracted.get("season"),
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "is_fully_processed": False,
        "created_at": datetime.now().isoformat()
    }
    
    journal_id = firestore_client.create_journal(journal_data)
    journal_data["id"] = journal_id
    return journal_data


@router.post("/pillar1/twilio/webhook")
async def twilio_phone_webhook(
    SpeechResult: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
    From: Optional[str] = Form(None)
):
    if SpeechResult:
        extracted = await google_llm_client.extract_journal_fields(SpeechResult)
        farmer_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, From or "phone-caller"))
        
        journal_data = {
            "farmer_id": farmer_id,
            "channel": "PHONE",
            "transcription": SpeechResult,
            "confidence": 0.90,
            "detected_language": "en-US",
            "crop": extracted.get("crop"),
            "disease_symptom": extracted.get("disease_symptom"),
            "region": extracted.get("region"),
            "season": extracted.get("season"),
            "is_fully_processed": False,
            "created_at": datetime.now().isoformat()
        }
        firestore_client.create_journal(journal_data)

        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you. Your farm observation regarding {extracted.get('crop', 'your crop')} has been logged into KisanNet. AI advice is being processed.</Say>
</Response>"""
        return Response(content=twiml_response, media_type="application/xml")
    else:
        twiml_prompt = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="5" action="/api/v1/pillar1/twilio/webhook" method="POST">
        <Say>Welcome to KisanNet voice platform. Please speak your crop observation after the tone.</Say>
    </Gather>
</Response>"""
        return Response(content=twiml_prompt, media_type="application/xml")


@router.get("/journal-status/{journal_id}")
@router.get("/pillar1/journal-status/{journal_id}")
async def get_journal_status(journal_id: str):
    doc = None
    if firestore_client.client:
        doc_ref = firestore_client.client.collection('farm_journals').document(journal_id)
        doc = doc_ref.get()

    if not doc or not doc.exists:
        raise HTTPException(status_code=404, detail="Farm journal record not found")

    journal = doc.to_dict()
    audio_b64 = None
    tts_prompt = None

    if journal.get("is_fully_processed") and journal.get("advice_text"):
        tts_prompt = f"Advice for {journal.get('crop') or 'your crop'}: {journal.get('advice_text')}. Source: {journal.get('advice_source')}."
        tts_result = await google_tts_client.synthesize_speech(
            text=tts_prompt,
            language_code=journal.get("detected_language") or "en-US"
        )
        audio_b64 = tts_result.get("audio_base64")

    journal["id"] = journal_id
    journal["tts_prompt"] = tts_prompt
    journal["audio_base64"] = audio_b64
    return journal


@router.post("/voice/talk", response_model=VoiceTalkResponse, status_code=status.HTTP_200_OK)
@router.post("/pillar1/voice/talk", response_model=VoiceTalkResponse, status_code=status.HTTP_200_OK)
async def direct_voice_talk(
    payload: VoiceTalkRequest,
    farmer: FarmerUser = Depends(get_current_farmer)
):
    language_code = payload.language_code or "en-US"
    transcription = ""
    confidence = 0.98
    detected_lang = language_code

    if payload.text and payload.text.strip():
        transcription = payload.text.strip()
    elif payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
            stt_result = await google_speech_client.transcribe_audio(audio_bytes=audio_bytes, language_code=language_code)
            transcription = stt_result.get("transcription") or ""
            confidence = stt_result.get("confidence", 0.0)
            detected_lang = stt_result.get("detected_language", language_code)
            if not transcription:
                raise HTTPException(status_code=422, detail="Could not transcribe audio.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Audio decode/STT error: %s", e)
            raise HTTPException(status_code=400, detail=f"Invalid audio_base64 or STT failure: {e}")
    else:
        raise HTTPException(status_code=400, detail="Either 'text' or 'audio_base64' must be provided.")

    farmer_name, farmer_region = await _get_farmer_profile_info(farmer.farmer_id)

    # Geofencing check
    if firestore_client.client:
        try:
            farmer_doc = firestore_client.client.collection('farmers').document(str(farmer.farmer_id)).get()
            if farmer_doc.exists:
                f_data = farmer_doc.to_dict()
                f_lat, f_lon = f_data.get('latitude'), f_data.get('longitude')
                if f_lat and f_lon and payload.latitude and payload.longitude:
                    dist = _haversine_distance(f_lat, f_lon, payload.latitude, payload.longitude)
                    if dist > 200:
                        logger.warning(f"GPS mismatch for {farmer.farmer_id}. Distance: {dist:.2f}m (>200m). Logging for Pillar 3 Trust Math.")
        except Exception as e:
            logger.warning(f"Geofencing check failed: {e}")

    # 1. Routing step: Classify query as CROP_ISSUE or SCHEME_QUESTION
    classification_prompt = (
        "Classify the following farmer query into one of three categories:\n"
        "1. CROP_ISSUE (if it's about crop diseases, pests, soil, irrigation, etc.)\n"
        "2. SCHEME_QUESTION (if it's about government schemes, loans, PM-KISAN, credit cards, insurance, subsidies)\n"
        "3. AMBIGUOUS (if it could be both or neither)\n"
        f"Query: '{transcription}'\n"
        "Respond with EXACTLY ONE WORD from the categories above."
    )
    from google import genai as google_genai
    _cls_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    classification = "CROP_ISSUE"
    try:
        cls_response = await asyncio.to_thread(
            _cls_client.models.generate_content,
            model="gemini-2.0-flash",
            contents=classification_prompt,
        )
        classification = cls_response.text.strip().upper()
    except Exception as e:
        logger.warning(f"Classification failed, defaulting to CROP_ISSUE: {e}")

    # 2. RAG search in BigQuery
    relevant_docs = []
    try:
        if classification == "SCHEME_QUESTION":
            relevant_docs = bq_client.rag_search_scheme(transcription, top_k=3)
        elif classification == "CROP_ISSUE":
            relevant_docs = bq_client.rag_search_crop(transcription, top_k=3)
        else: # AMBIGUOUS
            docs_scheme = bq_client.rag_search_scheme(transcription, top_k=3)
            docs_crop = bq_client.rag_search_crop(transcription, top_k=3)
            relevant_docs = sorted(docs_scheme + docs_crop, key=lambda x: x.get("similarity", 0.0), reverse=True)[:3]
    except Exception as e:
        logger.warning("BigQuery RAG search failed: %s", e)

    max_similarity = max([doc["similarity"] for doc in relevant_docs]) if relevant_docs else 0.0

    journal_id = str(uuid.uuid4())
    farmer_id = farmer.farmer_id
    now = datetime.now()

    # 3-Tier Confidence Check
    if max_similarity < 0.70 and len(relevant_docs) > 0:
        await escalate_to_human_expert(
            farmer_id=farmer_id,
            query=transcription,
            crop_type="General",
            disease_name=None,
            region=farmer_region,
            season="Kharif"
        )
        advice_short = "I'm not fully sure about this. Connecting you to your local Krishi Vigyan Kendra. Press 1 to connect."
        if language_code.startswith("hi"):
            advice_short = "मैं इसके बारे में पूरी तरह से निश्चित नहीं हूँ। मैं आपको आपके स्थानीय कृषि विज्ञान केंद्र से जोड़ रहा हूँ। कॉल करने के लिए 1 दबाएं।"
        advice_detailed = advice_short
        crop = "General"
        disease_symptom = "Unknown"
        region = farmer_region
        season = "Kharif"
        advice_source = "Krishi Vigyan Kendra Escalation"
        cost_benefit = "N/A"
    else:
        adv_data = await google_llm_client.generate_fast_multilingual_advice(
            transcription=transcription,
            language_code=language_code,
            context_docs=relevant_docs
        )
        crop = adv_data.get("crop") or ""
        disease_symptom = adv_data.get("disease_symptom") or ""
        region = adv_data.get("region") or farmer_region
        season = adv_data.get("season") or ""
        advice_short = adv_data.get("advice_short") or adv_data.get("answer_text") or ""
        advice_detailed = adv_data.get("advice_detailed") or adv_data.get("answer_text") or ""
        advice_source = adv_data.get("source") or ""
        cost_benefit = adv_data.get("cost_benefit") or ""
        
        # Moderate Confidence Disclaimer
        if 0.70 <= max_similarity < 0.85:
            if language_code.startswith("hi"):
                advice_short += " (यह सलाह अनुमानित है, कृपया KVK विशेषज्ञ से पुष्टि करें।)"
            else:
                advice_short += " (This advice is estimated, please verify with a KVK expert.)"

    final_region = region or farmer_region

    confirmation_text = await google_llm_client.generate_conversational_response(
        prompt_type="logging_confirmation",
        facts={
            "farmer_name": farmer_name,
            "region": final_region,
            "crop": crop,
            "issue": disease_symptom or "crop issue",
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%B %d, %Y")
        },
        language_code=language_code
    )

    journal_data = {
        "id": journal_id,
        "farmer_id": farmer_id,
        "channel": payload.channel,
        "transcription": transcription,
        "confidence": confidence,
        "detected_language": detected_lang,
        "crop": crop,
        "disease_symptom": disease_symptom,
        "region": final_region,
        "season": season,
        "advice_text": advice_short,
        "solution_text": advice_detailed,
        "advice_source": advice_source,
        "cost_benefit": cost_benefit,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "is_fully_processed": True,
        "created_at": now.isoformat()
    }
    
    if firestore_client.client:
        try:
            firestore_client.client.collection('farm_journals').document(journal_id).set(journal_data)
        except Exception as e:
            logger.warning(f"Failed to save journal to firestore: {e}")

    audio_base64 = None
    tts_prompt = f"<speak>{confirmation_text}<break time=\"800ms\"/>{advice_short}</speak>"
    try:
        tts_res = await google_tts_client.synthesize_speech(tts_prompt, language_code=language_code)
        audio_base64 = tts_res.get("audio_base64")
    except Exception as e:
        logger.warning("TTS synthesis skipped: %s", e)

    return VoiceTalkResponse(
        journal_id=uuid.UUID(journal_id),
        transcription=transcription,
        confidence=confidence,
        detected_language=detected_lang,
        crop=crop,
        disease_symptom=disease_symptom,
        region=final_region,
        season=season,
        confirmation_text=confirmation_text,
        advice_text=advice_short,
        advice_short=advice_short,
        advice_detailed=advice_detailed,
        advice_source=advice_source,
        cost_benefit=str(cost_benefit),
        tts_prompt=tts_prompt,
        audio_base64=audio_base64,
        is_fully_processed=True
    )


@router.post("/voice/talk-audio", response_model=VoiceTalkResponse, status_code=status.HTTP_200_OK)
@router.post("/pillar1/voice/talk-audio", response_model=VoiceTalkResponse, status_code=status.HTTP_200_OK)
async def direct_voice_talk_audio(
    file: Optional[UploadFile] = File(None),
    channel: str = Form("BROWSER"),
    language_code: str = Form("en-US"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    farmer: FarmerUser = Depends(get_current_farmer)
):
    if not file:
        raise HTTPException(status_code=400, detail="Audio file is required.")

    audio_bytes = await file.read()
    stt_result = await google_speech_client.transcribe_audio(audio_bytes=audio_bytes, language_code=language_code)
    transcription = stt_result.get("transcription") or ""
    confidence = stt_result.get("confidence", 0.0)
    detected_lang = stt_result.get("detected_language", language_code)

    if not transcription:
        raise HTTPException(status_code=422, detail="Could not transcribe the uploaded audio.")

    farmer_name, farmer_region = await _get_farmer_profile_info(farmer.farmer_id)

    # Geofencing check
    if firestore_client.client:
        try:
            farmer_doc = firestore_client.client.collection('farmers').document(str(farmer.farmer_id)).get()
            if farmer_doc.exists:
                f_data = farmer_doc.to_dict()
                f_lat, f_lon = f_data.get('latitude'), f_data.get('longitude')
                if f_lat and f_lon and latitude and longitude:
                    dist = _haversine_distance(f_lat, f_lon, latitude, longitude)
                    if dist > 200:
                        logger.warning(f"GPS mismatch for {farmer.farmer_id}. Distance: {dist:.2f}m (>200m). Logging for Pillar 3 Trust Math.")
        except Exception as e:
            logger.warning(f"Geofencing check failed: {e}")

    # 1. Routing step: Classify query as CROP_ISSUE or SCHEME_QUESTION
    classification_prompt = (
        "Classify the following farmer query into one of three categories:\n"
        "1. CROP_ISSUE (if it's about crop diseases, pests, soil, irrigation, etc.)\n"
        "2. SCHEME_QUESTION (if it's about government schemes, loans, PM-KISAN, credit cards, insurance, subsidies)\n"
        "3. AMBIGUOUS (if it could be both or neither)\n"
        f"Query: '{transcription}'\n"
        "Respond with EXACTLY ONE WORD from the categories above."
    )
    from google import genai as google_genai
    _cls_client2 = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    classification = "CROP_ISSUE"
    try:
        cls_response2 = await asyncio.to_thread(
            _cls_client2.models.generate_content,
            model="gemini-2.0-flash",
            contents=classification_prompt,
        )
        classification = cls_response2.text.strip().upper()
    except Exception as e:
        logger.warning(f"Classification failed, defaulting to CROP_ISSUE: {e}")

    # 2. RAG search in BigQuery
    relevant_docs = []
    try:
        if classification == "SCHEME_QUESTION":
            relevant_docs = bq_client.rag_search_scheme(transcription, top_k=3)
        elif classification == "CROP_ISSUE":
            relevant_docs = bq_client.rag_search_crop(transcription, top_k=3)
        else: # AMBIGUOUS
            docs_scheme = bq_client.rag_search_scheme(transcription, top_k=3)
            docs_crop = bq_client.rag_search_crop(transcription, top_k=3)
            relevant_docs = sorted(docs_scheme + docs_crop, key=lambda x: x.get("similarity", 0.0), reverse=True)[:3]
    except Exception as e:
        logger.warning("RAG search failed: %s", e)

    max_similarity = max([doc["similarity"] for doc in relevant_docs]) if relevant_docs else 0.0

    journal_id = str(uuid.uuid4())
    farmer_id = farmer.farmer_id
    now = datetime.now()

    # 3-Tier Confidence Check
    if max_similarity < 0.70 and len(relevant_docs) > 0:
        await escalate_to_human_expert(
            farmer_id=farmer_id,
            query=transcription,
            crop_type="General",
            disease_name=None,
            region=farmer_region,
            season="Kharif"
        )
        advice_short = "I'm not fully sure about this. Connecting you to your local Krishi Vigyan Kendra. Press 1 to connect."
        if language_code.startswith("hi"):
            advice_short = "मैं इसके बारे में पूरी तरह से निश्चित नहीं हूँ। मैं आपको आपके स्थानीय कृषि विज्ञान केंद्र से जोड़ रहा हूँ। कॉल करने के लिए 1 दबाएं।"
        advice_detailed = advice_short
        crop = "General"
        disease_symptom = "Unknown"
        region = farmer_region
        season = "Kharif"
        advice_source = "Krishi Vigyan Kendra Escalation"
        cost_benefit = "N/A"
    else:
        adv_data = await google_llm_client.generate_fast_multilingual_advice(
            transcription=transcription,
            language_code=language_code,
            context_docs=relevant_docs
        )
        crop = adv_data.get("crop") or ""
        disease_symptom = adv_data.get("disease_symptom") or ""
        region = adv_data.get("region") or farmer_region
        season = adv_data.get("season") or ""
        advice_short = adv_data.get("advice_short") or adv_data.get("answer_text") or ""
        advice_detailed = adv_data.get("advice_detailed") or adv_data.get("answer_text") or ""
        advice_source = adv_data.get("source") or ""
        cost_benefit = adv_data.get("cost_benefit") or ""

        # Moderate Confidence Disclaimer
        if 0.70 <= max_similarity < 0.85:
            if language_code.startswith("hi"):
                advice_short += " (यह सलाह अनुमानित है, कृपया KVK विशेषज्ञ से पुष्टि करें।)"
            else:
                advice_short += " (This advice is estimated, please verify with a KVK expert.)"

    final_region = region or farmer_region

    confirmation_text = await google_llm_client.generate_conversational_response(
        prompt_type="logging_confirmation",
        facts={
            "farmer_name": farmer_name,
            "region": final_region,
            "crop": crop,
            "issue": disease_symptom or "crop issue",
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%B %d, %Y")
        },
        language_code=language_code
    )

    journal_data = {
        "id": journal_id,
        "farmer_id": farmer_id,
        "channel": channel,
        "transcription": transcription,
        "confidence": confidence,
        "detected_language": detected_lang,
        "crop": crop,
        "disease_symptom": disease_symptom,
        "region": final_region,
        "season": season,
        "advice_text": advice_short,
        "solution_text": advice_detailed,
        "advice_source": advice_source,
        "cost_benefit": cost_benefit,
        "latitude": latitude,
        "longitude": longitude,
        "is_fully_processed": True,
        "created_at": now.isoformat()
    }
    
    if firestore_client.client:
        try:
            firestore_client.client.collection('farm_journals').document(journal_id).set(journal_data)
        except Exception as e:
            logger.warning(f"Failed to save journal to firestore: {e}")

    audio_base64 = None
    tts_prompt = f"<speak>{confirmation_text}<break time=\"800ms\"/>{advice_short}</speak>"
    try:
        tts_res = await google_tts_client.synthesize_speech(tts_prompt, language_code=language_code)
        audio_base64 = tts_res.get("audio_base64")
    except Exception as e:
        logger.warning("TTS synthesis skipped: %s", e)

    return VoiceTalkResponse(
        journal_id=uuid.UUID(journal_id),
        transcription=transcription,
        confidence=confidence,
        detected_language=detected_lang,
        crop=crop,
        disease_symptom=disease_symptom,
        region=final_region,
        season=season,
        confirmation_text=confirmation_text,
        advice_text=advice_short,
        advice_short=advice_short,
        advice_detailed=advice_detailed,
        advice_source=advice_source,
        cost_benefit=str(cost_benefit),
        tts_prompt=tts_prompt,
        audio_base64=audio_base64,
        is_fully_processed=True
    )


class WeatherAdvisoryRequest(BaseModel):
    crop_name: str = "Paddy"
    location: str = "Warangal, Telangana"
    temperature: float = 31.0
    feels_like: float = 33.0
    humidity: float = 65.0
    wind_speed: float = 12.0
    precipitation_prob: float = 20.0
    condition: str = "Clear Sky"
    language_code: str = "te-IN"


@router.post("/weather/ai-advisory", tags=["Weather AI Advisory"])
async def get_weather_ai_advisory(req: WeatherAdvisoryRequest):
    """
    Generates real-time AI agricultural advisory using Gemini 2.0 Flash based on live weather parameters.
    """
    return await google_llm_client.generate_weather_ai_advisory(
        crop_name=req.crop_name,
        location=req.location,
        temperature=req.temperature,
        feels_like=req.feels_like,
        humidity=req.humidity,
        wind_speed=req.wind_speed,
        precipitation_prob=req.precipitation_prob,
        condition=req.condition,
        language_code=req.language_code
    )

# =========================================================================
# AGENTIC AGRICULTURAL RESEARCH ASSISTANT (NEW UPGRADE)
# =========================================================================

from app.trusted_sources import trusted_sources
from app.agentic_research import agentic_researcher

class TrustedSourceModel(BaseModel):
    name: str
    base_url: str
    description: Optional[str] = ""
    enabled: Optional[bool] = True

@router.get("/api/v1/sources", tags=["Agentic Research"])
async def get_trusted_sources():
    """List all trusted domains configured for Agentic Research."""
    return {"sources": trusted_sources.get_all_sources()}

@router.post("/api/v1/sources", tags=["Agentic Research"])
async def add_trusted_source(src: TrustedSourceModel):
    """Add a new trusted domain."""
    new_src = trusted_sources.add_source(src.name, src.base_url, src.description)
    return {"status": "success", "source": new_src}

@router.put("/api/v1/sources/{source_id}", tags=["Agentic Research"])
async def update_trusted_source(source_id: str, updates: dict):
    """Update a trusted domain's configuration."""
    updated = trusted_sources.update_source(source_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "success", "source": updated}

@router.delete("/api/v1/sources/{source_id}", tags=["Agentic Research"])
async def delete_trusted_source(source_id: str):
    """Delete a trusted domain."""
    success = trusted_sources.delete_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "success", "message": "Deleted"}

class AgenticResearchRequest(BaseModel):
    question: str
    language: str = "Telugu"

@router.post("/api/v1/agent/research", tags=["Agentic Research"])
async def execute_agentic_research(req: AgenticResearchRequest):
    """Execute the full autonomous agricultural research workflow."""
    final_answer = await agentic_researcher.run_workflow(req.question, req.language)
    return {"status": "success", "response": final_answer}
import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status

from app.config import settings
from app.auth import FarmerUser
from app.google_speech import google_speech_client
from app.google_llm import google_llm_client
from app.google_tts import google_tts_client
from app.firestore_client import firestore_client
from app.bigquery_client import bq_client
from app.pillar5.escalation import escalate_to_human_expert
from app.pillar4.schemas import ConnectRequest
from app.pillar4.matching_engine import SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/twilio/ivr", tags=["Twilio IVR Voice Channel Adapter"])

async def _lookup_farmer_info(phone: str):
    """Looks up farmer record by phone number in Firestore, falls back to defaults."""
    farmer_name = "Patil"
    farmer_region = "Jalgaon"
    farmer_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, phone))
    
    try:
        # Simple Firestore query by phone
        docs = firestore_client.client.collection('farmers').where('phone_number', '==', phone).limit(1).stream()
        for doc in docs:
            row = doc.to_dict()
            farmer_name = row.get("name", "Patil")
            farmer_region = row.get("region") or row.get("village", "Jalgaon")
            farmer_id = doc.id
    except Exception as e:
        logger.warning(f"Failed to lookup farmer by phone in IVR: {e}")
    return farmer_id, farmer_name, farmer_region

@router.post("/inbound")
async def ivr_inbound():
    """
    Entry point for Twilio incoming calls.
    Prompts the user to speak their observation.
    """
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Welcome to KisanNet voice platform, your farmer friend. Please speak your crop observation after the tone.</Say>
    <Gather input="speech" timeout="5" action="/api/v1/twilio/ivr/log" method="POST">
        <Play>http://demo.twilio.com/docs/classic.mp3</Play>
    </Gather>
    <Say>We did not hear anything. Thank you for calling KisanNet. Goodbye.</Say>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.post("/log")
async def ivr_log(
    SpeechResult: Optional[str] = Form(None),
    From: Optional[str] = Form(None)
):
    """
    Processes transcription from caller, logs to journal (Firestore),
    and executes RAG pipeline with confidence gate (BigQuery).
    """
    if not SpeechResult:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, we did not receive any observation. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # 1. Lookup caller profile
    phone = From or "phone-caller"
    farmer_id, farmer_name, farmer_region = await _lookup_farmer_info(phone)

    # 2. Run BigQuery RAG search
    relevant_docs = []
    try:
        relevant_docs = bq_client.rag_search(SpeechResult, top_k=3)
    except Exception as e:
        logger.warning(f"IVR RAG search failed: {e}")

    max_similarity = max([doc["similarity"] for doc in relevant_docs]) if relevant_docs else 0.0

    journal_id = str(uuid.uuid4())
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%B %d, %Y")

    # 3. Handle confidence gate & synthesis
    if max_similarity < SIMILARITY_THRESHOLD:
        # LOW CONFIDENCE -> Pillar 5 expert escalation
        await escalate_to_human_expert(
            farmer_id=farmer_id,
            query=SpeechResult,
            crop_type="General",
            disease_name=None,
            region=farmer_region,
            season="Kharif"
        )
        
        advice_short = await google_llm_client.generate_conversational_response(
            prompt_type="advisory_escalation",
            facts={
                "farmer_name": farmer_name,
                "region": farmer_region,
                "crop": "General",
                "issue": SpeechResult
            },
            language_code="en-US"
        )
        advice_detailed = advice_short
        crop = "General"
        disease_symptom = "Unknown"
        region = farmer_region
        season = "Kharif"
        advice_source = "KVK Expert Escalation"
        cost_benefit = "N/A"
        
        # Save low confidence journal to Firestore
        journal_data = {
            "farmer_id": farmer_id,
            "channel": "PHONE",
            "transcription": SpeechResult,
            "confidence": 0.50,
            "detected_language": "en-US",
            "crop": crop,
            "disease_symptom": disease_symptom,
            "region": region,
            "season": season,
            "advice_text": advice_short,
            "solution_text": advice_detailed,
            "advice_source": advice_source,
            "cost_benefit": cost_benefit,
            "is_fully_processed": True,
            "observation_timestamp": firestore_client.firestore.SERVER_TIMESTAMP
        }
        firestore_client.client.collection('farm_journals').document(journal_id).set(journal_data)

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="dtmf" numDigits="1" timeout="5" action="/api/v1/twilio/ivr/escalate-connect?journal_id={journal_id}" method="POST">
        <Say>{advice_short}</Say>
    </Gather>
    <Say>Thank you for calling. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # HIGH CONFIDENCE -> Normal synthesis
    adv_data = await google_llm_client.generate_fast_multilingual_advice(
        transcription=SpeechResult,
        language_code="en-US",
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

    final_region = region or farmer_region

    # 4. Spoken confirmation dynamically via Gemini using shared Persona
    confirmation_text = await google_llm_client.generate_conversational_response(
        prompt_type="logging_confirmation",
        facts={
            "farmer_name": farmer_name,
            "region": final_region,
            "crop": crop,
            "issue": disease_symptom or "crop issue",
            "time": time_str,
            "date": date_str
        },
        language_code="en-US"
    )

    # Save processed journal record to Firestore
    journal_data = {
        "farmer_id": farmer_id,
        "channel": "PHONE",
        "transcription": SpeechResult,
        "confidence": 0.95,
        "detected_language": "en-US",
        "crop": crop,
        "disease_symptom": disease_symptom,
        "region": final_region,
        "season": season,
        "advice_text": advice_short,
        "solution_text": advice_detailed,
        "advice_source": advice_source,
        "cost_benefit": cost_benefit,
        "is_fully_processed": True,
        "observation_timestamp": firestore_client.firestore.SERVER_TIMESTAMP
    }
    firestore_client.client.collection('farm_journals').document(journal_id).set(journal_data)

    # 5. Build prompt menu options
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{confirmation_text}</Say>
    <Say>Here is your advice. {advice_short}</Say>
    <Gather input="dtmf" numDigits="1" timeout="7" action="/api/v1/twilio/ivr/action-menu?journal_id={journal_id}" method="POST">
        <Say>For detailed advisory, press 1. To leave feedback on this advice, press 2. To auto-match and call a farmer who solved this before, press 3.</Say>
    </Gather>
    <Say>Thank you for using KisanNet. Goodbye.</Say>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.post("/action-menu")
async def ivr_action_menu(
    journal_id: str,
    Digits: Optional[str] = Form(None),
    From: Optional[str] = Form(None)
):
    """
    Handles menu selection from user DTMF keypress.
    """
    doc_ref = firestore_client.client.collection('farm_journals').document(journal_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Record not found. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    journal = doc.to_dict()
    dig = Digits.strip() if Digits else ""

    if dig == "1":
        # Press 1 -> Speak detailed advice
        detailed_text = journal.get("solution_text") or journal.get("advice_text") or ""
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Here is the detailed advisory: {detailed_text}</Say>
    <Gather input="dtmf" numDigits="1" timeout="7" action="/api/v1/twilio/ivr/action-menu?journal_id={journal_id}" method="POST">
        <Say>To leave feedback on this advice, press 2. To auto-match and call a farmer who solved this before, press 3. Or stay on the line to hang up.</Say>
    </Gather>
    <Say>Thank you. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    elif dig == "2":
        # Press 2 -> Record feedback (Pillar 3 webhook redirect)
        advice_source = journal.get("advice_source", "UNKNOWN")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="dtmf speech" numDigits="1" timeout="5" action="/api/v1/pillar3/twilio/feedback-webhook?JournalId={journal_id}&amp;AdviceIdentifier={advice_source}" method="POST">
        <Say>Please press 1 if this worked. Press 2 if it did not. Or speak your feedback now.</Say>
    </Gather>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    elif dig == "3":
        # Press 3 -> Pillar 4 Match and direct connect narrative
        query_str = f"{journal.get('issue_category', 'CROP_DISEASE')} {journal.get('issue_subtype', journal.get('disease_symptom', ''))} {journal.get('transcription', '')}"
        
        matches = []
        try:
            matches = bq_client.rag_search(query_str, top_k=3)
        except Exception:
            pass

        if not matches:
            # Cold start human review
            escalation_msg = "We have not seen this problem before. You are the first to report it. We are escalating this to our expert team."
            await escalate_to_human_expert(
                farmer_id=journal.get("farmer_id"),
                query=journal.get("transcription"),
                crop_type=journal.get("crop", "General"),
                disease_name=journal.get("disease_symptom"),
                region=journal.get("region", "Jalgaon"),
                season=journal.get("season", "Kharif")
            )
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{escalation_msg}</Say>
    <Hangup/>
</Response>"""
            return Response(content=twiml, media_type="application/xml")

        # Match found! Speak narrative and prompt for key 1
        # Mock finding a different farmer for this demo
        top_match = matches[0]
        name = "Another Farmer"
        village = top_match.get("region") or journal.get("region") or "your district"
        year = "2026"
        wilson_pct = 85.0
        
        spoken_narrative = await google_llm_client.generate_conversational_response(
            prompt_type="community_match",
            facts={
                "farmer_name": name,
                "village": village,
                "year": year,
                "wilson_score": f"{round(wilson_pct)}%",
                "solution": top_match.get("content") or "this solution"
            },
            language_code="en-US"
        )

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="dtmf" numDigits="1" timeout="5" action="/api/v1/twilio/ivr/match-connect?target_farmer_id=other-farmer-uuid&amp;journal_id={journal_id}" method="POST">
        <Say>{spoken_narrative}</Say>
    </Gather>
    <Say>Thank you. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # If no matches, fallback and hang up
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you for using KisanNet. Goodbye.</Say>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.post("/escalate-connect")
async def ivr_escalate_connect(
    journal_id: str,
    Digits: Optional[str] = Form(None)
):
    """
    Connects the caller directly to Krishi Vigyan Kendra expert if they pressed 1.
    """
    dig = Digits.strip() if Digits else ""
    if dig == "1":
        # Dial KVK number. Fallback to settings.TWILIO_NUMBER
        kvk_number = settings.TWILIO_NUMBER or "+1234567890"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to a Krishi Vigyan Kendra agricultural expert now. Please hold.</Say>
    <Dial>{kvk_number}</Dial>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you. Goodbye.</Say>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.post("/match-connect")
async def ivr_match_connect(
    target_farmer_id: str,
    journal_id: str,
    Digits: Optional[str] = Form(None),
    From: Optional[str] = Form(None)
):
    """
    Bridges call directly to target farmer solver if they pressed 1.
    """
    dig = Digits.strip() if Digits else ""
    if dig == "1":
        # Look up target number in Firestore
        target = firestore_client.get_farmer(target_farmer_id)
        if not target or not target.get("phone_number"):
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, the target farmer's phone number is no longer reachable. Goodbye.</Say>
    <Hangup/>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
            
        # Bridge dial
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to {target.get('name', 'them')} now. Please wait.</Say>
    <Dial timeout="20">{target['phone_number']}</Dial>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you for using KisanNet. Goodbye.</Say>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

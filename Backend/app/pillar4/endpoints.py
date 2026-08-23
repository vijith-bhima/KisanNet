import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.auth import get_current_farmer, FarmerUser
from app.twilio_service import twilio_client, send_connection_sms
from app.pillar4.schemas import MatchRequest, MatchResponse, ConnectRequest, ConnectResponse
from app.pillar4.issue_classifier import issue_classifier
from app.pillar5.escalation import escalate_to_human_expert
from app.google_llm import google_llm_client
from app.firestore_client import firestore_client
from app.bigquery_client import bq_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Pillar 4: Auto-Matching With Past Solvers"])

@router.post("/match", response_model=MatchResponse)
@router.post("/pillar4/match", response_model=MatchResponse)
async def get_matches(
    request: MatchRequest,
    farmer: FarmerUser = Depends(get_current_farmer)
):
    """
    Tiered matchmaking engine generalized across all agricultural issue categories using BigQuery.
    """
    farmer_id = str(farmer.farmer_id)
    issue_category = request.issue_category
    issue_subtype = request.issue_subtype

    if issue_subtype is None and request.disease_name is not None:
        issue_category = issue_category or "CROP_DISEASE"
        issue_subtype = request.disease_name

    if not issue_category:
        cat, sub = await issue_classifier.classify_query(request.query, request.crop_type)
        issue_category = cat
        if issue_subtype is None:
            issue_subtype = sub

    from app.pillar4.matching_engine import matching_engine
    
    match_result = await matching_engine.find_matches(
        farmer_id=farmer_id,
        query=request.query,
        issue_category=issue_category,
        issue_subtype=issue_subtype,
        region=request.region,
        season=request.season,
        crop_type=request.crop_type,
        top_k=3
    )

    matches = match_result.get("matches", [])
    
    if len(matches) == 0:
        await escalate_to_human_expert(
            farmer_id=farmer_id,
            query=request.query,
            crop_type=request.crop_type or "General",
            disease_name=issue_subtype,
            region=request.region,
            season=request.season
        )
        return {
            "status": "no_matches",
            "message": "We haven't seen this problem before. You are the first "
                       "to report it. We are escalating this to our expert team.",
        }

    top_match = matches[0]
    spoken_narrative = await google_llm_client.generate_conversational_response(
        prompt_type="community_match",
        facts={
            "farmer_name": top_match.get("farmer_name"),
            "village": top_match.get("village"),
            "year": "2026",
            "wilson_score": f"{top_match.get('wilson_lower_bound', 0):.0f}%",
            "solution": top_match.get("solution_text")
        },
        language_code="en-US"
    )

    response = {
        "status": "success",
        "matches": matches,
        "is_fallback": match_result.get("is_fallback", False),
        "spoken_narrative": spoken_narrative,
        "disclaimer": "We found these farmers who had similar problems."
    }
    return response

@router.post("/connect", response_model=ConnectResponse)
@router.post("/pillar4/connect", response_model=ConnectResponse)
async def connect_with_farmer(
    request: ConnectRequest,
    farmer: FarmerUser = Depends(get_current_farmer)
):
    """
    Connect with a past solver farmer via Firestore.
    """
    farmer_id = farmer.farmer_id
    
    source = firestore_client.get_farmer(farmer_id)
    target = firestore_client.get_farmer(request.target_farmer_id)

    if not source or not source.get("phone_number"):
        raise HTTPException(
            status_code=404,
            detail="Your farmer profile or phone number was not found in the database. "
                   "Please complete your profile registration before initiating a connection."
        )

    if not target or not target.get("phone_number"):
        raise HTTPException(status_code=404, detail="Target farmer has no reachable phone number")

    if request.channel == "MOBILE" and not request.confirmed:
        return {
            "status": "confirm_required",
            "prompt": f"Call {target.get('name', 'them')} now?",
            "target_farmer_id": request.target_farmer_id,
        }

    # Store connection in Firestore
    connection_id = str(uuid.uuid4())
    conn_data = {
        "source_farmer_id": farmer_id,
        "target_farmer_id": request.target_farmer_id,
        "journal_id": str(request.journal_id),
        "channel": request.channel,
        "connection_method": "NUMBER_SHOWN" if request.channel == "BROWSER" else "BRIDGED_CALL",
        "created_at": firestore_client.firestore.SERVER_TIMESTAMP
    }
    firestore_client.client.collection('farmer_connections').document(connection_id).set(conn_data)

    if request.channel == "BROWSER":
        await send_connection_sms(
            to=target["phone_number"],
            target_name=target.get("name", "Farmer"),
            source_name=source.get("name", "Another farmer"),
            source_phone=source["phone_number"],
        )
        return {
            "status": "connected",
            "target_name": target.get("name", "Farmer"),
            "target_phone": target["phone_number"],
            "tel_link": f"tel:{target['phone_number']}",
            "message": f"Here's {target.get('name', 'their')} number — tap to call.",
        }

    call_sid = None
    from app.twilio_service import twilio_client
    twilio_number = settings.TWILIO_NUMBER or settings.TWILIO_PHONE_NUMBER
    base_url = settings.PUBLIC_BASE_URL if hasattr(settings, 'PUBLIC_BASE_URL') else ""
    connect_status_url = f"{base_url}/voice/connect-status?connection_id={connection_id}"
    
    call_result = await twilio_client.create_call(
        to=source["phone_number"],
        from_=twilio_number,
        twiml=f"""
        <Response>
            <Say>Connecting you to {target.get('name', 'them')}.</Say>
            <Dial action="{connect_status_url}" timeout="20">{target['phone_number']}</Dial>
        </Response>
        """,
    )
    call_sid = call_result.get("sid") if call_result else None

    return {
        "status": "connected",
        "message": f"Connecting you to {target.get('name', 'them')}...",
        "call_sid": call_sid,
        "is_mock": twilio_client.is_mock,
    }

@router.post("/voice/connect-status")
@router.post("/pillar4/voice/connect-status")
async def connect_status(request: Request):
    """
    Twilio voice call status webhook callback using Firestore.
    """
    form = await request.form()
    connection_id = request.query_params.get("connection_id")
    dial_status = form.get("DialCallStatus")

    if connection_id:
        doc_ref = firestore_client.client.collection('farmer_connections').document(connection_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({"call_status": dial_status})
            conn = doc.to_dict()

            if dial_status != "completed":
                source = firestore_client.get_farmer(conn["source_farmer_id"])
                target = firestore_client.get_farmer(conn["target_farmer_id"])
                
                if target and source:
                    await send_connection_sms(
                        to=target.get("phone_number"),
                        target_name=target.get("name", "Farmer"),
                        source_name=source.get("name", "Another farmer"),
                        source_phone=source.get("phone_number"),
                    )
                    doc_ref.update({"connection_method": "SMS_FALLBACK"})
    
    return {"status": "recorded"}

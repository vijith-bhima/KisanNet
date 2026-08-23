import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.auth import get_current_expert, ExpertUser
from app.google_llm import google_llm_client
from app.google_tts import google_tts_client
from app.firestore_client import firestore_client
from app.bigquery_client import bq_client
from app.pillar5.escalation import escalate_to_human_expert
from app.pillar4.matching_engine import SIMILARITY_THRESHOLD
from app.pillar2.schemas import (
    KnowledgeBaseIngestRequest,
    KnowledgeBaseResponse,
    AdviceGenerationRequest,
    AdviceGenerationResponse,
    PushSubscriptionRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pillar2", tags=["Pillar 2: RAG-Grounded AI Advice"])

@router.post("/knowledge/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_knowledge_document(
    payload: KnowledgeBaseIngestRequest,
    expert: ExpertUser = Depends(get_current_expert)
):
    """
    Ingestion endpoint for KVK / scientific advisories into BigQuery Vector Search.
    """
    # Create combined text
    combined_text = f"{payload.title}. {payload.content}. Crop: {payload.crop or ''}. Symptom: {payload.disease_symptom or ''}."
    
    # Generate embedding
    embedding = bq_client.embed_query(combined_text)
    
    doc_id = str(uuid.uuid4())
    
    # Insert directly into BigQuery
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    sql = f"""
    INSERT INTO `{bq_client.project}.{bq_client.dataset}.knowledge_base`
    (id, chunk_text, source_document, document_type, crop_type, disease_name, treatment_name, cost_per_acre, time_to_effect_days, region, embedding)
    VALUES (
        '{doc_id}', 
        '{combined_text.replace("'", "''")}', 
        '{payload.source.replace("'", "''") if payload.source else "UNKNOWN"}',
        'EXPERT_INGEST',
        '{payload.crop or ""}',
        '{payload.disease_symptom or ""}',
        '', 
        {payload.cost_per_acre or 0}, 
        {payload.time_to_effect or 0}, 
        '{payload.region or ""}',
        {embedding_str}
    )
    """
    try:
        bq_client.client.query(sql).result()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery insert failed: {str(e)}")

    return {
        "id": doc_id,
        "title": payload.title,
        "content": payload.content,
        "crop": payload.crop,
        "disease_symptom": payload.disease_symptom,
        "region": payload.region,
        "season": payload.season,
        "source": payload.source
    }

@router.post("/generate-advice", response_model=AdviceGenerationResponse)
async def generate_advice_for_journal(
    payload: AdviceGenerationRequest
):
    """
    Triggers the RAGEngine workflow for a farm_journals record.
    """
    doc_ref = firestore_client.client.collection('farm_journals').document(str(payload.journal_id))
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Farm journal {payload.journal_id} not found")

    journal = doc.to_dict()
    query_str = f"{journal.get('crop') or ''} {journal.get('disease_symptom') or ''} {journal.get('transcription', '')}"

    try:
        relevant_docs = bq_client.rag_search(query_str, top_k=3)
    except Exception as e:
        logger.warning(f"BigQuery Vector Search failed: {e}")
        relevant_docs = []

    max_similarity = max([doc["similarity"] for doc in relevant_docs]) if relevant_docs else 0.0

    if max_similarity < SIMILARITY_THRESHOLD:
        escalation_msg = "I'm not fully sure about this. Connecting you to your local Krishi Vigyan Kendra."
        journal['advice_text'] = escalation_msg
        journal['solution_text'] = escalation_msg
        journal['advice_source'] = "Krishi Vigyan Kendra Escalation"
        journal['cost_benefit'] = "N/A"
        journal['is_fully_processed'] = True
        
        doc_ref.update(journal)

        tts_result = await google_tts_client.synthesize_speech(
            text=escalation_msg,
            language_code=journal.get('detected_language') or "en-US"
        )

        return AdviceGenerationResponse(
            journal_id=payload.journal_id,
            advice_text=escalation_msg,
            advice_short=escalation_msg,
            advice_detailed=escalation_msg,
            advice_source="Krishi Vigyan Kendra Escalation",
            cost_benefit="N/A",
            tts_prompt=escalation_msg,
            audio_base64=tts_result.get("audio_base64"),
            is_fully_processed=True
        )

    journal_data_for_llm = {
        "crop": journal.get("crop"),
        "disease_symptom": journal.get("disease_symptom"),
        "region": journal.get("region"),
        "season": journal.get("season"),
        "transcription": journal.get("transcription")
    }
    
    advice_res = await google_llm_client.generate_rag_advice(journal_data_for_llm, relevant_docs)

    advice_short = advice_res.get("advice_short") or advice_res.get("answer_text", "")
    advice_detailed = advice_res.get("advice_detailed") or advice_res.get("answer_text", "")
    advice_source = advice_res.get("source", "ICAR-KVK")

    journal['advice_text'] = advice_short
    journal['solution_text'] = advice_detailed
    journal['advice_source'] = advice_source
    journal['cost_benefit'] = advice_res.get("cost_benefit", "")
    journal['is_fully_processed'] = True
    
    doc_ref.update(journal)

    tts_result = await google_tts_client.synthesize_speech(
        text=advice_short,
        language_code=journal.get('detected_language') or "en-US"
    )

    return AdviceGenerationResponse(
        journal_id=payload.journal_id,
        advice_text=advice_short,
        advice_short=advice_short,
        advice_detailed=advice_detailed,
        advice_source=advice_source,
        cost_benefit=str(journal.get('cost_benefit', '')),
        tts_prompt=advice_short,
        audio_base64=tts_result.get("audio_base64"),
        is_fully_processed=True
    )

@router.post("/subscribe", status_code=status.HTTP_200_OK)
async def create_push_subscription(
    payload: PushSubscriptionRequest
):
    return {
        "status": "subscribed",
        "webhook_url": payload.webhook_url,
        "message": "Push subscription registered successfully"
    }

import uuid
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EscalationQueue:
    """
    Pillar 5: Human Expert Review & Triage Escalation Queue.
    Handles cold-start unmapped farm problems by queuing them for KVK agronomists.
    """
    def __init__(self):
        self.escalated_tickets = []

    async def escalate_unresolved_query(
        self,
        farmer_id: str,
        query: str,
        crop_type: str,
        disease_name: Optional[str],
        region: str,
        season: str
    ) -> Dict[str, Any]:
        ticket = {
            "ticket_id": str(uuid.uuid4()),
            "farmer_id": farmer_id,
            "query": query,
            "crop_type": crop_type,
            "disease_name": disease_name,
            "region": region,
            "season": season,
            "status": "QUEUED_FOR_EXPERT_REVIEW",
            "priority": "HIGH"
        }
        self.escalated_tickets.append(ticket)
        logger.info(f"[Pillar 5 Escalation] Cold-start problem escalated for farmer {farmer_id}: {crop_type} / {disease_name}")
        return ticket


escalation_queue = EscalationQueue()

async def escalate_to_human_expert(
    farmer_id: str,
    query: str,
    crop_type: str,
    disease_name: Optional[str],
    region: str,
    season: str
) -> Dict[str, Any]:
    """Helper function to escalate a cold-start match failure to human expert team."""
    return await escalation_queue.escalate_unresolved_query(
        farmer_id=farmer_id,
        query=query,
        crop_type=crop_type,
        disease_name=disease_name,
        region=region,
        season=season
    )

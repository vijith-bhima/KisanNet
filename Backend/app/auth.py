import os
import uuid
from typing import Optional
from fastapi import Header, HTTPException, status
from app.config import settings

ENVIRONMENT = settings.ENVIRONMENT.lower()

class FarmerUser:
    def __init__(self, farmer_id: str, name: str = ""):
        self.farmer_id = farmer_id
        self.name = name

class ExpertUser:
    def __init__(self, expert_id: str, name: str = ""):
        self.expert_id = expert_id
        self.name = name

def _get_valid_uuid_string(input_str: Optional[str]) -> Optional[str]:
    """Converts input string into a valid UUID hex string, or returns None if invalid."""
    if not input_str:
        return None
    try:
        val = uuid.UUID(input_str)
        return str(val)
    except (ValueError, AttributeError):
        # Deterministic UUID generation for arbitrary string IDs (e.g. Firebase UID)
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(input_str)))

async def get_current_farmer(
    x_farmer_id: Optional[str] = Header(None, alias="X-Farmer-ID"),
    authorization: Optional[str] = Header(None)
) -> FarmerUser:
    """
    Auth dependency. Resolves farmer identity from X-Farmer-ID header.

    - Production: rejects requests with no valid identity.
    - Development (ENVIRONMENT=development): falls back to a known dev UUID so
      curl/Swagger testing works without a real auth token. This fallback is
      explicitly logged every time it is used so it is never silent.
    """
    farmer_id = _get_valid_uuid_string(x_farmer_id)

    if farmer_id is None:
        if ENVIRONMENT == "development":
            DEV_FARMER_UUID = "11111111-1111-1111-1111-111111111111"
            import logging
            logging.getLogger(__name__).warning(
                "⚠️  DEV FALLBACK IDENTITY IN USE — farmer_id set to %s. "
                "This ONLY works because ENVIRONMENT=development. "
                "Set X-Farmer-ID header in production requests.",
                DEV_FARMER_UUID,
            )
            return FarmerUser(farmer_id=DEV_FARMER_UUID)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Farmer-ID header is required. Provide a valid farmer UUID or Firebase UID.",
        )

    return FarmerUser(farmer_id=farmer_id)


async def get_current_expert(
    x_expert_id: Optional[str] = Header(None, alias="X-Expert-ID")
) -> ExpertUser:
    """
    Auth dependency for KVK Agriculture Experts.
    Rejects unauthenticated expert requests in production.
    """
    expert_id = _get_valid_uuid_string(x_expert_id)

    if expert_id is None:
        if ENVIRONMENT == "development":
            DEV_EXPERT_UUID = "22222222-2222-2222-2222-222222222222"
            import logging
            logging.getLogger(__name__).warning(
                "⚠️  DEV FALLBACK EXPERT IDENTITY IN USE — expert_id set to %s. "
                "ENVIRONMENT=development only.",
                DEV_EXPERT_UUID,
            )
            return ExpertUser(expert_id=DEV_EXPERT_UUID)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Expert-ID header is required.",
        )

    return ExpertUser(expert_id=expert_id)

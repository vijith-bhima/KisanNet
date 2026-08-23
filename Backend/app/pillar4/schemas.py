from typing import List, Optional, Any
from pydantic import BaseModel, Field

class MatchRequest(BaseModel):
    query: str
    issue_category: Optional[str] = None
    issue_subtype: Optional[str] = None
    crop_type: Optional[str] = None
    disease_name: Optional[str] = None  # Deprecated alias for backward compatibility
    region: str
    season: str

class MatchResultItem(BaseModel):
    farmer_id: Any
    farmer_name: str
    village: Optional[str] = None
    solution_text: Optional[str] = None
    wilson_lower_bound: float
    bayesian_score: Optional[float] = None
    vote_count: Optional[int] = None
    similarity: Optional[float] = None
    observation_timestamp: Optional[Any] = None

class MatchResponse(BaseModel):
    status: str
    message: Optional[str] = None
    matches: Optional[List[dict]] = None
    is_fallback: Optional[bool] = False
    disclaimer: Optional[str] = None
    spoken_narrative: Optional[str] = None

class ConnectRequest(BaseModel):
    target_farmer_id: str
    journal_id: str
    channel: str # 'BROWSER' or 'MOBILE'
    confirmed: bool = False # MOBILE only

class ConnectResponse(BaseModel):
    status: str
    target_name: Optional[str] = None
    target_phone: Optional[str] = None
    tel_link: Optional[str] = None
    message: Optional[str] = None
    prompt: Optional[str] = None
    target_farmer_id: Optional[str] = None
    call_sid: Optional[str] = None
    is_mock: Optional[bool] = False

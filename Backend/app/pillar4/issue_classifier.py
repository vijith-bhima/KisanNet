import re
import json
import logging
from typing import Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)

VALID_ISSUE_CATEGORIES = [
    "CROP_DISEASE",
    "PEST",
    "IRRIGATION",
    "SOIL",
    "MARKET_PRICE",
    "EQUIPMENT",
    "WEATHER",
    "GOVT_SCHEME",
    "LIVESTOCK",
    "POST_HARVEST",
    "OTHER"
]

class IssueClassificationSchema(BaseModel):
    issue_category: str = Field(
        description="One of: CROP_DISEASE, PEST, IRRIGATION, SOIL, MARKET_PRICE, EQUIPMENT, WEATHER, GOVT_SCHEME, LIVESTOCK, POST_HARVEST, OTHER"
    )
    issue_subtype: str = Field(
        description="Specific problem subtype identifier e.g. DRIP_SYSTEM_CLOG, YELLOWING_LEAVES, LOW_MANDI_PRICE, TRACTOR_ENGINE_FAIL"
    )

KEYWORD_CATEGORY_RULES = [
    ("IRRIGATION", [r"\bdrip\b", r"\birrigation\b", r"\bpipe\b", r"\bclog\b", r"\bwater logging\b", r"\bwater pump\b", r"\bsprinkler\b"]),
    ("EQUIPMENT", [r"\btractor\b", r"\bmachine\b", r"\bharvest(er|ing)\b", r"\bpump motor\b", r"\brotavator\b", r"\bsprayer\b"]),
    ("MARKET_PRICE", [r"\bprice\b", r"\bmandi\b", r"\brate\b", r"\bcost\b", r"\bsell\b", r"\bmarket\b", r"\btrader\b"]),
    ("GOVT_SCHEME", [r"\bscheme\b", r"\bsubsidy\b", r"\bklcc\b", r"\bpm-kisan\b", r"\binsurance\b", r"\bcompensation\b", r"\bloan\b"]),
    ("SOIL", [r"\bsoil\b", r"\bfertilizer\b", r"\burea\b", r"\bdap\b", r"\bnpk\b", r"\bph\b", r"\bsalinity\b", r"\bnutrient\b"]),
    ("PEST", [r"\bpest\b", r"\bborer\b", r"\bcaterpillar\b", r"\baphid\b", r"\bwhitefly\b", r"\blocust\b", r"\bbollworm\b", r"\binsect\b"]),
    ("WEATHER", [r"\bweather\b", r"\brain\b", r"\bdrought\b", r"\bfrost\b", r"\bhailstorm\b", r"\bheatwave\b", r"\bmonsoon\b"]),
    ("LIVESTOCK", [r"\bcow\b", r"\bbuffalo\b", r"\bcattle\b", r"\bgoat\b", r"\bpoultry\b", r"\bfodder\b", r"\bmilk yield\b", r"\banimal\b"]),
    ("POST_HARVEST", [r"\bstorage\b", r"\bgodown\b", r"\bmoisture\b", r"\bgrain rot\b", r"\bsilo\b", r"\bspoilage\b"]),
    ("CROP_DISEASE", [r"\bdisease\b", r"\byellow(ing)?\b", r"\bleaf curl\b", r"\brust\b", r"\bblight\b", r"\bfungus\b", r"\brot\b", r"\bwilt\b", r"\bspot\b"]),
]

class IssueClassifier:
    """
    Generalized agricultural issue taxonomy classifier.
    Maps free-text query into issue_category and issue_subtype.
    """
    def __init__(self, api_key: str = settings.GOOGLE_API_KEY, model_name: str = settings.GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name

    async def classify_query(self, query: str, crop_type: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Classifies free-text query into (issue_category, issue_subtype).
        Uses Google Gemini 2.0 Flash structured schema, falling back to deterministic regex heuristics.
        """
        if not query or not query.strip():
            return ("OTHER", None)

        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                prompt = (
                    "Classify the following farmer query into an issue category and specific issue subtype.\n"
                    f"Categories: {', '.join(VALID_ISSUE_CATEGORIES)}\n"
                    f"Crop: {crop_type or 'General / None'}\n"
                    f"Query: \"{query}\""
                )
                res = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=IssueClassificationSchema
                    )
                )
                parsed = json.loads(res.text.strip())
                cat = parsed.get("issue_category", "OTHER").upper()
                sub = parsed.get("issue_subtype")
                if cat in VALID_ISSUE_CATEGORIES:
                    return (cat, sub)
        except Exception as e:
            logger.debug(f"Gemini issue classifier fallback: {e}")

        # Fast keyword heuristic fallback
        q_lower = query.lower()
        for cat, patterns in KEYWORD_CATEGORY_RULES:
            for pat in patterns:
                match = re.search(pat, q_lower)
                if match:
                    # Clean matched keyword for subtype
                    sub_token = match.group(0).upper().replace(" ", "_")
                    return (cat, sub_token)

        return ("CROP_DISEASE", query.strip().upper().replace(" ", "_"))


issue_classifier = IssueClassifier()

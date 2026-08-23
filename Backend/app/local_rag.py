import json
import os
import re
import logging

logger = logging.getLogger(__name__)

# Resolve path to "my data" folder dynamically relative to the backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MY_DATA_DIR = os.path.join(BASE_DIR, "my data")

class LocalRAG:
    def __init__(self):
        self.kb_data = []
        self.schemes_data = []
        self._load_data()

    def _load_data(self):
        kb_path = os.path.join(MY_DATA_DIR, "knowledge_base.json")
        schemes_path = os.path.join(MY_DATA_DIR, "schemes.json")
        
        try:
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    self.kb_data = json.load(f)
                    logger.info(f"Loaded {len(self.kb_data)} knowledge base records from local JSON.")
            else:
                logger.warning(f"Could not find {kb_path}")
                
            if os.path.exists(schemes_path):
                with open(schemes_path, "r", encoding="utf-8") as f:
                    self.schemes_data = json.load(f)
                    logger.info(f"Loaded {len(self.schemes_data)} scheme records from local JSON.")
            else:
                logger.warning(f"Could not find {schemes_path}")
        except Exception as e:
            logger.error(f"Error loading local data: {e}")

    def _score_text(self, query: str, text: str) -> int:
        if not text:
            return 0
        # Simple keyword overlap scoring based on word tokens
        query_words = set(re.findall(r'\w+', query.lower()))
        text_words = set(re.findall(r'\w+', text.lower()))
        
        # Boost matches for words longer than 3 chars to ignore stop words slightly
        query_keywords = {w for w in query_words if len(w) > 3}
        return len(query_keywords.intersection(text_words))

    def search(self, query: str, top_k: int = 3):
        results = []
        
        # Search Knowledge Base (Crops/Diseases)
        for item in self.kb_data:
            text_to_search = f"{item.get('crop', '')} {item.get('disease', '')} {item.get('symptoms', '')}"
            score = self._score_text(query, text_to_search)
            if score > 0:
                results.append({
                    "type": "disease_treatment",
                    "score": score,
                    "crop": item.get("crop"),
                    "disease": item.get("disease"),
                    "symptoms": item.get("symptoms"),
                    "treatment_a": item.get("treatment_option_a", {}),
                    "treatment_b": item.get("treatment_option_b", {})
                })
                
        # Search Schemes
        for item in self.schemes_data:
            text_to_search = f"{item.get('name', '')} {item.get('description', '')}"
            score = self._score_text(query, text_to_search)
            if score > 0:
                results.append({
                    "type": "government_scheme",
                    "score": score,
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "eligibility": item.get("eligibility")
                })
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Remove score from output to avoid confusing LLM
        final_results = results[:top_k]
        for r in final_results:
            r.pop("score", None)
            
        return final_results

# Instantiate globally to cache the loaded JSON in memory
local_rag = LocalRAG()

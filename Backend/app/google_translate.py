import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleTranslateClient:
    """
    Google Cloud Translation API Client for BRICS cross-border support.
    Translates farmer free-text and advisories across BRICS languages (hi, pt, ru, zh, ar, en).
    """
    async def translate_text(
        self,
        text: str,
        target_language: str = "en",
        source_language: str = None
    ) -> Dict[str, Any]:
        try:
            from google.cloud import translate_v2 as translate
            client = translate.Client()
            result = client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )
            return {
                "translated_text": result.get("translatedText", text),
                "detected_source_language": result.get("detectedSourceLanguage", source_language or "en"),
                "target_language": target_language
            }
        except Exception as e:
            logger.warning(f"Google Cloud Translate API call fallback: {e}")
            return {
                "translated_text": text,
                "detected_source_language": source_language or "en",
                "target_language": target_language
            }

google_translate_client = GoogleTranslateClient()

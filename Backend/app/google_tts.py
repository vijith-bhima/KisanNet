import base64
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Regional High-Fidelity Voice Mapping
HIGH_FIDELITY_VOICES = {
    "hi-IN": "hi-IN-Neural2-F",
    "pa-IN": "pa-IN-Wavenet-A",
    "mr-IN": "mr-IN-Wavenet-A",
    "te-IN": "te-IN-Standard-A",
    "ta-IN": "ta-IN-Wavenet-A",
    "kn-IN": "kn-IN-Wavenet-A",
    "bn-IN": "bn-IN-Wavenet-A",
    "gu-IN": "gu-IN-Standard-A",
    "en-IN": "en-IN-Wavenet-C",
    "en-US": "en-US-Neural2-F"
}

class GoogleTTSClient:
    """
    Google Cloud Text-to-Speech Client for synthesizing advisory audio for farmers.
    Matches the farmer's default_language and returns Base64 encoded MP3 audio bytes.
    """
    async def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-US",
        speaking_rate: float = 1.0
    ) -> Dict[str, Any]:
        """
        Synthesizes text prompt into audio bytes (Base64 encoded MP3).
        Supports SSML if prompt starts with <speak>.
        """
        try:
            from google.cloud import texttospeech
            client = texttospeech.TextToSpeechClient()

            # Automatic SSML vs Plaintext detection
            if text.strip().startswith("<speak>"):
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_name = HIGH_FIDELITY_VOICES.get(language_code)
            if voice_name:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name
                )
            else:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            audio_base64 = base64.b64encode(response.audio_content).decode("utf-8")
            
            return {
                "audio_base64": audio_base64,
                "mime_type": "audio/mp3",
                "text": text,
                "language_code": language_code
            }
        except Exception as e:
            # When Cloud TTS is unconfigured, return None so browser native SpeechSynthesis speaks with zero latency
            return {
                "audio_base64": None,
                "mime_type": "audio/mp3",
                "text": text,
                "language_code": language_code
            }

google_tts_client = GoogleTTSClient()


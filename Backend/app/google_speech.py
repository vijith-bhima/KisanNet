import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleSpeechClient:
    """
    Google Cloud Speech-to-Text Integration Client.
    Uses google-cloud-speech batch recognition with native confidence scores in [0, 1].

    NOTE: This is the batch `recognize()` code path (not streaming).
    True streaming STT requires `streaming_recognize()` which is a different code path
    — see the docstring on `transcribe_audio_streaming()` below for details.
    If the Cloud STT credentials are absent (GOOGLE_APPLICATION_CREDENTIALS not set),
    this returns an explicit error dict with transcription=None rather than fabricating
    a fake transcription, so callers can handle the missing credential correctly.
    """
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language_code: str = "en-US",
        sample_rate_hertz: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribes audio bytes using Google Cloud Speech-to-Text batch API.
        Returns native confidence score in [0.0, 1.0].
        Returns transcription=None on credential/API failure — callers must handle this.
        """
        try:
            from google.cloud import speech
            client = speech.SpeechClient()
            audio = speech.RecognitionAudio(content=audio_bytes)
            
            config_kwargs = {
                "language_code": language_code,
                "enable_automatic_punctuation": True
            }
            if sample_rate_hertz:
                config_kwargs["sample_rate_hertz"] = sample_rate_hertz
                config_kwargs["encoding"] = speech.RecognitionConfig.AudioEncoding.LINEAR16
            else:
                config_kwargs["encoding"] = speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED

            config = speech.RecognitionConfig(**config_kwargs)
            response = client.recognize(config=config, audio=audio)
            
            transcript_parts = []
            confidences = []
            
            for result in response.results:
                if result.alternatives:
                    alt = result.alternatives[0]
                    transcript_parts.append(alt.transcript)
                    confidences.append(alt.confidence)

            final_transcript = " ".join(transcript_parts).strip()
            avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.80

            return {
                "transcription": final_transcript or None,
                "confidence": min(max(avg_confidence, 0.0), 1.0),
                "detected_language": language_code,
                "error": None
            }
        except Exception as e:
            logger.warning(
                "Google Cloud Speech-to-Text unavailable (GOOGLE_APPLICATION_CREDENTIALS likely not set): %s", e
            )
            return {
                "transcription": None,
                "confidence": 0.0,
                "detected_language": language_code,
                "error": str(e)
            }

    # -----------------------------------------------------------------------
    # NOTE: Streaming STT is NOT currently wired in.
    # -----------------------------------------------------------------------
    # To enable true streaming recognition (low-latency barge-in style),
    # you would use `speech_client.streaming_recognize()` with a generator
    # of `StreamingRecognizeRequest` objects. This is a fundamentally different
    # API than the batch `recognize()` call above — it requires a bidirectional
    # gRPC stream and cannot be called from a standard HTTP/REST handler without
    # a WebSocket or gRPC transport layer on the FastAPI side.
    #
    # The browser currently handles real-time STT via the Web Speech API
    # (SpeechRecognition), which is the correct low-latency path for the browser
    # UI. Google Cloud Streaming STT would be needed for Twilio IVR calls or
    # native mobile apps. Flag this as a required follow-up for those channels.
    # -----------------------------------------------------------------------

google_speech_client = GoogleSpeechClient()

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class VoiceIntentClassifier:
    """
    Language-Specific Intent Classifier for Farmer Feedback
    Supports: Hindi, Marathi, Tamil, Telugu, English
    """

    LANGUAGE_WORDS = {
        "hi": {  # Hindi
            "positive": ["haan", "theek", "sahi", "acha", "kaam kiya", "ho gaya"],
            "negative": ["nahi", "galat", "theek nahi", "sahi nahi", "na kaam", "fail"],
            "negation_particles": ["nahi", "na"]
        },
        "mr": {  # Marathi
            "positive": ["ho", "theek", "barobar", "kaam zala"],
            "negative": ["nahi", "chuk", "theek nahi", "kaam nahi zala"],
            "negation_particles": ["nahi", "na"]
        },
        "ta": {  # Tamil
            "positive": ["aam", "sari", "nalla", "seri"],
            "negative": ["illai", "tappu", "seri illai", "sari illai"],
            "negation_particles": ["illai", "ila"]
        },
        "te": {  # Telugu
            "positive": ["avunu", "sare", "baagundi"],
            "negative": ["ledu", "tappu", "sare ledu", "avunu ledu"],
            "negation_particles": ["ledu", "le"]
        },
        "en": {  # English
            "positive": ["yes", "yeah", "worked", "correct", "good"],
            "negative": ["no", "nope", "wrong", "incorrect", "didn't work"],
            "negation_particles": ["not", "n't"]
        }
    }

    def classify_intent(self, transcript: str, language: str = "hi") -> Tuple[int, float]:
        """
        Classify farmer's voice feedback into intent.
        Returns: (feedback_int, confidence)
        feedback: 1 = Worked, 2 = Didn't work, 0 = Unclear
        """
        if language not in self.LANGUAGE_WORDS:
            language = "en"

        normalized = transcript.lower().strip()
        lang_words = self.LANGUAGE_WORDS.get(language, self.LANGUAGE_WORDS["en"])

        # STEP 1: Check NEGATIVE phrases FIRST (prevents "theek nahi" -> "yes")
        negative_patterns = lang_words.get("negative", [])
        for pattern in negative_patterns:
            if re.search(r'\b' + re.escape(pattern) + r'\b', normalized, re.IGNORECASE):
                # Check if negation particle is adjacent
                for particle in lang_words.get("negation_particles", []):
                    if particle in normalized:
                        return (2, 0.95)
                return (2, 0.90)

        # STEP 2: Check POSITIVE phrases
        positive_patterns = lang_words.get("positive", [])
        for pattern in positive_patterns:
            if re.search(r'\b' + re.escape(pattern) + r'\b', normalized, re.IGNORECASE):
                # Double-check: if negation particle exists but wasn't caught
                for particle in lang_words.get("negation_particles", []):
                    if particle in normalized:
                        return (2, 0.85)  # Override: negative wins
                return (1, 0.95)

        # STEP 3: Check for ambiguous responses
        ambiguous = ["hmm", "maybe", "pata nahi", "malum nahi", "unknown", "not sure"]
        for pattern in ambiguous:
            if re.search(r'\b' + re.escape(pattern) + r'\b', normalized, re.IGNORECASE):
                return (0, 0.40)

        # STEP 4: Completely unclear
        return (0, 0.10)

voice_intent_classifier = VoiceIntentClassifier()

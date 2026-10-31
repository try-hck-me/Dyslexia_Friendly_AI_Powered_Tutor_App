"""
Sentiment analysis service.
Classifies user messages into mood categories using a transformer model.
GoEmotions (Demszky et al., 2020) implemented via j-hartmann/emotion-english-distilroberta-base.
"""

import logging
import json
from app.services.llm_groq import generate
from app.utils.prompts import EMOTION_ACTION_MAPPING_PROMPT

logger = logging.getLogger(__name__)

# Lazy-loaded singletons — initialized on first call to detect_mood()
_spell = None
_emotion_classifier = None


def _get_spell():
    """Return the SpellChecker, initializing it on first use."""
    global _spell
    if _spell is None:
        from spellchecker import SpellChecker
        _spell = SpellChecker()
    return _spell


def _get_classifier():
    """Return the emotion pipeline, downloading/loading the model on first use."""
    global _emotion_classifier
    if _emotion_classifier is None:
        try:
            from transformers import pipeline
            logger.info("Loading GoEmotions sentiment model... (this may take a moment)")
            _emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,  # equivalent to return_all_scores=True
            )
            logger.info("GoEmotions model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            _emotion_classifier = False  # sentinel: tried but failed
    return _emotion_classifier if _emotion_classifier else None


def _spell_correct(message: str) -> str:
    """
    Normalize spelling before passing to the model.
    spell.correction() may return None for unknown words — we keep
    the original word in that case so join() never receives None.
    """
    try:
        spell = _get_spell()
        words = message.split()
        corrected_words = [
            (spell.correction(w) or w)   # None-safe fallback
            for w in words
        ]
        return " ".join(corrected_words).lower()
    except Exception:
        # Spell checker unavailable — use raw message
        return message.lower()


def detect_mood(message: str) -> dict:
    """
    Detect the mood of a user message using GoEmotions and map to tutor actions.

    Args:
        message: The user's message text.

    Returns:
        JSON structure with 'detected_emotion', 'confidence', 'tutor_action', etc.
    """
    emotion_classifier = _get_classifier()

    if not emotion_classifier:
        logger.warning("Emotion classifier not available. Falling back.")
        return {
            "detected_emotion": "neutral",
            "confidence": 1.0,
            "tutor_action": "general_support",
            "simplify_content": False,
            "flag_for_review": False,
        }

    # Step 1: Normalize spelling
    normalized = _spell_correct(message)

    # Step 2: Run emotion model
    try:
        scores = emotion_classifier(normalized)[0]
        top = max(scores, key=lambda x: x["score"])
        emotion = top["label"]
        confidence = round(top["score"], 2)
    except Exception as e:
        logger.error(f"Emotion classification failed: {e}")
        return {
            "detected_emotion": "neutral",
            "confidence": 1.0,
            "tutor_action": "general_support",
            "simplify_content": False,
            "flag_for_review": False,
        }

    # Step 3: Map to tutor actions using LLM
    prompt = EMOTION_ACTION_MAPPING_PROMPT.format(
        emotion=emotion,
        confidence=confidence,
        message=message,
    )

    try:
        result = generate(
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=150,
        )

        # Strip markdown code fences if present
        result_str = result.strip()
        if result_str.startswith("```json"):
            result_str = result_str[7:]
        if result_str.startswith("```"):
            result_str = result_str[3:]
        if result_str.endswith("```"):
            result_str = result_str[:-3]

        return json.loads(result_str.strip())

    except Exception as e:
        logger.warning(f"LLM emotion mapping failed: {e}. Returning raw emotion.")
        return {
            "detected_emotion": emotion,
            "confidence": confidence,
            "tutor_action": "needs_encouragement" if emotion in ("sadness", "fear") else "general_support",
            "simplify_content": emotion in ("anger", "disgust"),
            "flag_for_review": False,
        }

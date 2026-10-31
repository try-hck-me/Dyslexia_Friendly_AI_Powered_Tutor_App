"""
Groq LLM service.
Wraps the Groq Python client for chat completions with:
  - Singleton client initialization
  - Exponential-backoff retry on rate-limit (429) and transient (503) errors
  - Clear error messages for missing API key
"""

import os
import time
import logging
from groq import Groq, RateLimitError, APIStatusError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Singleton Groq client
_client: Groq | None = None

# Retry config
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0   # seconds — doubles each attempt


def get_client() -> Groq:
    """Get or initialize the Groq client (singleton)."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file: GROQ_API_KEY=gsk_..."
            )
        _client = Groq(api_key=api_key)
        logger.info("Groq client initialized.")
    return _client


def generate(
    user_prompt: str,
    system_prompt: str = "",
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Generate a response from the Groq LLM.

    Retries up to _MAX_RETRIES times on:
      - RateLimitError (HTTP 429)
      - APIStatusError with status 503 (service unavailable)

    Args:
        user_prompt:   The user message / question.
        system_prompt: Optional system-level instructions.
        model:         Groq model ID to use.
        temperature:   Sampling temperature (0.0 – 1.0).
        max_tokens:    Maximum tokens in the response.

    Returns:
        The generated text, stripped of leading/trailing whitespace.

    Raises:
        RuntimeError if all retries are exhausted.
    """
    client = get_client()

    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    last_error: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            last_error = e
            delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"Groq rate-limit (429) on attempt {attempt}/{_MAX_RETRIES}. "
                f"Retrying in {delay:.1f}s…"
            )
            time.sleep(delay)

        except APIStatusError as e:
            # Retry only on transient server errors (5xx)
            if e.status_code >= 500:
                last_error = e
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    f"Groq server error ({e.status_code}) on attempt "
                    f"{attempt}/{_MAX_RETRIES}. Retrying in {delay:.1f}s…"
                )
                time.sleep(delay)
            else:
                # 4xx errors (except 429) are not retryable
                logger.error(f"Groq API client error: {e}")
                raise RuntimeError(f"LLM request failed ({e.status_code}): {e}") from e

        except Exception as e:
            logger.error(f"Groq unexpected error: {e}")
            raise RuntimeError(f"LLM generation failed: {e}") from e

    logger.error(f"Groq: all {_MAX_RETRIES} retries exhausted. Last error: {last_error}")
    raise RuntimeError(
        f"LLM generation failed after {_MAX_RETRIES} retries. "
        "The AI service may be temporarily overloaded — please try again in a moment."
    )

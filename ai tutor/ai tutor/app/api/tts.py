"""
Text-to-Speech API Endpoint using Sarvam AI.
The Sarvam API key is read from the SARVAM_API_KEY environment variable.
"""

import os
import logging
import urllib.request
import urllib.error
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.utils.formatter import build_response
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter()

SARVAM_URL = "https://api.sarvam.ai/text-to-speech"

def _get_sarvam_key() -> str:
    """Read the Sarvam API key from environment. Raises clearly if missing."""
    key = os.getenv("SARVAM_API_KEY", "")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="TTS service is not configured (SARVAM_API_KEY missing in .env).",
        )
    return key

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", max_length=2500)
    speaker: str = Field("shubh", description="Voice for the text-to-speech engine")

@router.post("/tts")
async def generate_speech(request: TTSRequest):
    """
    Synthesize speech using Sarvam AI's text-to-speech API.
    Aimed at dyslexia-friendly playback (slightly slower pace).
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    try:
        api_key = _get_sarvam_key()
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": request.text,
            "target_language_code": "en-IN",
            "speaker": request.speaker,
            "pace": 0.9,
            "model": "bulbul:v3",
        }
        
        json_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(SARVAM_URL, data=json_data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=25) as response:
            resp_body = response.read().decode("utf-8")
            data = json.loads(resp_body)
            
            audio_b64 = data.get("audios", [])[0] if data.get("audios") else None
            
            if not audio_b64:
                raise HTTPException(status_code=500, detail="No audio returned from TTS service")
                
            return build_response(success=True, data={"audio": audio_b64})
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.error(f"Sarvam API error {e.code}: {error_body}")
        raise HTTPException(status_code=e.code, detail=f"Sarvam API Error: {error_body}")
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

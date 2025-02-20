from typing import Dict
from fastapi import APIRouter, Depends, UploadFile, File
from app.services.voice_api import VoiceAPIService
from app.core.deps import get_current_user
from app.models.auth import UserInDB
from fastapi.responses import StreamingResponse
import io

router = APIRouter()

@router.post("/command")
async def process_voice_command(
    audio: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Process voice command and convert to API request."""
    voice_service = VoiceAPIService()
    return await voice_service.process_voice_command(audio)

@router.post("/response")
async def generate_voice_response(
    text: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate voice response from text."""
    voice_service = VoiceAPIService()
    audio_data = await voice_service.generate_voice_response(text)
    
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav"
    )

@router.post("/natural-language")
async def process_natural_language_query(
    query: str,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Process natural language API query."""
    voice_service = VoiceAPIService()
    return await voice_service.process_natural_language_query(query)

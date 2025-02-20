from typing import Dict, Any, Optional, List
import speech_recognition as sr
from app.core.logger import logger
from app.models.voice import VoiceCommand, VoiceResponse
from app.core.ai.nlp_processor import NLPProcessor

class VoiceAPIController:
    def __init__(self, nlp_processor: NLPProcessor):
        self.recognizer = sr.Recognizer()
        self.nlp = nlp_processor
        self.command_history: List[VoiceCommand] = []
        
    async def process_voice_command(self, audio_data: bytes) -> VoiceResponse:
        try:
            # Convert audio to text
            text = await self._convert_audio_to_text(audio_data)
            
            # Parse command using NLP
            command = await self.nlp.parse_api_command(text)
            
            # Execute API command
            response = await self._execute_command(command)
            
            # Log command
            self.command_history.append(command)
            
            return response
        except Exception as e:
            logger.error(f"Voice command processing failed: {str(e)}")
            raise
            
    async def get_command_suggestions(self, partial_audio: bytes) -> List[str]:
        try:
            # Convert partial audio to text
            partial_text = await self._convert_audio_to_text(partial_audio)
            
            # Get command suggestions
            suggestions = await self.nlp.get_command_suggestions(partial_text)
            
            return suggestions
        except Exception as e:
            logger.error(f"Failed to get command suggestions: {str(e)}")
            return [] 
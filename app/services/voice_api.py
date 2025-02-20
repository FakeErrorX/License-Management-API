from typing import Dict, Optional, BinaryIO
from fastapi import HTTPException, UploadFile
import speech_recognition as sr
import pyttsx3
import json
import tempfile
import os
from datetime import datetime
from transformers import pipeline
from app.core.config import settings

class VoiceAPIService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.text_to_speech = pyttsx3.init()
        self.nlp_pipeline = pipeline("text-classification")
        
    async def process_voice_command(self, audio_file: UploadFile) -> Dict:
        """Process voice command and convert to API request."""
        try:
            # Save uploaded audio temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp_audio:
                temp_audio.write(await audio_file.read())
                temp_path = temp_audio.name

            # Convert speech to text
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)

            # Parse command
            command = await self._parse_voice_command(text)

            # Clean up temp file
            os.unlink(temp_path)

            return {
                "text": text,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Voice command processing failed: {str(e)}"
            )

    async def generate_voice_response(self, text: str) -> BinaryIO:
        """Generate voice response from text."""
        try:
            # Convert text to speech
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                self.text_to_speech.save_to_file(text, temp_audio.name)
                self.text_to_speech.runAndWait()
                
                with open(temp_audio.name, "rb") as audio_file:
                    audio_data = audio_file.read()

            # Clean up temp file
            os.unlink(temp_audio.name)

            return audio_data
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Voice response generation failed: {str(e)}"
            )

    async def process_natural_language_query(self, query: str) -> Dict:
        """Process natural language API query."""
        try:
            # Analyze query intent
            intent = await self._analyze_query_intent(query)

            # Extract parameters
            params = await self._extract_query_parameters(query)

            # Generate API request
            api_request = await self._generate_api_request(intent, params)

            return {
                "query": query,
                "intent": intent,
                "parameters": params,
                "api_request": api_request,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Natural language query processing failed: {str(e)}"
            )

    async def _parse_voice_command(self, text: str) -> Dict:
        """Parse voice command into structured format."""
        # Analyze command intent
        intent = self.nlp_pipeline(text)[0]
        
        # Extract key information
        command = {
            "action": intent["label"],
            "confidence": intent["score"],
            "parameters": await self._extract_command_parameters(text)
        }
        
        return command

    async def _analyze_query_intent(self, query: str) -> Dict:
        """Analyze the intent of a natural language query."""
        # Use NLP pipeline to classify intent
        result = self.nlp_pipeline(query)[0]
        
        return {
            "type": result["label"],
            "confidence": result["score"]
        }

    async def _extract_query_parameters(self, query: str) -> Dict:
        """Extract parameters from natural language query."""
        # Extract key parameters using NLP
        # This is a simplified implementation
        params = {}
        
        # Extract dates
        if "today" in query.lower():
            params["date"] = datetime.now().date().isoformat()
        
        # Extract numbers
        import re
        numbers = re.findall(r'\d+', query)
        if numbers:
            params["number"] = numbers[0]
            
        return params

    async def _generate_api_request(self, intent: Dict, params: Dict) -> Dict:
        """Generate API request from intent and parameters."""
        # Map intent to API endpoint
        endpoint_mapping = {
            "get_license": "/api/v1/licenses",
            "create_user": "/api/v1/users",
            "check_status": "/api/v1/status"
        }
        
        endpoint = endpoint_mapping.get(intent["type"], "/api/v1/default")
        
        return {
            "method": "GET" if intent["type"].startswith("get") else "POST",
            "endpoint": endpoint,
            "parameters": params
        }

    async def _extract_command_parameters(self, text: str) -> Dict:
        """Extract parameters from voice command."""
        params = {}
        
        # Extract key information using basic NLP
        words = text.lower().split()
        
        # Extract dates
        if "today" in words:
            params["date"] = datetime.now().date().isoformat()
            
        # Extract numbers
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            params["number"] = numbers[0]
            
        return params

from typing import Dict, Any, List
import openai
from app.core.logger import logger
from app.models.documentation import APIEndpoint, Documentation

class AIDocs:
    def __init__(self, openai_api_key: str):
        self.openai = openai
        self.openai.api_key = openai_api_key
        
    async def generate_endpoint_docs(self, endpoint: APIEndpoint) -> Documentation:
        try:
            # Generate documentation using GPT
            prompt = self._create_doc_prompt(endpoint)
            response = await self._generate_docs(prompt)
            
            return Documentation(
                endpoint=endpoint.path,
                description=response['description'],
                parameters=response['parameters'],
                examples=response['examples'],
                generated_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            raise
            
    async def generate_code_samples(self, endpoint: APIEndpoint, languages: List[str]) -> Dict[str, str]:
        try:
            samples = {}
            for lang in languages:
                prompt = self._create_code_sample_prompt(endpoint, lang)
                sample = await self._generate_code_sample(prompt)
                samples[lang] = sample
            return samples
        except Exception as e:
            logger.error(f"Code sample generation failed: {str(e)}")
            raise 
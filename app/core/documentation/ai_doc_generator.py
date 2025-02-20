from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.documentation import APIEndpoint, Documentation, CodeExample, InteractiveGuide
from app.core.ai.nlp_processor import NLPProcessor

class AIDocumentationGenerator:
    def __init__(self, nlp_processor: NLPProcessor):
        self.nlp = nlp_processor
        self.docs_cache: Dict[str, Documentation] = {}
        self.examples_cache: Dict[str, List[CodeExample]] = {}
        
    async def generate_documentation(self, endpoint: APIEndpoint) -> Documentation:
        try:
            # Generate natural language description
            description = await self._generate_description(endpoint)
            
            # Generate code examples
            examples = await self._generate_code_examples(endpoint)
            
            # Create interactive guides
            guides = await self._create_interactive_guides(endpoint)
            
            # Generate error handling docs
            error_docs = await self._generate_error_docs(endpoint)
            
            doc = Documentation(
                endpoint_id=endpoint.id,
                description=description,
                examples=examples,
                guides=guides,
                error_handling=error_docs,
                generated_at=datetime.utcnow()
            )
            
            self.docs_cache[endpoint.id] = doc
            return doc
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            raise 
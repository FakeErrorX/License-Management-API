from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.documentation import APIDoc, CodeExample, DocTemplate
from app.core.ai.doc_ai import DocumentationAI

class SmartDocGenerator:
    def __init__(self, doc_ai: DocumentationAI):
        self.ai = doc_ai
        self.doc_templates: Dict[str, DocTemplate] = {}
        self.code_examples: Dict[str, List[CodeExample]] = {}
        self.generated_docs: Dict[str, APIDoc] = {}
        
    async def generate_smart_documentation(self, api_spec: Dict[str, Any]) -> APIDoc:
        try:
            # Analyze API specification
            analysis = await self._analyze_api_spec(api_spec)
            
            # Generate natural language description
            description = await self._generate_description(analysis)
            
            # Create code examples
            examples = await self._generate_code_examples(analysis)
            
            # Generate usage guidelines
            guidelines = await self._generate_usage_guidelines(analysis)
            
            # Create interactive tutorials
            tutorials = await self._create_interactive_tutorials(analysis)
            
            # Generate error handling documentation
            error_docs = await self._generate_error_docs(analysis)
            
            return APIDoc(
                spec_version=api_spec["version"],
                description=description,
                examples=examples,
                guidelines=guidelines,
                tutorials=tutorials,
                error_handling=error_docs,
                generated_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            raise 
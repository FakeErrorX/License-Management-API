from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.diagnostics import ErrorPattern, DiagnosisResult, ErrorSolution
from app.core.analytics import APIAnalytics

class AIErrorAnalyzer:
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.known_solutions: Dict[str, List[ErrorSolution]] = {}
        
    async def analyze_error(self, error_data: Dict[str, Any]) -> DiagnosisResult:
        try:
            # Extract error patterns
            pattern = await self._extract_error_pattern(error_data)
            
            # Match with known patterns
            matches = await self._match_error_patterns(pattern)
            
            # Generate solution recommendations
            solutions = await self._generate_solutions(matches)
            
            # Create diagnosis result
            result = DiagnosisResult(
                error_id=error_data.get('id'),
                error_type=error_data.get('type'),
                patterns_matched=matches,
                suggested_solutions=solutions,
                confidence_score=self._calculate_confidence(matches),
                analyzed_at=datetime.utcnow()
            )
            
            # Update error patterns database
            await self._update_error_patterns(pattern, result)
            
            return result
        except Exception as e:
            logger.error(f"Error analysis failed: {str(e)}")
            raise 
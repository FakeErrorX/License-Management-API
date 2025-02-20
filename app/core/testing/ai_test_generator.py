from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.testing import TestCase, TestSuite, TestResult, TestCoverage
from app.core.ai.test_ai import TestAI

class AITestGenerator:
    def __init__(self, test_ai: TestAI):
        self.test_ai = test_ai
        self.test_suites: Dict[str, TestSuite] = {}
        self.coverage_data: Dict[str, TestCoverage] = {}
        
    async def generate_test_suite(self, endpoint: APIEndpoint) -> TestSuite:
        try:
            # Generate test cases using AI
            test_cases = await self._generate_test_cases(endpoint)
            
            # Generate edge cases
            edge_cases = await self._generate_edge_cases(endpoint)
            
            # Generate security tests
            security_tests = await self._generate_security_tests(endpoint)
            
            # Create test suite
            suite = TestSuite(
                endpoint_id=endpoint.id,
                test_cases=test_cases + edge_cases + security_tests,
                coverage=await self._calculate_coverage(test_cases),
                generated_at=datetime.utcnow()
            )
            
            self.test_suites[endpoint.id] = suite
            return suite
            
        except Exception as e:
            logger.error(f"Test generation failed: {str(e)}")
            raise 
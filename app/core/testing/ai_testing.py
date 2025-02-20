from typing import Dict, Any, List
import asyncio
from app.core.logger import logger
from app.models.testing import TestCase, TestResult, TestSuite

class AITestingSystem:
    def __init__(self):
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        
    async def generate_test_cases(self, endpoint: APIEndpoint) -> List[TestCase]:
        try:
            # Generate test cases using AI
            test_cases = await self._ai_generate_tests(endpoint)
            
            # Add to test suite
            suite = TestSuite(
                name=f"suite_{endpoint.path}",
                endpoint=endpoint,
                test_cases=test_cases
            )
            self.test_suites[endpoint.path] = suite
            
            return test_cases
        except Exception as e:
            logger.error(f"Test case generation failed: {str(e)}")
            raise
            
    async def run_tests(self, endpoint_path: str) -> List[TestResult]:
        try:
            suite = self.test_suites.get(endpoint_path)
            if not suite:
                raise ValueError(f"No test suite found for {endpoint_path}")
                
            results = []
            for test_case in suite.test_cases:
                result = await self._execute_test(test_case)
                results.append(result)
                
            self.test_results[endpoint_path] = results
            return results
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            raise 
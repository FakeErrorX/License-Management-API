from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from datetime import datetime
import logging
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from app.core.config import settings
from app.services.ai_service import AIService
from app.models.testing import TestCase, TestSuite, TestResult, TestMetrics

class AdaptiveTestingService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.test_results = self.db.test_results
        self.ai_service = AIService()
        self.logger = logging.getLogger(__name__)
        self.test_classifier = RandomForestClassifier()

    async def generate_test_suite(self, api_spec: Dict) -> TestSuite:
        """Generate adaptive test suite based on API specification."""
        try:
            # Analyze API specification
            analysis = await self._analyze_api_spec(api_spec)
            
            # Generate test cases
            test_cases = await self._generate_test_cases(analysis)
            
            # Optimize test suite
            optimized_suite = await self._optimize_test_suite(test_cases)
            
            return TestSuite(
                name=f"Adaptive_Suite_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                test_cases=optimized_suite,
                created_at=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Test suite generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Test suite generation failed"
            )

    async def execute_test_suite(self, test_suite: TestSuite) -> List[TestResult]:
        """Execute test suite with adaptive retry and parallel execution."""
        try:
            # Prepare test execution
            execution_plan = await self._create_execution_plan(test_suite)
            
            # Execute tests in parallel
            results = await self._execute_tests_parallel(execution_plan)
            
            # Analyze results
            analysis = await self._analyze_test_results(results)
            
            # Update test suite based on results
            await self._update_test_suite(test_suite, analysis)
            
            return results
        except Exception as e:
            self.logger.error(f"Test execution failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Test execution failed"
            )

    async def analyze_test_coverage(self, test_results: List[TestResult]) -> TestMetrics:
        """Analyze test coverage and generate metrics."""
        try:
            # Calculate coverage metrics
            coverage = await self._calculate_coverage(test_results)
            
            # Identify coverage gaps
            gaps = await self._identify_coverage_gaps(coverage)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(gaps)
            
            return TestMetrics(
                coverage_percentage=coverage["percentage"],
                covered_endpoints=coverage["endpoints"],
                gaps=gaps,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Coverage analysis failed"
            )

    async def optimize_test_performance(self, test_suite: TestSuite) -> TestSuite:
        """Optimize test suite performance using AI."""
        try:
            # Analyze performance metrics
            metrics = await self._analyze_performance(test_suite)
            
            # Identify bottlenecks
            bottlenecks = await self._identify_bottlenecks(metrics)
            
            # Generate optimizations
            optimizations = await self._generate_optimizations(bottlenecks)
            
            # Apply optimizations
            optimized_suite = await self._apply_optimizations(test_suite, optimizations)
            
            return optimized_suite
        except Exception as e:
            self.logger.error(f"Test optimization failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Test optimization failed"
            )

    async def generate_regression_tests(
        self,
        changes: Dict,
        existing_tests: List[TestCase]
    ) -> List[TestCase]:
        """Generate regression tests for code changes."""
        try:
            # Analyze changes
            analysis = await self._analyze_changes(changes)
            
            # Identify impacted areas
            impact = await self._identify_impact(analysis)
            
            # Generate new tests
            new_tests = await self._generate_regression_tests(impact)
            
            # Merge with existing tests
            merged_tests = await self._merge_tests(existing_tests, new_tests)
            
            return merged_tests
        except Exception as e:
            self.logger.error(f"Regression test generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Regression test generation failed"
            )

    async def _analyze_api_spec(self, api_spec: Dict) -> Dict:
        """Analyze API specification for test generation."""
        try:
            # Extract endpoints
            endpoints = await self.ai_service.extract_endpoints(api_spec)
            
            # Analyze parameters
            params = await self.ai_service.analyze_parameters(api_spec)
            
            # Identify dependencies
            deps = await self.ai_service.identify_dependencies(api_spec)
            
            return {
                "endpoints": endpoints,
                "parameters": params,
                "dependencies": deps
            }
        except Exception as e:
            self.logger.error(f"API spec analysis failed: {str(e)}")
            raise

    async def _generate_test_cases(self, analysis: Dict) -> List[TestCase]:
        """Generate test cases based on analysis."""
        try:
            test_cases = []
            
            for endpoint in analysis["endpoints"]:
                # Generate positive tests
                positive = await self.ai_service.generate_positive_tests(endpoint)
                test_cases.extend(positive)
                
                # Generate negative tests
                negative = await self.ai_service.generate_negative_tests(endpoint)
                test_cases.extend(negative)
                
                # Generate edge cases
                edge = await self.ai_service.generate_edge_cases(endpoint)
                test_cases.extend(edge)
            
            return test_cases
        except Exception as e:
            self.logger.error(f"Test case generation failed: {str(e)}")
            raise

    async def _optimize_test_suite(self, test_cases: List[TestCase]) -> List[TestCase]:
        """Optimize test suite for maximum coverage and minimum redundancy."""
        try:
            # Calculate test weights
            weights = await self._calculate_test_weights(test_cases)
            
            # Remove redundant tests
            unique_tests = await self._remove_redundant_tests(test_cases, weights)
            
            # Prioritize tests
            prioritized = await self._prioritize_tests(unique_tests, weights)
            
            return prioritized
        except Exception as e:
            self.logger.error(f"Test suite optimization failed: {str(e)}")
            raise

    async def _create_execution_plan(self, test_suite: TestSuite) -> Dict:
        """Create optimized test execution plan."""
        try:
            # Group tests by dependency
            groups = await self._group_by_dependency(test_suite.test_cases)
            
            # Calculate optimal parallelization
            parallel_groups = await self._calculate_parallel_groups(groups)
            
            # Create execution schedule
            schedule = await self._create_schedule(parallel_groups)
            
            return {
                "groups": parallel_groups,
                "schedule": schedule,
                "estimated_duration": await self._estimate_duration(schedule)
            }
        except Exception as e:
            self.logger.error(f"Execution plan creation failed: {str(e)}")
            raise

    async def _execute_tests_parallel(
        self,
        execution_plan: Dict
    ) -> List[TestResult]:
        """Execute tests in parallel according to plan."""
        try:
            results = []
            for group in execution_plan["groups"]:
                # Execute group in parallel
                group_results = await asyncio.gather(*[
                    self._execute_test(test)
                    for test in group
                ])
                results.extend(group_results)
            
            return results
        except Exception as e:
            self.logger.error(f"Parallel test execution failed: {str(e)}")
            raise

    async def _analyze_test_results(self, results: List[TestResult]) -> Dict:
        """Analyze test results for patterns and insights."""
        try:
            # Calculate success rate
            success_rate = len([r for r in results if r.success]) / len(results)
            
            # Analyze failures
            failure_analysis = await self._analyze_failures([
                r for r in results if not r.success
            ])
            
            # Generate insights
            insights = await self.ai_service.generate_test_insights(results)
            
            return {
                "success_rate": success_rate,
                "failure_analysis": failure_analysis,
                "insights": insights
            }
        except Exception as e:
            self.logger.error(f"Result analysis failed: {str(e)}")
            raise

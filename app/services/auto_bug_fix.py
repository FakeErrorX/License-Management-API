from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from datetime import datetime
import ast
import logging
import difflib
from app.core.config import settings
from app.services.ai_service import AIService
from app.models.bug_fix import BugReport, BugFix, CodePatch
from app.utils.code_analysis import analyze_code, generate_ast

class AutoBugFixService:
    def __init__(self):
        self.ai_service = AIService()
        self.logger = logging.getLogger(__name__)

    async def analyze_and_fix_bug(self, bug_report: BugReport) -> BugFix:
        """Analyze bug report and generate fix using AI."""
        try:
            # Analyze bug report
            analysis = await self._analyze_bug_report(bug_report)
            
            # Generate potential fixes
            fixes = await self._generate_potential_fixes(analysis)
            
            # Test fixes
            tested_fixes = await self._test_fixes(fixes)
            
            # Select best fix
            best_fix = await self._select_best_fix(tested_fixes)
            
            # Apply fix
            applied_fix = await self._apply_fix(best_fix)
            
            return applied_fix
        except Exception as e:
            self.logger.error(f"Bug fix generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Bug fix generation failed"
            )

    async def auto_detect_bugs(self, code: str) -> List[BugReport]:
        """Automatically detect potential bugs in code using AI."""
        try:
            # Generate AST
            ast_tree = await self._generate_ast(code)
            
            # Analyze code patterns
            patterns = await self._analyze_code_patterns(ast_tree)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(patterns)
            
            # Generate bug reports
            reports = await self._generate_bug_reports(anomalies)
            
            return reports
        except Exception as e:
            self.logger.error(f"Bug detection failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Bug detection failed"
            )

    async def validate_fix(self, fix: BugFix) -> bool:
        """Validate a proposed bug fix using AI."""
        try:
            # Check fix syntax
            syntax_valid = await self._validate_syntax(fix.patch)
            
            # Run test cases
            tests_passed = await self._run_test_cases(fix)
            
            # Check for regressions
            no_regressions = await self._check_regressions(fix)
            
            # Verify fix addresses root cause
            root_cause_fixed = await self._verify_root_cause(fix)
            
            return all([
                syntax_valid,
                tests_passed,
                no_regressions,
                root_cause_fixed
            ])
        except Exception as e:
            self.logger.error(f"Fix validation failed: {str(e)}")
            return False

    async def generate_regression_tests(self, fix: BugFix) -> List[str]:
        """Generate regression tests for a bug fix using AI."""
        try:
            # Analyze fix impact
            impact = await self._analyze_fix_impact(fix)
            
            # Generate test cases
            test_cases = await self._generate_test_cases(impact)
            
            # Validate test cases
            validated_tests = await self._validate_test_cases(test_cases)
            
            return validated_tests
        except Exception as e:
            self.logger.error(f"Test generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Test generation failed"
            )

    async def _analyze_bug_report(self, report: BugReport) -> Dict:
        """Analyze bug report using AI."""
        try:
            # Extract key information
            info = await self.ai_service.extract_bug_info(report)
            
            # Classify bug type
            bug_type = await self.ai_service.classify_bug(info)
            
            # Identify potential causes
            causes = await self.ai_service.identify_causes(info)
            
            return {
                "info": info,
                "type": bug_type,
                "causes": causes
            }
        except Exception as e:
            self.logger.error(f"Bug analysis failed: {str(e)}")
            raise

    async def _generate_potential_fixes(self, analysis: Dict) -> List[CodePatch]:
        """Generate potential fixes using AI."""
        try:
            return await self.ai_service.generate_fixes(analysis)
        except Exception as e:
            self.logger.error(f"Fix generation failed: {str(e)}")
            raise

    async def _test_fixes(self, fixes: List[CodePatch]) -> List[Tuple[CodePatch, float]]:
        """Test potential fixes and score them."""
        results = []
        for fix in fixes:
            try:
                # Run tests
                test_results = await self._run_tests(fix)
                
                # Calculate score
                score = await self._calculate_fix_score(fix, test_results)
                
                results.append((fix, score))
            except Exception as e:
                self.logger.warning(f"Fix testing failed: {str(e)}")
                continue
        
        return sorted(results, key=lambda x: x[1], reverse=True)

    async def _select_best_fix(
        self,
        tested_fixes: List[Tuple[CodePatch, float]]
    ) -> CodePatch:
        """Select the best fix based on testing results."""
        if not tested_fixes:
            raise ValueError("No valid fixes found")
        
        return tested_fixes[0][0]

    async def _apply_fix(self, fix: CodePatch) -> BugFix:
        """Apply the selected fix."""
        try:
            # Generate patch
            patch = await self._generate_patch(fix)
            
            # Apply patch
            applied = await self._apply_patch(patch)
            
            # Verify application
            verified = await self._verify_patch(applied)
            
            return BugFix(
                patch=patch,
                applied=applied,
                verified=verified,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Fix application failed: {str(e)}")
            raise

    async def _generate_ast(self, code: str) -> ast.AST:
        """Generate AST from code."""
        try:
            return ast.parse(code)
        except Exception as e:
            self.logger.error(f"AST generation failed: {str(e)}")
            raise

    async def _analyze_code_patterns(self, ast_tree: ast.AST) -> List[Dict]:
        """Analyze code patterns in AST."""
        try:
            return await self.ai_service.analyze_patterns(ast_tree)
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {str(e)}")
            raise

    async def _detect_anomalies(self, patterns: List[Dict]) -> List[Dict]:
        """Detect anomalies in code patterns."""
        try:
            return await self.ai_service.detect_anomalies(patterns)
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            raise

    async def _generate_bug_reports(self, anomalies: List[Dict]) -> List[BugReport]:
        """Generate bug reports from detected anomalies."""
        try:
            return [
                BugReport(
                    title=f"Potential bug in {a['location']}",
                    description=a['description'],
                    severity=a['severity'],
                    timestamp=datetime.utcnow()
                )
                for a in anomalies
            ]
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise

    async def _validate_syntax(self, patch: str) -> bool:
        """Validate patch syntax."""
        try:
            ast.parse(patch)
            return True
        except Exception:
            return False

    async def _run_test_cases(self, fix: BugFix) -> bool:
        """Run test cases for fix."""
        try:
            return await self.ai_service.run_tests(fix)
        except Exception:
            return False

    async def _check_regressions(self, fix: BugFix) -> bool:
        """Check for regressions caused by fix."""
        try:
            return await self.ai_service.check_regressions(fix)
        except Exception:
            return False

    async def _verify_root_cause(self, fix: BugFix) -> bool:
        """Verify fix addresses root cause."""
        try:
            return await self.ai_service.verify_root_cause(fix)
        except Exception:
            return False

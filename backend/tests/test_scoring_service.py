"""
Test Scoring Service

Acts as a judge to evaluate and score E2E test outputs with detailed reasoning.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestScore:
    """Test score with detailed evaluation."""
    test_name: str
    score: float  # 0.0 to 10.0
    max_score: float = 10.0
    category: str = ""
    reasoning: str = ""
    strengths: List[str] = None
    weaknesses: List[str] = None
    recommendations: List[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.weaknesses is None:
            self.weaknesses = []
        if self.recommendations is None:
            self.recommendations = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TestResult:
    """Complete test result with output and scoring."""
    test_name: str
    test_output: Dict[str, Any]
    score: TestScore
    execution_time: float
    status: str  # "passed", "failed", "error"
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class TestScoringService:
    """Service to score and evaluate E2E test outputs."""
    
    def __init__(self):
        self.scoring_criteria = {
            "file_reader": {
                "functionality": 3.0,
                "security": 2.0,
                "error_handling": 2.0,
                "performance": 1.5,
                "documentation": 1.5
            },
            "text_processor": {
                "functionality": 3.0,
                "security": 2.0,
                "error_handling": 2.0,
                "performance": 1.5,
                "documentation": 1.5
            },
            "document_analyzer": {
                "functionality": 3.0,
                "security": 2.0,
                "error_handling": 2.0,
                "performance": 1.5,
                "documentation": 1.5
            },
            "web_content_fetcher": {
                "functionality": 3.0,
                "security": 2.0,
                "error_handling": 2.0,
                "performance": 1.5,
                "documentation": 1.5
            },
            "data_formatter": {
                "functionality": 3.0,
                "security": 2.0,
                "error_handling": 2.0,
                "performance": 1.5,
                "documentation": 1.5
            }
        }
    
    def score_test_output(self, test_name: str, test_output: Dict[str, Any], 
                         execution_time: float, status: str) -> TestResult:
        """
        Score a test output and return detailed evaluation.
        
        Args:
            test_name: Name of the test
            test_output: Raw test output
            execution_time: Time taken to execute
            status: Test status (passed/failed/error)
            
        Returns:
            TestResult with detailed scoring
        """
        try:
            # Determine test category
            category = self._determine_test_category(test_name)
            
            # Score the test based on category and output
            score = self._evaluate_test(test_name, test_output, execution_time, status, category)
            
            # Create test result
            result = TestResult(
                test_name=test_name,
                test_output=test_output,
                score=score,
                execution_time=execution_time,
                status=status
            )
            
            logger.info(f"Test {test_name} scored: {score.score}/{score.max_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring test {test_name}: {str(e)}")
            # Return default score on error
            default_score = TestScore(
                test_name=test_name,
                score=0.0,
                reasoning=f"Scoring error: {str(e)}",
                weaknesses=["Scoring service error"]
            )
            return TestResult(
                test_name=test_name,
                test_output=test_output,
                score=default_score,
                execution_time=execution_time,
                status="error"
            )
    
    def _determine_test_category(self, test_name: str) -> str:
        """Determine the test category from test name."""
        test_name_lower = test_name.lower()
        
        if "file_reader" in test_name_lower:
            return "file_reader"
        elif "text_processor" in test_name_lower:
            return "text_processor"
        elif "document_analyzer" in test_name_lower:
            return "document_analyzer"
        elif "web_content_fetcher" in test_name_lower:
            return "web_content_fetcher"
        elif "data_formatter" in test_name_lower:
            return "data_formatter"
        elif "workflow" in test_name_lower or "scenario" in test_name_lower:
            return "integration"
        else:
            return "general"
    
    def _evaluate_test(self, test_name: str, test_output: Dict[str, Any], 
                       execution_time: float, status: str, category: str) -> TestScore:
        """Evaluate and score a test based on its category and output."""
        
        if category in self.scoring_criteria:
            return self._evaluate_specific_tool(test_name, test_output, execution_time, status, category)
        elif category == "integration":
            return self._evaluate_integration_test(test_name, test_output, execution_time, status)
        else:
            return self._evaluate_general_test(test_name, test_output, execution_time, status)
    
    def _evaluate_specific_tool(self, test_name: str, test_output: Dict[str, Any], 
                               execution_time: float, status: str, category: str) -> TestScore:
        """Evaluate a specific MCP tool test."""
        
        criteria = self.scoring_criteria[category]
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Base score from status
        base_score = 10.0 if status == "passed" else 5.0 if status == "failed" else 0.0
        
        # Evaluate functionality
        functionality_score = self._evaluate_functionality(test_output, category)
        strengths.extend(functionality_score[0])
        weaknesses.extend(functionality_score[1])
        recommendations.extend(functionality_score[2])
        
        # Evaluate security
        security_score = self._evaluate_security(test_output, category)
        strengths.extend(security_score[0])
        weaknesses.extend(security_score[1])
        recommendations.extend(security_score[2])
        
        # Evaluate error handling
        error_handling_score = self._evaluate_error_handling(test_output, category)
        strengths.extend(error_handling_score[0])
        weaknesses.extend(error_handling_score[1])
        recommendations.extend(error_handling_score[2])
        
        # Evaluate performance
        performance_score = self._evaluate_performance(execution_time, category)
        strengths.extend(performance_score[0])
        weaknesses.extend(performance_score[1])
        recommendations.extend(performance_score[2])
        
        # Calculate weighted score
        weighted_score = (
            functionality_score[3] * criteria["functionality"] +
            security_score[3] * criteria["security"] +
            error_handling_score[3] * criteria["error_handling"] +
            performance_score[3] * criteria["performance"] +
            (base_score / 10.0) * criteria["documentation"]
        ) / sum(criteria.values()) * 10.0
        
        reasoning = f"Tool {category} evaluated across {len(criteria)} criteria: "
        reasoning += f"Functionality ({functionality_score[3]:.1f}/10), "
        reasoning += f"Security ({security_score[3]:.1f}/10), "
        reasoning += f"Error Handling ({error_handling_score[3]:.1f}/10), "
        reasoning += f"Performance ({performance_score[3]:.1f}/10)"
        
        return TestScore(
            test_name=test_name,
            score=round(weighted_score, 2),
            category=category,
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _evaluate_functionality(self, test_output: Dict[str, Any], category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate functionality of the test output."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            if "status" in test_output:
                if test_output["status"] == "success":
                    score += 8.0
                    strengths.append("Tool executed successfully")
                    
                    # Check for specific functionality indicators
                    if category == "file_reader" and "content" in test_output:
                        score += 1.0
                        strengths.append("File content successfully read")
                    elif category == "web_content_fetcher" and "content" in test_output:
                        score += 1.0
                        strengths.append("Web content successfully fetched")
                    elif category == "text_processor" and "processed_text" in test_output:
                        score += 1.0
                        strengths.append("Text processing completed successfully")
                        
                elif test_output["status"] == "error":
                    score += 2.0
                    weaknesses.append("Tool execution failed")
                    if "error_message" in test_output:
                        strengths.append("Error message provided")
                        score += 1.0
                        
            # Check for expected fields based on category
            if category == "file_reader":
                if "file_info" in test_output:
                    score += 1.0
                    strengths.append("File metadata provided")
                if "metrics" in test_output:
                    score += 1.0
                    strengths.append("Content metrics calculated")
                    
            elif category == "web_content_fetcher":
                if "results_count" in test_output:
                    score += 1.0
                    strengths.append("Search results count provided")
                if "search_engine" in test_output:
                    score += 1.0
                    strengths.append("Search engine information included")
                    
            elif category == "text_processor":
                if "original_length" in test_output and "processed_length" in test_output:
                    score += 1.0
                    strengths.append("Text length metrics provided")
                    
            elif category == "document_analyzer":
                if "analysis_type" in test_output:
                    score += 1.0
                    strengths.append("Analysis type specified")
                if "metrics" in test_output:
                    score += 1.0
                    strengths.append("Analysis metrics provided")
                    
            elif category == "data_formatter":
                if "output_format" in test_output:
                    score += 1.0
                    strengths.append("Output format specified")
                if "formatted_data" in test_output:
                    score += 1.0
                    strengths.append("Formatted data provided")
            
            # Cap score at 10.0
            score = min(score, 10.0)
            
        except Exception as e:
            weaknesses.append(f"Functionality evaluation error: {str(e)}")
            score = 0.0
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_security(self, test_output: Dict[str, Any], category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate security aspects of the test output."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Check for security-related fields
            if "error_type" in test_output:
                if test_output["error_type"] == "validation_error":
                    score += 3.0
                    strengths.append("Input validation errors properly categorized")
                elif test_output["error_type"] == "security_error":
                    score += 4.0
                    strengths.append("Security errors properly identified")
                    
            # Check for path validation in file operations
            if category == "file_reader":
                if "Invalid file path" in str(test_output.get("error_message", "")):
                    score += 2.0
                    strengths.append("Path validation working correctly")
                    
            # Check for URL validation in web operations
            if category == "web_content_fetcher":
                if "Invalid URL" in str(test_output.get("error_message", "")):
                    score += 2.0
                    strengths.append("URL validation working correctly")
                    
            # Check for input sanitization
            if "sanitized_params" in str(test_output):
                score += 2.0
                strengths.append("Input sanitization implemented")
                
            # Check for size limits
            if "exceeds maximum" in str(test_output.get("error_message", "")):
                score += 1.0
                strengths.append("Size limits enforced")
                
            # Cap score at 10.0
            score = min(score, 10.0)
            
        except Exception as e:
            weaknesses.append(f"Security evaluation error: {str(e)}")
            score = 0.0
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_error_handling(self, test_output: Dict[str, Any], category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate error handling quality."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Check for error message presence
            if "error_message" in test_output:
                score += 3.0
                strengths.append("Error message provided")
                
                # Check error message quality
                error_msg = test_output["error_message"]
                if len(error_msg) > 10:
                    score += 1.0
                    strengths.append("Detailed error message")
                if "validation" in error_msg.lower():
                    score += 1.0
                    strengths.append("Validation error properly identified")
                    
            # Check for error categorization
            if "error_type" in test_output:
                score += 2.0
                strengths.append("Error properly categorized")
                
            # Check for graceful degradation
            if test_output.get("status") == "error" and "content" in test_output:
                score += 2.0
                strengths.append("Graceful error handling with fallback content")
                
            # Check for user-friendly error messages
            if "error_message" in test_output:
                error_msg = test_output["error_message"]
                if not any(tech_term in error_msg.lower() for tech_term in ["exception", "traceback", "stack"]):
                    score += 1.0
                    strengths.append("User-friendly error message")
                    
            # Cap score at 10.0
            score = min(score, 10.0)
            
        except Exception as e:
            weaknesses.append(f"Error handling evaluation error: {str(e)}")
            score = 0.0
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_performance(self, execution_time: float, category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate performance based on execution time."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Performance thresholds (in seconds)
            excellent_threshold = 0.1
            good_threshold = 0.5
            acceptable_threshold = 2.0
            poor_threshold = 5.0
            
            if execution_time <= excellent_threshold:
                score += 10.0
                strengths.append("Excellent performance")
            elif execution_time <= good_threshold:
                score += 8.0
                strengths.append("Good performance")
            elif execution_time <= acceptable_threshold:
                score += 6.0
                strengths.append("Acceptable performance")
            elif execution_time <= poor_threshold:
                score += 3.0
                weaknesses.append("Performance could be improved")
                recommendations.append("Consider optimizing tool execution")
            else:
                score += 1.0
                weaknesses.append("Poor performance")
                recommendations.append("Performance optimization required")
                
            # Add specific performance insights
            if category == "file_reader" and execution_time > 1.0:
                recommendations.append("File reading performance may benefit from streaming for large files")
            elif category == "web_content_fetcher" and execution_time > 2.0:
                recommendations.append("Web content fetching may benefit from caching or async processing")
            elif category == "text_processor" and execution_time > 0.5:
                recommendations.append("Text processing may benefit from batch processing for large texts")
                
        except Exception as e:
            weaknesses.append(f"Performance evaluation error: {str(e)}")
            score = 0.0
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_integration_test(self, test_name: str, test_output: Dict[str, Any], 
                                  execution_time: float, status: str) -> TestScore:
        """Evaluate integration/workflow tests."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Base score from status
            if status == "passed":
                score += 8.0
                strengths.append("Integration test passed successfully")
            else:
                score += 2.0
                weaknesses.append("Integration test failed")
                
            # Check for workflow completeness
            if "workflow" in test_name.lower():
                if "step" in str(test_output).lower() or "workflow" in str(test_output).lower():
                    score += 1.0
                    strengths.append("Workflow steps properly tracked")
                    
            # Check for multiple tool usage
            if any(tool in str(test_output).lower() for tool in ["file_reader", "text_processor", "web_content_fetcher"]):
                score += 1.0
                strengths.append("Multiple tools integrated successfully")
                
            # Performance evaluation for integration tests
            if execution_time <= 5.0:
                score += 1.0
                strengths.append("Integration workflow completed efficiently")
            else:
                weaknesses.append("Integration workflow took longer than expected")
                recommendations.append("Consider optimizing workflow execution")
                
        except Exception as e:
            weaknesses.append(f"Integration evaluation error: {str(e)}")
            score = 0.0
            
        reasoning = f"Integration test evaluated for workflow completeness and tool integration"
        
        return TestScore(
            test_name=test_name,
            score=round(score, 2),
            category="integration",
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _evaluate_general_test(self, test_name: str, test_output: Dict[str, Any], 
                               execution_time: float, status: str) -> TestScore:
        """Evaluate general tests not fitting specific categories."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Base score from status
            if status == "passed":
                score += 7.0
                strengths.append("Test passed successfully")
            else:
                score += 2.0
                weaknesses.append("Test failed")
                
            # Check for output quality
            if test_output and len(str(test_output)) > 10:
                score += 2.0
                strengths.append("Test provided meaningful output")
                
            # Performance check
            if execution_time <= 1.0:
                score += 1.0
                strengths.append("Test executed efficiently")
            else:
                weaknesses.append("Test execution time could be improved")
                
        except Exception as e:
            weaknesses.append(f"General evaluation error: {str(e)}")
            score = 0.0
            
        reasoning = f"General test evaluated for basic functionality and performance"
        
        return TestScore(
            test_name=test_name,
            score=round(score, 2),
            category="general",
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def generate_test_report(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Generate comprehensive test report with scoring analysis."""
        try:
            total_tests = len(test_results)
            passed_tests = len([r for r in test_results if r.status == "passed"])
            failed_tests = len([r for r in test_results if r.status == "failed"])
            error_tests = len([r for r in test_results if r.status == "error"])
            
            # Calculate average scores
            scores = [r.score.score for r in test_results if r.score.score > 0]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Category breakdown
            categories = {}
            for result in test_results:
                category = result.score.category
                if category not in categories:
                    categories[category] = {"count": 0, "total_score": 0.0, "tests": []}
                categories[category]["count"] += 1
                categories[category]["total_score"] += result.score.score
                categories[category]["tests"].append(result.test_name)
                
            # Calculate category averages
            for category in categories:
                categories[category]["avg_score"] = (
                    categories[category]["total_score"] / categories[category]["count"]
                )
            
            # Performance analysis
            execution_times = [r.execution_time for r in test_results]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
            total_execution_time = sum(execution_times)
            
            # Generate recommendations
            recommendations = []
            if avg_score < 7.0:
                recommendations.append("Overall test quality needs improvement")
            if avg_execution_time > 2.0:
                recommendations.append("Performance optimization recommended")
            if failed_tests > 0:
                recommendations.append("Failed tests need investigation and fixing")
                
            report = {
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "error_tests": error_tests,
                    "success_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0.0,
                    "average_score": round(avg_score, 2),
                    "average_execution_time": round(avg_execution_time, 3),
                    "total_execution_time": round(total_execution_time, 3)
                },
                "categories": categories,
                "test_results": [asdict(result) for result in test_results],
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating test report: {str(e)}")
            return {
                "error": f"Failed to generate report: {str(e)}",
                "generated_at": datetime.now().isoformat()
            }


# Global instance for easy access
test_scoring_service = TestScoringService()

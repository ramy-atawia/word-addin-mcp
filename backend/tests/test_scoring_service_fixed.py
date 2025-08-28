"""
Fixed Test Scoring Service

Corrects the scoring logic to properly normalize scores to 0-10 scale.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TestScore:
    """Test score with detailed evaluation."""
    test_name: str
    score: float  # Score out of 10
    max_score: float = 10.0
    category: str = ""
    reasoning: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        # Ensure score is within valid range
        self.score = max(0.0, min(10.0, self.score))


@dataclass
class TestResult:
    """Complete test result with output and scoring."""
    test_name: str
    test_output: Dict[str, Any]
    score: TestScore
    execution_time: float
    status: str
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class FixedTestScoringService:
    """Fixed service to score and evaluate E2E test outputs with proper 0-10 scale."""
    
    def __init__(self):
        # Scoring criteria with proper weights that sum to 1.0 (100%)
        self.scoring_criteria = {
            "file_reader": {
                "functionality": 0.35,    # 35% - Core functionality
                "security": 0.20,         # 20% - Security validation
                "error_handling": 0.25,   # 25% - Error handling
                "performance": 0.20       # 20% - Performance
            },
            "text_processor": {
                "functionality": 0.35,    # 35% - Core functionality
                "security": 0.20,         # 20% - Security validation
                "error_handling": 0.25,   # 25% - Error handling
                "performance": 0.20       # 20% - Performance
            },
            "document_analyzer": {
                "functionality": 0.35,    # 35% - Core functionality
                "security": 0.20,         # 20% - Security validation
                "error_handling": 0.25,   # 25% - Error handling
                "performance": 0.20       # 20% - Performance
            },
            "web_content_fetcher": {
                "functionality": 0.35,    # 35% - Core functionality
                "security": 0.20,         # 20% - Security validation
                "error_handling": 0.25,   # 25% - Error handling
                "performance": 0.20       # 20% - Performance
            },
            "data_formatter": {
                "functionality": 0.35,    # 35% - Core functionality
                "security": 0.20,         # 20% - Security validation
                "error_handling": 0.25,   # 25% - Error handling
                "performance": 0.20       # 20% - Performance
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
            
            logger.info(f"Test {test_name} scored: {score.score:.1f}/10.0")
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
        """Evaluate a specific MCP tool test with proper 0-10 scoring."""
        
        criteria = self.scoring_criteria[category]
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Evaluate each criterion and get scores (0-10 scale)
        functionality_score = self._evaluate_functionality(test_output, category)
        strengths.extend(functionality_score[0])
        weaknesses.extend(functionality_score[1])
        recommendations.extend(functionality_score[2])
        
        security_score = self._evaluate_security(test_output, category)
        strengths.extend(security_score[0])
        weaknesses.extend(security_score[1])
        recommendations.extend(security_score[2])
        
        error_handling_score = self._evaluate_error_handling(test_output, category)
        strengths.extend(error_handling_score[0])
        weaknesses.extend(error_handling_score[1])
        recommendations.extend(error_handling_score[2])
        
        performance_score = self._evaluate_performance(execution_time, category)
        strengths.extend(performance_score[0])
        weaknesses.extend(performance_score[1])
        recommendations.extend(performance_score[2])
        
        # Calculate weighted score (0-10 scale)
        weighted_score = (
            functionality_score[3] * criteria["functionality"] +
            security_score[3] * criteria["security"] +
            error_handling_score[3] * criteria["error_handling"] +
            performance_score[3] * criteria["performance"]
        )
        
        # Ensure score is within 0-10 range
        final_score = max(0.0, min(10.0, weighted_score))
        
        reasoning = f"Tool {category} evaluated across {len(criteria)} criteria: "
        reasoning += f"Functionality ({functionality_score[3]:.1f}/10), "
        reasoning += f"Security ({security_score[3]:.1f}/10), "
        reasoning += f"Error Handling ({error_handling_score[3]:.1f}/10), "
        reasoning += f"Performance ({performance_score[3]:.1f}/10)"
        
        return TestScore(
            test_name=test_name,
            score=round(final_score, 1),
            category=category,
            reasoning=reasoning,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _evaluate_functionality(self, test_output: Dict[str, Any], category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate functionality of the test output (0-10 scale)."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            if "status" in test_output:
                if test_output["status"] == "success":
                    score += 6.0  # Base success score
                    strengths.append("Tool executed successfully")
                    
                    # Check for specific functionality indicators
                    if category == "file_reader" and "content" in test_output:
                        score += 2.0
                        strengths.append("File content successfully read")
                    elif category == "web_content_fetcher" and "content" in test_output:
                        score += 2.0
                        strengths.append("Web content successfully fetched")
                    elif category == "text_processor" and "processed_text" in test_output:
                        score += 2.0
                        strengths.append("Text processing completed successfully")
                        
                elif test_output["status"] == "error":
                    score += 2.0  # Base error score
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
            score = min(10.0, score)
            
        except Exception as e:
            logger.error(f"Error evaluating functionality: {str(e)}")
            score = 0.0
            weaknesses.append("Functionality evaluation error")
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_security(self, test_output: Dict[str, Any], category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate security aspects (0-10 scale)."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Check for security validation
            if "status" in test_output and test_output["status"] == "error":
                if "error_message" in test_output:
                    error_msg = test_output["error_message"].lower()
                    if "invalid" in error_msg or "validation" in error_msg:
                        score += 5.0
                        strengths.append("Input validation working correctly")
                        
            # Check for path traversal protection
            if category == "file_reader":
                if "status" in test_output and test_output["status"] == "error":
                    if "path" in test_output.get("error_message", "").lower():
                        score += 3.0
                        strengths.append("Path validation working correctly")
                        
            # Check for URL validation
            if category == "web_content_fetcher":
                if "status" in test_output and test_output["status"] == "error":
                    if "url" in test_output.get("error_message", "").lower():
                        score += 3.0
                        strengths.append("URL validation working correctly")
                        
            # Check for operation validation
            if category == "text_processor":
                if "status" in test_output and test_output["status"] == "error":
                    if "operation" in test_output.get("error_message", "").lower():
                        score += 2.0
                        strengths.append("Operation validation working correctly")
            
            # Cap score at 10.0
            score = min(10.0, score)
            
        except Exception as e:
            logger.error(f"Error evaluating security: {str(e)}")
            score = 0.0
            weaknesses.append("Security evaluation error")
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_error_handling(self, test_output: Dict[str, Any], category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate error handling (0-10 scale)."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Check for error message presence
            if "error_message" in test_output:
                score += 3.0
                strengths.append("Error message provided")
                
                # Check for detailed error message
                error_msg = test_output["error_message"]
                if len(error_msg) > 10:
                    score += 2.0
                    strengths.append("Detailed error message")
                    
                # Check for error categorization
                if "error_type" in test_output:
                    score += 2.0
                    strengths.append("Error properly categorized")
                    
                # Check for user-friendly error message
                if not any(word in error_msg.lower() for word in ["exception", "traceback", "stack"]):
                    score += 2.0
                    strengths.append("User-friendly error message")
                    
            # Check for graceful failure
            if "status" in test_output and test_output["status"] == "error":
                score += 1.0
                strengths.append("Graceful error handling")
            
            # Cap score at 10.0
            score = min(10.0, score)
            
        except Exception as e:
            logger.error(f"Error evaluating error handling: {str(e)}")
            score = 0.0
            weaknesses.append("Error handling evaluation error")
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_performance(self, execution_time: float, category: str) -> Tuple[List[str], List[str], List[str], float]:
        """Evaluate performance (0-10 scale)."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Performance scoring based on execution time
            if execution_time < 0.001:  # Ultra-fast
                score = 10.0
                strengths.append("Ultra-fast execution")
            elif execution_time < 0.01:  # Very fast
                score = 9.0
                strengths.append("Very fast execution")
            elif execution_time < 0.1:  # Fast
                score = 8.0
                strengths.append("Fast execution")
            elif execution_time < 1.0:  # Good
                score = 7.0
                strengths.append("Good performance")
            elif execution_time < 5.0:  # Acceptable
                score = 6.0
                strengths.append("Acceptable performance")
            elif execution_time < 10.0:  # Slow
                score = 4.0
                weaknesses.append("Slow execution")
            else:  # Very slow
                score = 2.0
                weaknesses.append("Very slow execution")
                
        except Exception as e:
            logger.error(f"Error evaluating performance: {str(e)}")
            score = 0.0
            weaknesses.append("Performance evaluation error")
            
        return strengths, weaknesses, recommendations, score
    
    def _evaluate_integration_test(self, test_name: str, test_output: Dict[str, Any], 
                                 execution_time: float) -> TestScore:
        """Evaluate integration tests (0-10 scale)."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Base score for successful integration
            if test_output.get("status") == "success":
                score += 6.0
                strengths.append("Integration test passed successfully")
                
                # Check for workflow completion
                if "workflow" in test_output:
                    score += 2.0
                    strengths.append("Workflow steps properly tracked")
                    
                # Check for tool integration
                if "tools_used" in test_output:
                    score += 2.0
                    strengths.append("Multiple tools integrated successfully")
                    
            # Performance bonus
            if execution_time < 0.01:
                score += 1.0
                strengths.append("Integration workflow completed efficiently")
                
        except Exception as e:
            logger.error(f"Error evaluating integration test: {str(e)}")
            score = 0.0
            weaknesses.append("Integration evaluation error")
            
        # Cap score at 10.0
        score = min(10.0, score)
        
        return TestScore(
            test_name=test_name,
            score=round(score, 1),
            category="integration",
            reasoning="Integration test evaluated for workflow completeness and tool integration",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _evaluate_general_test(self, test_name: str, test_output: Dict[str, Any], 
                              execution_time: float) -> TestScore:
        """Evaluate general tests (0-10 scale)."""
        strengths = []
        weaknesses = []
        recommendations = []
        score = 0.0
        
        try:
            # Basic evaluation for general tests
            if test_output.get("status") == "success":
                score = 8.0
                strengths.append("Test completed successfully")
            elif test_output.get("status") == "error":
                score = 4.0
                weaknesses.append("Test encountered an error")
            else:
                score = 6.0
                strengths.append("Test completed with unknown status")
                
        except Exception as e:
            logger.error(f"Error evaluating general test: {str(e)}")
            score = 0.0
            weaknesses.append("General evaluation error")
            
        return TestScore(
            test_name=test_name,
            score=round(score, 1),
            category="general",
            reasoning="General test evaluation",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

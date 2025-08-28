"""
Demo Script: Test Scoring System

Demonstrates how the test scoring service evaluates different types of test outputs
and provides detailed scoring with reasoning.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.services.test_scoring_service import test_scoring_service, TestResult


def demo_scoring_system():
    """Demonstrate the test scoring system with various test outputs."""
    
    print("🎯 Test Scoring System Demo")
    print("=" * 50)
    print("This demo shows how the AI judge evaluates different test outputs\n")
    
    # Demo 1: Perfect file reader test
    print("📁 Demo 1: Perfect File Reader Test")
    print("-" * 40)
    
    perfect_file_output = {
        "status": "success",
        "content": "Sample file content for testing",
        "file_info": {"name": "test.txt", "size": 100},
        "metrics": {"characters": 100, "words": 20},
        "content_type": "text"
    }
    
    result1 = test_scoring_service.score_test_output(
        "perfect_file_reader_test",
        perfect_file_output,
        0.05,  # 50ms execution time
        "passed"
    )
    
    print(f"Test: {result1.test_name}")
    print(f"Score: {result1.score.score}/10")
    print(f"Category: {result1.score.category}")
    print(f"Reasoning: {result1.score.reasoning}")
    print(f"Strengths: {', '.join(result1.score.strengths[:3])}...")
    print()
    
    # Demo 2: Failed security test
    print("🔒 Demo 2: Failed Security Test")
    print("-" * 40)
    
    failed_security_output = {
        "status": "error",
        "error_message": "Invalid file path: ../../../etc/passwd",
        "error_type": "validation_error"
    }
    
    result2 = test_scoring_service.score_test_output(
        "failed_security_test",
        failed_security_output,
        0.001,  # 1ms execution time
        "passed"  # Passed because it correctly rejected malicious path
    )
    
    print(f"Test: {result2.test_name}")
    print(f"Score: {result2.score.score}/10")
    print(f"Category: {result2.score.category}")
    print(f"Reasoning: {result2.score.reasoning}")
    print(f"Strengths: {', '.join(result2.score.strengths[:3])}...")
    print()
    
    # Demo 3: Web search with Rmay Atawia
    print("🌐 Demo 3: Web Search Test (Rmay Atawia)")
    print("-" * 40)
    
    web_search_output = {
        "status": "success",
        "content": [
            {
                "title": "Rmay Atawia: Machine Learning Research",
                "url": "https://scholar.google.com/citations?user=rmay_atawia",
                "snippet": "Research in computer vision and ML algorithms",
                "relevance": 0.95
            }
        ],
        "query": "rmay atawia research publications",
        "results_count": 1,
        "search_engine": "google"
    }
    
    result3 = test_scoring_service.score_test_output(
        "rmay_atawia_research_search",
        web_search_output,
        0.8,  # 800ms execution time
        "passed"
    )
    
    print(f"Test: {result3.test_name}")
    print(f"Score: {result3.score.score}/10")
    print(f"Category: {result3.score.category}")
    print(f"Reasoning: {result3.score.reasoning}")
    print(f"Strengths: {', '.join(result3.score.strengths[:3])}...")
    print()
    
    # Demo 4: Performance issue test
    print("⏱️ Demo 4: Performance Issue Test")
    print("-" * 40)
    
    slow_test_output = {
        "status": "success",
        "processed_text": "Large text processing result",
        "operation": "summarize",
        "original_length": 10000,
        "processed_length": 1000
    }
    
    result4 = test_scoring_service.score_test_output(
        "slow_performance_test",
        slow_test_output,
        8.5,  # 8.5 seconds execution time
        "passed"
    )
    
    print(f"Test: {result4.test_name}")
    print(f"Score: {result4.score.score}/10")
    print(f"Category: {result4.score.category}")
    print(f"Reasoning: {result4.score.reasoning}")
    print(f"Strengths: {', '.join(result4.score.strengths[:2])}...")
    print(f"Weaknesses: {', '.join(result4.score.weaknesses[:2])}...")
    print(f"Recommendations: {', '.join(result4.score.recommendations[:2])}...")
    print()
    
    # Demo 5: Integration workflow test
    print("🔄 Demo 5: Integration Workflow Test")
    print("-" * 40)
    
    workflow_output = {
        "status": "success",
        "workflow": "research_analysis",
        "steps": [
            "web_search: rmay atawia publications",
            "document_analysis: content analysis",
            "data_formatting: report generation"
        ],
        "tools_used": ["web_content_fetcher", "document_analyzer", "data_formatter"],
        "result": "Research analysis workflow completed successfully"
    }
    
    result5 = test_scoring_service.score_test_output(
        "research_workflow_integration",
        workflow_output,
        3.2,  # 3.2 seconds execution time
        "passed"
    )
    
    print(f"Test: {result5.test_name}")
    print(f"Score: {result5.score.score}/10")
    print(f"Category: {result5.score.category}")
    print(f"Reasoning: {result5.score.reasoning}")
    print(f"Strengths: {', '.join(result5.score.strengths[:3])}...")
    print()
    
    # Generate comprehensive report
    print("📊 Generating Comprehensive Report...")
    print("-" * 40)
    
    all_results = [result1, result2, result3, result4, result5]
    report = test_scoring_service.generate_test_report(all_results)
    
    summary = report.get("summary", {})
    print(f"Total Tests: {summary.get('total_tests', 0)}")
    print(f"Success Rate: {summary.get('success_rate', 0)}%")
    print(f"Average Score: {summary.get('average_score', 0):.2f}/10")
    print(f"Average Execution Time: {summary.get('average_execution_time', 0):.3f}s")
    
    # Category breakdown
    print("\n🏷️ Category Performance:")
    categories = report.get("categories", {})
    for category, data in categories.items():
        print(f"  {category.title()}: {data.get('avg_score', 0):.1f}/10 ({data.get('count', 0)} tests)")
    
    print("\n🎯 Scoring System Summary:")
    print("✅ The AI judge evaluates tests across multiple criteria:")
    print("   - Functionality (3.0 points): Tool execution success and output quality")
    print("   - Security (2.0 points): Input validation and security measures")
    print("   - Error Handling (2.0 points): Error message quality and categorization")
    print("   - Performance (1.5 points): Execution time and efficiency")
    print("   - Documentation (1.5 points): Output structure and metadata")
    print("\n💡 Each test gets a detailed score with strengths, weaknesses, and recommendations!")


if __name__ == "__main__":
    demo_scoring_system()

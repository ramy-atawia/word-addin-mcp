"""
Integration tests for Patent Search Tool with real-world test cases.

This test suite validates the patent search functionality with the three
validated test cases:
1. 5G handover using AI
2. 5G dynamic spectrum sharing  
3. Financial AI auditing

Tests cover:
- Claims text inclusion
- Report structure validation
- Data quality verification
- Professional report standards compliance
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import httpx


class TestPatentSearchIntegration:
    """Integration tests for Patent Search Tool with real test cases."""
    
    @pytest.fixture
    def test_queries(self):
        """Test queries validated in production."""
        return [
            {
                "query": "5G handover using AI",
                "expected_keywords": ["5G", "handover", "AI", "artificial intelligence"],
                "expected_risk_levels": ["HIGH", "MEDIUM", "LOW"],
                "min_patents": 5,
                "max_patents": 50
            },
            {
                "query": "5G dynamic spectrum sharing",
                "expected_keywords": ["5G", "dynamic", "spectrum", "sharing", "DSS"],
                "expected_risk_levels": ["HIGH", "MEDIUM", "LOW"],
                "min_patents": 5,
                "max_patents": 50
            },
            {
                "query": "Financial AI auditing",
                "expected_keywords": ["financial", "AI", "auditing", "artificial intelligence"],
                "expected_risk_levels": ["HIGH", "MEDIUM", "LOW"],
                "min_patents": 5,
                "max_patents": 50
            }
        ]
    
    @pytest.fixture
    def mock_patentsview_response(self):
        """Mock PatentsView API response with realistic data."""
        return {
            "patents": [
                {
                    "patent_id": "12345678",
                    "patent_title": "Test Patent Title",
                    "patent_abstract": "This is a test patent abstract that describes the invention in detail.",
                    "patent_date": "2024-01-15",
                    "inventors": [{"inventor_name_first": "John", "inventor_name_last": "Doe"}],
                    "assignees": [{"assignee_organization": "Test Company Inc."}],
                    "cpc_subsections": ["H04W36/00"],
                    "uspc_mainclasses": ["455/436"]
                }
            ]
        }
    
    @pytest.fixture
    def mock_claims_response(self):
        """Mock PatentsView claims API response."""
        return {
            "patents": [
                {
                    "patent_id": "12345678",
                    "claims": [
                        {
                            "claim_sequence": 1,
                            "claim_number": "1",
                            "claim_text": "A method for performing handover in a wireless communication system comprising: receiving measurement reports from user equipment; analyzing the measurement reports using artificial intelligence; and determining handover parameters based on the analysis.",
                            "claim_dependent": False
                        },
                        {
                            "claim_sequence": 2,
                            "claim_number": "2", 
                            "claim_text": "The method of claim 1, wherein the artificial intelligence comprises a neural network.",
                            "claim_dependent": True
                        }
                    ]
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_patent_search_tool_execution(self, test_client: TestClient, test_queries):
        """Test patent search tool execution with real queries."""
        
        for test_case in test_queries:
            query = test_case["query"]
            
            # Execute patent search
            response = test_client.post(
                "/api/v1/mcp/tools/prior_art_search_tool/execute",
                json={"parameters": {"query": query}}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            
            # Parse the markdown result
            result_text = data["result"]
            assert isinstance(result_text, str)
            assert len(result_text) > 100  # Should be substantial report
            
            # Verify report structure
            self._validate_report_structure(result_text, test_case)
    
    def _validate_report_structure(self, report_text: str, test_case: dict):
        """Validate the structure and content of the patent search report."""
        
        # Check for required sections
        required_sections = [
            "# Prior Art Search Report:",
            "## Executive Summary",
            "## Search Methodology",
            "## Invention Analysis",
            "## Prior Art References",
            "## Risk Analysis",
            "## Conclusions and Recommendations"
        ]
        
        for section in required_sections:
            assert section in report_text, f"Missing required section: {section}"
        
        # Check for query-specific content
        query = test_case["query"]
        assert query in report_text, f"Query '{query}' not found in report"
        
        # Check for expected keywords
        for keyword in test_case["expected_keywords"]:
            assert keyword.lower() in report_text.lower(), f"Expected keyword '{keyword}' not found"
        
        # Check for risk level analysis
        for risk_level in test_case["expected_risk_levels"]:
            assert risk_level in report_text, f"Risk level '{risk_level}' not found in analysis"
        
        # Check for claims text inclusion (critical improvement)
        assert "Key Claims:" in report_text, "Claims text section missing"
        assert "Claim 1:" in report_text, "Individual claims not included"
        
        # Check for hybrid analysis elements
        assert "Innovation Summary:" in report_text, "Innovation summaries missing"
        assert "Detailed Claim Analysis" in report_text, "Detailed analysis section missing"
        assert "Claim-by-Claim Analysis:" in report_text, "Claim-by-claim analysis missing"
        
        # Check for professional elements
        assert "Patentability Assessment:" in report_text, "Patentability assessment missing"
        assert "35 USC" in report_text, "Legal framework missing"
        assert "Freedom to Operate" in report_text, "FTO analysis missing"
        
        # Check for patent count validation
        assert "Total Patents:" in report_text, "Patent count not displayed"
        
        # Check for search methodology
        assert "Search Queries Used" in report_text, "Search methodology missing"
        assert "→" in report_text, "Query result counts not displayed"

    @pytest.mark.asyncio
    async def test_claims_text_inclusion(self, test_client: TestClient):
        """Test that claims text is properly included in reports."""
        
        # Use a simple query for focused testing
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G handover using AI"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Verify claims text is included
        claims_indicators = [
            "Key Claims:",
            "Claim 1:",
            "Claim 2:",
            "A method for",
            "The method of claim"
        ]
        
        found_claims = sum(1 for indicator in claims_indicators if indicator in result_text)
        assert found_claims >= 3, f"Claims text not properly included. Found {found_claims} indicators."
        
        # Verify claims are not just counts
        assert "Claims Count:" in result_text, "Claims count should be included"
        assert "claim_text" not in result_text, "Raw claim_text field should not appear in report"

    @pytest.mark.asyncio
    async def test_report_quality_standards(self, test_client: TestClient):
        """Test that reports meet professional quality standards."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G dynamic spectrum sharing"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check for professional report elements
        professional_elements = [
            "Executive Summary",
            "Risk level:",
            "HIGH RISK:",
            "MEDIUM RISK:", 
            "LOW RISK:",
            "Immediate actions needed",
            "Areas for further investigation",
            "Strategic considerations"
        ]
        
        for element in professional_elements:
            assert element in result_text, f"Professional element '{element}' missing"
        
        # Check for proper patent information
        patent_info_elements = [
            "Patent ID:",
            "Title:",
            "Date:",
            "Assignee:",
            "Abstract:",
            "Relevance:",
            "Risk Assessment:"
        ]
        
        for element in patent_info_elements:
            assert element in result_text, f"Patent info element '{element}' missing"

    @pytest.mark.asyncio
    async def test_search_query_performance_tracking(self, test_client: TestClient):
        """Test that search query performance is tracked and displayed."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "Financial AI auditing"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check for query performance tracking
        assert "Search Queries Used (with result counts):" in result_text
        assert "→" in result_text  # Arrow indicating query → count format
        assert "patents" in result_text  # Should show "X patents" format
        
        # Verify multiple queries were used
        query_lines = [line for line in result_text.split('\n') if '→' in line and 'patents' in line]
        assert len(query_lines) >= 3, f"Expected multiple query lines, got {len(query_lines)}"

    @pytest.mark.asyncio
    async def test_risk_analysis_quality(self, test_client: TestClient):
        """Test that risk analysis provides meaningful insights."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G handover using AI"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check for comprehensive risk analysis
        risk_section = self._extract_section(result_text, "## Risk Analysis")
        assert risk_section is not None, "Risk Analysis section not found"
        
        # Verify risk categories are present
        assert "HIGH RISK:" in risk_section
        assert "MEDIUM RISK:" in risk_section
        assert "LOW RISK:" in risk_section
        
        # Check for specific risk assessments
        assert "patents" in risk_section.lower()  # Should mention specific patents
        assert "conflict" in risk_section.lower() or "overlap" in risk_section.lower()

    @pytest.mark.asyncio
    async def test_recommendations_quality(self, test_client: TestClient):
        """Test that recommendations are actionable and specific."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G dynamic spectrum sharing"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check for recommendations section
        recommendations_section = self._extract_section(result_text, "## Recommendations")
        assert recommendations_section is not None, "Recommendations section not found"
        
        # Verify actionable recommendations
        action_indicators = [
            "Immediate actions",
            "Areas for further investigation", 
            "Strategic considerations"
        ]
        
        for indicator in action_indicators:
            assert indicator in recommendations_section, f"Missing recommendation type: {indicator}"
        
        # Check for specific, actionable language
        assert len(recommendations_section) > 200, "Recommendations should be substantial"

    def _extract_section(self, text: str, section_header: str) -> str:
        """Extract a specific section from the report text."""
        lines = text.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if section_header in line:
                start_idx = i
            elif start_idx is not None and line.startswith('##') and line != section_header:
                end_idx = i
                break
        
        if start_idx is not None:
            end_idx = end_idx if end_idx is not None else len(lines)
            return '\n'.join(lines[start_idx:end_idx])
        
        return None

    @pytest.mark.asyncio
    async def test_error_handling(self, test_client: TestClient):
        """Test error handling for invalid inputs."""
        
        # Test empty query
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": ""}}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
        
        # Test very short query
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "AI"}}
        )
        
        # Should still work but may have limited results
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_report_consistency_across_queries(self, test_client: TestClient, test_queries):
        """Test that report structure is consistent across different queries."""
        
        reports = []
        
        # Generate reports for all test queries
        for test_case in test_queries:
            response = test_client.post(
                "/api/v1/mcp/tools/prior_art_search_tool/execute",
                json={"parameters": {"query": test_case["query"]}}
            )
            
            assert response.status_code == 200
            data = response.json()
            reports.append(data["result"])
        
        # Verify all reports have consistent structure
        for i, report in enumerate(reports):
            query = test_queries[i]["query"]
            
            # Check for consistent sections
            required_sections = [
                "# Prior Art Search Report:",
                "## Executive Summary",
                "## Search Results",
                "## Key Patents", 
                "## Risk Analysis",
                "## Recommendations"
            ]
            
            for section in required_sections:
                assert section in report, f"Report for '{query}' missing section: {section}"

    @pytest.mark.asyncio
    async def test_claims_analysis_depth(self, test_client: TestClient):
        """Test that claims analysis provides sufficient depth."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G handover using AI"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check for detailed claims analysis
        claims_section = self._extract_section(result_text, "## Key Patents")
        assert claims_section is not None, "Key Patents section not found"
        
        # Verify claims are analyzed, not just listed
        assert "Claim 1:" in claims_section
        assert "A method" in claims_section or "A system" in claims_section or "An apparatus" in claims_section
        
        # Check for claim dependency information
        assert "claim" in claims_section.lower()  # Should reference claims multiple times
        
        # Verify claims are integrated into risk assessment
        risk_section = self._extract_section(result_text, "## Risk Analysis")
        assert "claim" in risk_section.lower() or "patent" in risk_section.lower()


class TestPatentSearchDataQuality:
    """Test data quality and completeness of patent search results."""
    
    @pytest.mark.asyncio
    async def test_patent_metadata_completeness(self, test_client: TestClient):
        """Test that patent metadata is complete and properly formatted."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G dynamic spectrum sharing"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Extract patent information from report
        patent_sections = self._extract_patent_sections(result_text)
        
        for patent_section in patent_sections:
            # Check for required metadata fields
            required_fields = [
                "Patent ID:",
                "Title:",
                "Date:",
                "Assignee:",
                "Abstract:",
                "Claims Count:",
                "Key Claims:",
                "Relevance:",
                "Risk Assessment:"
            ]
            
            for field in required_fields:
                assert field in patent_section, f"Missing field {field} in patent section"
    
    def _extract_patent_sections(self, report_text: str) -> list:
        """Extract individual patent sections from the report."""
        lines = report_text.split('\n')
        patent_sections = []
        current_section = []
        in_patent_section = False
        
        for line in lines:
            if line.startswith('###') and ('Patent' in line or '1.' in line or '2.' in line):
                if current_section:
                    patent_sections.append('\n'.join(current_section))
                current_section = [line]
                in_patent_section = True
            elif in_patent_section and (line.startswith('###') or line.startswith('##')):
                if current_section:
                    patent_sections.append('\n'.join(current_section))
                current_section = []
                in_patent_section = False
            elif in_patent_section:
                current_section.append(line)
        
        if current_section:
            patent_sections.append('\n'.join(current_section))
        
        return patent_sections

    @pytest.mark.asyncio
    async def test_abstract_completeness(self, test_client: TestClient):
        """Test that abstracts are complete, not truncated."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "Financial AI auditing"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check that abstracts are not truncated
        assert "..." not in result_text, "Abstracts should not be truncated with '...'"
        
        # Check for substantial abstract content
        abstract_sections = [line for line in result_text.split('\n') if 'Abstract:' in line]
        for abstract_line in abstract_sections:
            # Abstract should be more than just the label
            abstract_content = abstract_line.replace('Abstract:', '').strip()
            assert len(abstract_content) > 50, f"Abstract too short: {abstract_content}"

    @pytest.mark.asyncio
    async def test_claims_text_quality(self, test_client: TestClient):
        """Test that claims text is properly formatted and meaningful."""
        
        response = test_client.post(
            "/api/v1/mcp/tools/prior_art_search_tool/execute",
            json={"parameters": {"query": "5G handover using AI"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]
        
        # Check for properly formatted claims
        claim_lines = [line for line in result_text.split('\n') if line.strip().startswith('Claim ')]
        
        assert len(claim_lines) > 0, "No properly formatted claims found"
        
        for claim_line in claim_lines:
            # Claims should have meaningful content
            assert len(claim_line) > 20, f"Claim too short: {claim_line}"
            assert ":" in claim_line, f"Claim should have colon separator: {claim_line}"
            
            # Claims should contain technical language
            technical_terms = ["method", "system", "apparatus", "device", "process", "comprising"]
            has_technical_term = any(term in claim_line.lower() for term in technical_terms)
            assert has_technical_term, f"Claim lacks technical language: {claim_line}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

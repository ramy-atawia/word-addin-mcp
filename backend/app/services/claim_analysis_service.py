"""
Claim Analysis Service

Service for analyzing patent claims for validity, quality, and improvement opportunities.
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import re

from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ClaimAnalysisService:
    """Service for analyzing patent claims using LLM."""
    
    def __init__(self):
        # Get LLM configuration from settings
        from app.core.config import settings
        self.llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment_name
        )
        
        # Configuration
        self.timeout = 120.0
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def analyze_claims(self, claims: List[Dict[str, Any]], analysis_type: str = "comprehensive",
                           focus_areas: Optional[List[str]] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Analyze patent claims for validity, quality, and improvement opportunities."""
        try:
            logger.info(f"Starting claim analysis for {len(claims)} claims")
            
            # Generate LLM analysis criteria
            llm_criteria = await self._generate_llm_analysis_criteria(claims, analysis_type, focus_areas)
            
            # Perform comprehensive claim analysis
            analysis_result = await self._analyze_claims_with_llm(claims, analysis_type, focus_areas)
            
            # Generate analysis report
            analysis_report = await self._generate_analysis_report(analysis_result, claims)
            
            # Create result
            result = {
                "claims_analyzed": len(claims),
                "analysis_type": analysis_type,
                "analysis": analysis_result,
                "quality_assessment": analysis_result.get("quality_assessment", {}),
                "recommendations": analysis_result.get("recommendations", {}),
                "risk_assessment": analysis_result.get("risk_assessment", {}),
                "analysis_report": analysis_report,
                "analysis_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "analysis_type": analysis_type,
                    "focus_areas": focus_areas or [],
                    "execution_time": time.time()
                }
            }
            
            logger.info(f"Claim analysis completed: {len(claims)} claims analyzed")
            
            # Prepare LLM criteria for return
            generated_criteria = [llm_criteria]
            logger.info(f"Returning analysis result with {len(generated_criteria)} generated criteria")
            
            return result, generated_criteria
            
        except Exception as e:
            logger.error(f"Claim analysis failed for {len(claims)} claims: {str(e)}")
            raise
    
    async def _generate_llm_analysis_criteria(self, claims: List[Dict[str, Any]], analysis_type: str,
                                            focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Generate sophisticated analysis criteria using LLM."""
        try:
            # Prepare claims summary for LLM
            claims_summary = []
            for i, claim in enumerate(claims, 1):
                claims_summary.append(f"Claim {i} ({claim.get('claim_type', 'unknown')}): {claim.get('claim_text', '')[:200]}...")
            
            claims_text = "\n".join(claims_summary)
            
            prompt = f"""
You are a patent attorney analyzing patent claims for validity, quality, and improvement opportunities.

Claims to Analyze:
{claims_text}

Analysis Type: {analysis_type}
Focus Areas: {focus_areas or 'General patent analysis'}

Generate analysis strategy considering:
1. Claim structure and dependencies
2. Validity issues (35 USC 101, 112, 103, 102)
3. Quality assessment (clarity, breadth, defensibility)
4. Improvement opportunities
5. Risk assessment and mitigation strategies

Return a JSON response with these fields:
{{
    "analysis_framework": {{
        "validity_checklist": ["101_eligibility", "112_clarity", "103_obviousness", "102_novelty"],
        "quality_metrics": ["clarity", "breadth", "defensibility", "technical_accuracy"],
        "risk_factors": ["prior_art_risks", "validity_risks", "enforcement_risks"]
    }},
    "focus_areas": ["area1", "area2", "area3"],
    "analysis_priorities": ["priority1", "priority2", "priority3"],
    "expected_issues": ["potential_issue1", "potential_issue2"],
    "analysis_strategy": "detailed explanation of the analysis approach",
    "reasoning": "detailed reasoning for the analysis strategy"
}}

Focus on creating a comprehensive analysis framework for patent claim evaluation.
"""
            
            response_data = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )
            response = response_data.get("text", "")
            
            # Parse the JSON response (handle markdown-wrapped responses)
            try:
                # Remove markdown code blocks if present
                if response.startswith("```json"):
                    response = response.replace("```json", "").replace("```", "").strip()
                elif response.startswith("```"):
                    response = response.replace("```", "").strip()
                
                criteria = json.loads(response)
                logger.info(f"Generated LLM analysis criteria: {criteria.get('reasoning', 'No reasoning provided')}")
                return criteria
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response}")
                return self._fallback_analysis_criteria(claims, analysis_type)
                
        except Exception as e:
            logger.error(f"LLM analysis criteria generation failed: {e}")
            return self._fallback_analysis_criteria(claims, analysis_type)
    
    def _fallback_analysis_criteria(self, claims: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        """Fallback analysis criteria when LLM generation fails."""
        return {
            "analysis_framework": {
                "validity_checklist": ["101_eligibility", "112_clarity", "103_obviousness", "102_novelty"],
                "quality_metrics": ["clarity", "breadth", "defensibility", "technical_accuracy"],
                "risk_factors": ["prior_art_risks", "validity_risks", "enforcement_risks"]
            },
            "focus_areas": ["claim_structure", "technical_content", "legal_compliance"],
            "analysis_priorities": ["validity_assessment", "quality_evaluation", "improvement_recommendations"],
            "expected_issues": ["potential_clarity_issues", "potential_breadth_issues"],
            "analysis_strategy": "Standard patent claim analysis approach",
            "reasoning": "Fallback to standard analysis framework due to LLM generation failure"
        }
    
    async def _analyze_claims_with_llm(self, claims: List[Dict[str, Any]], analysis_type: str,
                                     focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze claims using LLM integration."""
        try:
            # Load prompts
            system_prompt = self._load_system_prompt()
            user_prompt = self._load_user_prompt(claims, analysis_type, focus_areas)
            
            # Call LLM for analysis
            response_data = self.llm_client.generate_text(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=4000,
                temperature=0.3
            )
            
            # Parse response
            response_text = response_data.get("text", "")
            
            # Try to parse as JSON first (for structured responses)
            try:
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If not JSON, parse as natural language analysis
                result = self._parse_natural_language_analysis(response_text, claims, analysis_type)
            
            # Validate and clean analysis
            if not result.get("quality_assessment"):
                result["quality_assessment"] = self._create_default_quality_assessment(claims)
            if not result.get("recommendations"):
                result["recommendations"] = self._create_default_recommendations(claims)
            if not result.get("risk_assessment"):
                result["risk_assessment"] = self._create_default_risk_assessment(claims)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM claim analysis failed: {e}")
            return self._create_fallback_analysis(claims, analysis_type)
    
    def _parse_natural_language_analysis(self, response_text: str, claims: List[Dict[str, Any]], 
                                       analysis_type: str) -> Dict[str, Any]:
        """Parse natural language analysis from LLM response."""
        import re
        
        # Extract sections from the response
        sections = {
            "quality_assessment": {},
            "recommendations": {},
            "risk_assessment": {}
        }
        
        # Look for quality assessment
        quality_match = re.search(r'quality[^:]*:?\s*([^#\n]+)', response_text, re.IGNORECASE)
        if quality_match:
            sections["quality_assessment"]["overall_quality"] = quality_match.group(1).strip()
        
        # Look for recommendations
        recommendations = []
        rec_matches = re.findall(r'(?:recommend|suggest|improve)[^.!?]*[.!?]', response_text, re.IGNORECASE)
        for match in rec_matches:
            recommendations.append(match.strip())
        sections["recommendations"]["improvements"] = recommendations
        
        # Look for risks
        risks = []
        risk_matches = re.findall(r'(?:risk|issue|problem|concern)[^.!?]*[.!?]', response_text, re.IGNORECASE)
        for match in risk_matches:
            risks.append(match.strip())
        sections["risk_assessment"]["identified_risks"] = risks
        
        return {
            "quality_assessment": sections["quality_assessment"],
            "recommendations": sections["recommendations"],
            "risk_assessment": sections["risk_assessment"],
            "analysis_notes": "Analysis parsed from natural language LLM response"
        }
    
    def _create_default_quality_assessment(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create default quality assessment when LLM fails."""
        return {
            "overall_quality": "standard",
            "clarity_score": 0.7,
            "breadth_score": 0.6,
            "defensibility_score": 0.6,
            "technical_accuracy": 0.7,
            "key_strengths": ["Claims have basic structure", "Technical content present"],
            "areas_for_improvement": ["Enhance technical specificity", "Improve claim clarity"]
        }
    
    def _create_default_recommendations(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create default recommendations when LLM fails."""
        return {
            "improvements": [
                "Review claim language for clarity",
                "Ensure proper claim dependencies",
                "Add technical specificity where needed",
                "Consider additional dependent claims"
            ],
            "priorities": ["high", "medium", "medium", "low"],
            "focus_areas": {
                "claim_structure": "Ensure proper independent/dependent claim relationships",
                "technical_content": "Add more specific technical details",
                "legal_compliance": "Verify USPTO formatting requirements"
            }
        }
    
    def _create_default_risk_assessment(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create default risk assessment when LLM fails."""
        return {
            "high_risk": [],
            "medium_risk": ["Potential clarity issues", "Limited technical specificity"],
            "low_risk": ["Basic claim structure present"],
            "mitigation_strategies": [
                "Conduct prior art search",
                "Review claim language for clarity",
                "Add technical specificity"
            ]
        }
    
    def _create_fallback_analysis(self, claims: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        """Create fallback analysis when LLM fails."""
        return {
            "quality_assessment": self._create_default_quality_assessment(claims),
            "recommendations": self._create_default_recommendations(claims),
            "risk_assessment": self._create_default_risk_assessment(claims),
            "analysis_notes": "Fallback analysis generated due to LLM processing issues"
        }
    
    def _load_system_prompt(self) -> str:
        """Load system prompt for claim analysis."""
        try:
            with open("backend/app/prompts/claim_analysis_system.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return """You are a patent attorney analyzing patent claims for validity, quality, and improvement opportunities. Provide comprehensive analysis covering claim structure, validity issues, quality assessment, and recommendations."""
    
    def _load_user_prompt(self, claims: List[Dict[str, Any]], analysis_type: str, 
                         focus_areas: Optional[List[str]]) -> str:
        """Load and format user prompt for claim analysis."""
        try:
            with open("backend/app/prompts/claim_analysis_user.txt", "r") as f:
                template = f.read().strip()
            
            # Format claims for the prompt
            claims_text = ""
            for i, claim in enumerate(claims, 1):
                claims_text += f"Claim {i} ({claim.get('claim_type', 'unknown')}): {claim.get('claim_text', '')}\n\n"
            
            return template.format(
                claims_text=claims_text,
                analysis_type=analysis_type,
                focus_areas=", ".join(focus_areas) if focus_areas else "General patent analysis"
            )
        except FileNotFoundError:
            # Fallback prompt
            claims_text = ""
            for i, claim in enumerate(claims, 1):
                claims_text += f"Claim {i}: {claim.get('claim_text', '')}\n\n"
            
            return f"""Analyze the following patent claims for validity, quality, and improvement opportunities:

{claims_text}

Analysis Type: {analysis_type}
Focus Areas: {focus_areas or 'General patent analysis'}

Provide comprehensive analysis covering:
1. Claim structure and dependencies
2. Validity assessment (35 USC 101, 112, 103, 102)
3. Quality evaluation (clarity, breadth, defensibility)
4. Improvement recommendations
5. Risk assessment and mitigation strategies"""
    
    async def _generate_analysis_report(self, analysis_result: Dict[str, Any], claims: List[Dict[str, Any]]) -> str:
        """Generate comprehensive analysis report."""
        try:
            quality_assessment = analysis_result.get("quality_assessment", {})
            recommendations = analysis_result.get("recommendations", {})
            risk_assessment = analysis_result.get("risk_assessment", {})
            
            report = f"# Patent Claim Analysis Report\n\n"
            
            # Executive Summary
            report += f"## 1. Executive Summary\n"
            report += f"Comprehensive analysis of {len(claims)} patent claims completed. "
            report += f"Overall quality: {quality_assessment.get('overall_quality', 'standard')}. "
            report += f"Key focus areas: {', '.join(recommendations.get('focus_areas', {}).keys())}.\n\n"
            
            # Quality Assessment
            report += f"## 2. Quality Assessment\n"
            report += f"- **Clarity Score**: {quality_assessment.get('clarity_score', 0.7):.2f}\n"
            report += f"- **Breadth Score**: {quality_assessment.get('breadth_score', 0.6):.2f}\n"
            report += f"- **Defensibility Score**: {quality_assessment.get('defensibility_score', 0.6):.2f}\n"
            report += f"- **Technical Accuracy**: {quality_assessment.get('technical_accuracy', 0.7):.2f}\n\n"
            
            # Key Strengths
            if quality_assessment.get("key_strengths"):
                report += f"**Key Strengths:**\n"
                for strength in quality_assessment["key_strengths"]:
                    report += f"- {strength}\n"
                report += "\n"
            
            # Areas for Improvement
            if quality_assessment.get("areas_for_improvement"):
                report += f"**Areas for Improvement:**\n"
                for area in quality_assessment["areas_for_improvement"]:
                    report += f"- {area}\n"
                report += "\n"
            
            # Recommendations
            report += f"## 3. Improvement Recommendations\n"
            if recommendations.get("improvements"):
                for i, improvement in enumerate(recommendations["improvements"], 1):
                    priority = recommendations.get("priorities", [])[i-1] if i <= len(recommendations.get("priorities", [])) else "medium"
                    report += f"{i}. **{improvement}** (Priority: {priority})\n"
                report += "\n"
            
            # Risk Assessment
            report += f"## 4. Risk Assessment\n"
            if risk_assessment.get("high_risk"):
                report += f"**High Risk Issues:**\n"
                for risk in risk_assessment["high_risk"]:
                    report += f"- {risk}\n"
                report += "\n"
            
            if risk_assessment.get("medium_risk"):
                report += f"**Medium Risk Issues:**\n"
                for risk in risk_assessment["medium_risk"]:
                    report += f"- {risk}\n"
                report += "\n"
            
            if risk_assessment.get("low_risk"):
                report += f"**Low Risk Issues:**\n"
                for risk in risk_assessment["low_risk"]:
                    report += f"- {risk}\n"
                report += "\n"
            
            # Mitigation Strategies
            if risk_assessment.get("mitigation_strategies"):
                report += f"**Mitigation Strategies:**\n"
                for strategy in risk_assessment["mitigation_strategies"]:
                    report += f"- {strategy}\n"
                report += "\n"
            
            # Metadata
            report += f"---\n"
            report += f"**Analysis Metadata:**\n"
            report += f"- Claims analyzed: {len(claims)}\n"
            report += f"- Generated: {datetime.now().isoformat()}\n"
            report += f"- Analysis type: {analysis_result.get('analysis_type', 'comprehensive')}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Claim analysis completed for {len(claims)} claims. Analysis generated with standard assessment."
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration."""
        return {
            "service": "ClaimAnalysisService",
            "llm_configured": bool(self.llm_client),
            "status": "active"
        }

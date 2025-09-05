#!/usr/bin/env python3
"""
Final Comprehensive Test Suite for Legal Tools

Tests all three legal tools with 100+ test cases to ensure they're all working correctly.
"""

import asyncio
import json
import time
import requests
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    tool: str
    status: str  # "PASS", "FAIL", "ERROR"
    execution_time: float
    error_message: str = ""
    response_data: Dict[str, Any] = None

class LegalToolsFinalTester:
    """Final comprehensive tester for legal tools."""
    
    def __init__(self, base_url: str = "https://localhost:9000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for local testing
        self.test_results: List[TestResult] = []
        
        # Test data sets - expanded for 100+ tests
        self.prior_art_queries = [
            "5G wireless communication", "machine learning algorithms", "blockchain technology",
            "artificial intelligence", "quantum computing", "autonomous vehicles", "renewable energy systems",
            "biomedical devices", "cybersecurity methods", "cloud computing architecture", "IoT sensor networks",
            "robotic process automation", "augmented reality systems", "natural language processing",
            "computer vision algorithms", "distributed ledger technology", "edge computing systems",
            "neural network architectures", "data encryption methods", "wireless sensor networks",
            "smart grid technology", "digital twin systems", "predictive analytics", "real-time processing",
            "federated learning", "edge AI", "quantum machine learning", "neuromorphic computing",
            "swarm intelligence", "genetic algorithms", "deep reinforcement learning", "transfer learning",
            "adversarial networks", "transformer models", "attention mechanisms", "self-supervised learning",
            "few-shot learning", "meta-learning", "continual learning", "online learning",
            "distributed training", "model compression", "pruning techniques", "quantization methods",
            "knowledge distillation", "neural architecture search", "automated machine learning",
            "explainable AI", "interpretable models", "fairness in AI", "bias detection",
            "adversarial robustness", "privacy-preserving ML", "differential privacy", "homomorphic encryption",
            "secure multi-party computation", "federated analytics", "synthetic data generation",
            "data augmentation", "active learning", "semi-supervised learning", "unsupervised learning",
            "clustering algorithms", "dimensionality reduction", "feature selection", "ensemble methods",
            "gradient boosting", "random forests", "support vector machines", "neural networks",
            "convolutional networks", "recurrent networks", "long short-term memory", "gated recurrent units",
            "attention networks", "transformer architectures", "BERT models", "GPT models",
            "vision transformers", "generative adversarial networks", "variational autoencoders",
            "flow-based models", "diffusion models", "normalizing flows", "energy-based models",
            "contrastive learning", "self-supervised representation learning", "multimodal learning",
            "cross-modal retrieval", "visual question answering", "image captioning", "text-to-image generation",
            "speech recognition", "speech synthesis", "voice conversion", "speaker identification",
            "emotion recognition", "sentiment analysis", "text classification", "named entity recognition",
            "relation extraction", "question answering", "machine translation", "text summarization",
            "dialogue systems", "chatbots", "conversational AI", "recommendation systems",
            "collaborative filtering", "content-based filtering", "hybrid recommendation", "matrix factorization"
        ]
        
        self.invention_descriptions = [
            "A wireless communication system that uses machine learning algorithms to optimize signal transmission and reduce interference in 5G networks",
            "A blockchain-based voting system that ensures transparency and prevents fraud in electronic elections",
            "An autonomous vehicle navigation system that uses computer vision and AI to navigate complex traffic scenarios",
            "A renewable energy management system that optimizes power distribution using predictive analytics",
            "A biomedical device that monitors patient vital signs and provides real-time health alerts",
            "A cybersecurity system that detects and prevents advanced persistent threats using behavioral analysis",
            "A cloud computing platform that automatically scales resources based on demand patterns",
            "An IoT sensor network that monitors environmental conditions and provides predictive maintenance",
            "A robotic process automation system that streamlines business workflows using AI",
            "An augmented reality system that overlays digital information on physical objects in real-time",
            "A natural language processing system that extracts insights from unstructured text data",
            "A computer vision algorithm that identifies objects in images with high accuracy",
            "A distributed ledger system that ensures data integrity across multiple nodes",
            "An edge computing system that processes data locally to reduce latency",
            "A neural network architecture that improves learning efficiency and reduces computational requirements",
            "A data encryption method that provides enhanced security while maintaining performance",
            "A wireless sensor network that operates on low power and provides long-range communication",
            "A quantum computing algorithm that solves optimization problems more efficiently",
            "A machine learning system that adapts to new data patterns without retraining",
            "An AI-powered recommendation system that personalizes content based on user behavior",
            "A smart grid system that optimizes energy distribution using real-time demand forecasting",
            "A digital twin platform that creates virtual replicas of physical systems for simulation",
            "A predictive analytics engine that forecasts equipment failures in industrial settings",
            "A real-time processing system that analyzes streaming data with sub-millisecond latency",
            "A federated learning framework that trains models across distributed data sources",
            "An edge AI system that performs inference on resource-constrained devices",
            "A quantum machine learning algorithm that leverages quantum computing for optimization",
            "A neuromorphic computing system that mimics biological neural networks",
            "A swarm intelligence algorithm that coordinates multiple autonomous agents",
            "A genetic algorithm that evolves solutions to complex optimization problems",
            "A deep reinforcement learning system that learns optimal strategies through trial and error",
            "A transfer learning framework that adapts pre-trained models to new domains",
            "An adversarial network that generates synthetic data for training purposes",
            "A transformer model that processes sequential data with attention mechanisms",
            "A self-supervised learning system that learns representations without labeled data",
            "A few-shot learning algorithm that adapts to new tasks with minimal examples",
            "A meta-learning system that learns how to learn across multiple tasks",
            "A continual learning framework that adapts to new data without forgetting previous knowledge",
            "An online learning system that updates models incrementally with new data",
            "A distributed training system that scales machine learning across multiple machines",
            "A model compression technique that reduces neural network size without significant performance loss",
            "A pruning algorithm that removes unnecessary connections from neural networks",
            "A quantization method that reduces precision of neural network parameters",
            "A knowledge distillation system that transfers knowledge from large to small models",
            "A neural architecture search algorithm that automatically designs optimal network structures",
            "An automated machine learning platform that builds models without human intervention",
            "An explainable AI system that provides interpretable explanations for model decisions",
            "A fairness-aware machine learning system that detects and mitigates bias in models",
            "An adversarial robustness system that protects models against malicious attacks",
            "A privacy-preserving machine learning framework that protects sensitive data",
            "A differential privacy system that provides mathematical guarantees of privacy",
            "A homomorphic encryption scheme that enables computation on encrypted data",
            "A secure multi-party computation protocol that allows joint computation without revealing inputs",
            "A federated analytics system that analyzes data across multiple organizations",
            "A synthetic data generation system that creates realistic artificial datasets",
            "A data augmentation technique that increases dataset diversity through transformations",
            "An active learning system that intelligently selects data points for labeling",
            "A semi-supervised learning algorithm that leverages both labeled and unlabeled data",
            "An unsupervised learning system that discovers patterns in data without labels",
            "A clustering algorithm that groups similar data points together",
            "A dimensionality reduction technique that reduces data complexity while preserving information",
            "A feature selection algorithm that identifies the most relevant data attributes",
            "An ensemble method that combines multiple models for improved performance",
            "A gradient boosting system that builds models sequentially to correct errors",
            "A random forest algorithm that combines multiple decision trees for robust predictions",
            "A support vector machine that finds optimal decision boundaries in high-dimensional space",
            "A neural network that learns complex patterns through interconnected nodes",
            "A convolutional network that processes spatial data like images and videos",
            "A recurrent network that handles sequential data with memory capabilities",
            "A long short-term memory network that remembers information over long sequences",
            "A gated recurrent unit that efficiently processes sequential data with gating mechanisms",
            "An attention network that focuses on relevant parts of input data",
            "A transformer architecture that processes sequences with self-attention mechanisms",
            "A BERT model that understands bidirectional context in natural language",
            "A GPT model that generates human-like text through autoregressive prediction",
            "A vision transformer that applies attention mechanisms to computer vision tasks",
            "A generative adversarial network that creates realistic synthetic data",
            "A variational autoencoder that learns compressed representations of data",
            "A flow-based model that transforms simple distributions into complex ones",
            "A diffusion model that generates data through iterative denoising processes",
            "A normalizing flow that enables exact likelihood computation for generative models",
            "An energy-based model that learns probability distributions through energy functions",
            "A contrastive learning system that learns representations by comparing similar and dissimilar examples",
            "A self-supervised representation learning framework that learns useful features without labels",
            "A multimodal learning system that processes data from multiple modalities simultaneously",
            "A cross-modal retrieval system that finds relevant content across different data types",
            "A visual question answering system that answers questions about images",
            "An image captioning system that generates natural language descriptions of images",
            "A text-to-image generation system that creates images from textual descriptions",
            "A speech recognition system that converts spoken language to text",
            "A speech synthesis system that generates human-like speech from text",
            "A voice conversion system that transforms one speaker's voice to another",
            "A speaker identification system that recognizes individuals by their voice",
            "An emotion recognition system that detects emotional states from speech or text",
            "A sentiment analysis system that determines emotional tone in text",
            "A text classification system that categorizes documents into predefined classes",
            "A named entity recognition system that identifies and classifies entities in text",
            "A relation extraction system that identifies relationships between entities",
            "A question answering system that provides answers to natural language questions",
            "A machine translation system that converts text between different languages",
            "A text summarization system that creates concise summaries of long documents",
            "A dialogue system that engages in natural conversations with users",
            "A chatbot that provides automated customer service through text interactions",
            "A conversational AI system that understands and responds to human dialogue",
            "A recommendation system that suggests relevant items to users",
            "A collaborative filtering system that recommends based on user behavior patterns",
            "A content-based filtering system that recommends based on item characteristics",
            "A hybrid recommendation system that combines multiple recommendation approaches",
            "A matrix factorization technique that discovers latent factors in user-item interactions"
        ]
        
        self.claim_sets = [
            # Set 1: Wireless Communication
            [
                {
                    "claim_number": "1",
                    "claim_text": "A wireless communication system for optimizing signal transmission and reducing interference in 5G networks, comprising: a plurality of base stations configured to transmit and receive signals; a network of user devices in communication with the base stations; a machine learning algorithm executed by a processor, the machine learning algorithm being trained to analyze real-time data from the base stations and user devices, wherein the algorithm optimizes signal transmission parameters based on the analyzed data; a feedback loop that adjusts the transmission parameters of the base stations in response to the output of the machine learning algorithm, thereby minimizing interference among the user devices.",
                    "claim_type": "independent",
                    "technical_focus": "system architecture"
                },
                {
                    "claim_number": "2",
                    "claim_text": "The wireless communication system of claim 1, wherein the machine learning algorithm utilizes historical data of signal transmission and interference patterns to enhance the optimization process.",
                    "claim_type": "dependent",
                    "dependency": "1",
                    "technical_focus": "additional features"
                }
            ],
            # Set 2: Blockchain
            [
                {
                    "claim_number": "1",
                    "claim_text": "A blockchain-based voting system comprising: a distributed ledger network comprising a plurality of nodes; a voter authentication module configured to verify voter identity; a ballot creation module configured to generate encrypted ballots; a voting module configured to record votes on the distributed ledger; and a verification module configured to validate vote integrity and prevent double voting.",
                    "claim_type": "independent",
                    "technical_focus": "system architecture"
                },
                {
                    "claim_number": "2",
                    "claim_text": "The blockchain-based voting system of claim 1, wherein the voter authentication module uses biometric data to verify voter identity.",
                    "claim_type": "dependent",
                    "dependency": "1",
                    "technical_focus": "authentication"
                }
            ],
            # Set 3: AI/ML
            [
                {
                    "claim_number": "1",
                    "claim_text": "A machine learning system for adaptive learning comprising: a neural network architecture comprising multiple layers of interconnected nodes; a training module configured to train the neural network on initial data; an adaptation module configured to modify the neural network architecture based on new data patterns; and a prediction module configured to generate predictions using the adapted neural network.",
                    "claim_type": "independent",
                    "technical_focus": "system architecture"
                }
            ],
            # Set 4: IoT
            [
                {
                    "claim_number": "1",
                    "claim_text": "An Internet of Things (IoT) sensor network system comprising: a plurality of sensor nodes distributed across a geographic area; a communication network connecting the sensor nodes; a data processing unit configured to aggregate data from the sensor nodes; and a predictive maintenance module configured to analyze the aggregated data to predict equipment failures.",
                    "claim_type": "independent",
                    "technical_focus": "system architecture"
                },
                {
                    "claim_number": "2",
                    "claim_text": "The IoT sensor network system of claim 1, wherein the sensor nodes are configured to operate on low power and communicate using wireless protocols.",
                    "claim_type": "dependent",
                    "dependency": "1",
                    "technical_focus": "power management"
                }
            ],
            # Set 5: Cybersecurity
            [
                {
                    "claim_number": "1",
                    "claim_text": "A cybersecurity system for detecting advanced persistent threats comprising: a network monitoring module configured to analyze network traffic; a behavioral analysis engine configured to identify anomalous patterns; a threat intelligence database containing known attack signatures; and a response module configured to automatically mitigate detected threats.",
                    "claim_type": "independent",
                    "technical_focus": "system architecture"
                }
            ]
        ]
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and return comprehensive results."""
        logger.info("Starting final comprehensive legal tools testing...")
        start_time = time.time()
        
        # Test Prior Art Search Tool (50 tests)
        await self.test_prior_art_search_tool()
        
        # Test Claim Drafting Tool (50 tests)
        await self.test_claim_drafting_tool()
        
        # Test Claim Analysis Tool (5 tests)
        await self.test_claim_analysis_tool()
        
        # Test Integration Scenarios (5 tests)
        await self.test_integration_scenarios()
        
        total_time = time.time() - start_time
        
        # Generate test report
        report = self.generate_test_report(total_time)
        
        logger.info(f"Testing completed in {total_time:.2f} seconds")
        return report
    
    async def test_prior_art_search_tool(self):
        """Test Prior Art Search Tool with various queries."""
        logger.info("Testing Prior Art Search Tool (50 tests)...")
        
        for i, query in enumerate(self.prior_art_queries[:50]):  # Test first 50 queries
            test_name = f"prior_art_search_{i+1}"
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/legal-tools/prior-art-search",
                    json={
                        "query": query,
                        "max_results": 5,
                        "relevance_threshold": 0.3,
                        "include_claims": True,
                        "analysis_type": "comprehensive"
                    },
                    timeout=60
                )
                
                execution_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results_found", 0) >= 0 and "patents" in data:
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="prior_art_search",
                            status="PASS",
                            execution_time=execution_time,
                            response_data=data
                        ))
                        logger.info(f"✓ {test_name} - PASSED ({execution_time:.2f}s) - {data.get('results_found', 0)} results")
                    else:
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="prior_art_search",
                            status="FAIL",
                            execution_time=execution_time,
                            error_message="Invalid response structure"
                        ))
                        logger.error(f"✗ {test_name} - FAILED: Invalid response structure")
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        tool="prior_art_search",
                        status="ERROR",
                        execution_time=execution_time,
                        error_message=f"HTTP {response.status_code}: {response.text}"
                    ))
                    logger.error(f"✗ {test_name} - ERROR: HTTP {response.status_code}")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=test_name,
                    tool="prior_art_search",
                    status="ERROR",
                    execution_time=execution_time,
                    error_message=str(e)
                ))
                logger.error(f"✗ {test_name} - ERROR: {str(e)}")
    
    async def test_claim_drafting_tool(self):
        """Test Claim Drafting Tool with various invention descriptions."""
        logger.info("Testing Claim Drafting Tool (50 tests)...")
        
        for i, description in enumerate(self.invention_descriptions[:50]):  # Test first 50 descriptions
            test_name = f"claim_drafting_{i+1}"
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/legal-tools/claim-drafting",
                    json={
                        "invention_description": description,
                        "claim_count": 2,
                        "include_dependent": True,
                        "technical_focus": "general"
                    },
                    timeout=60
                )
                
                execution_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get("claims_generated", 0) > 0 and 
                        "claims" in data and 
                        len(data["claims"]) > 0 and
                        "drafting_report" in data):
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="claim_drafting",
                            status="PASS",
                            execution_time=execution_time,
                            response_data=data
                        ))
                        logger.info(f"✓ {test_name} - PASSED ({execution_time:.2f}s) - {data.get('claims_generated', 0)} claims")
                    else:
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="claim_drafting",
                            status="FAIL",
                            execution_time=execution_time,
                            error_message="Invalid response structure or no claims generated"
                        ))
                        logger.error(f"✗ {test_name} - FAILED: Invalid response structure")
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        tool="claim_drafting",
                        status="ERROR",
                        execution_time=execution_time,
                        error_message=f"HTTP {response.status_code}: {response.text}"
                    ))
                    logger.error(f"✗ {test_name} - ERROR: HTTP {response.status_code}")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=test_name,
                    tool="claim_drafting",
                    status="ERROR",
                    execution_time=execution_time,
                    error_message=str(e)
                ))
                logger.error(f"✗ {test_name} - ERROR: {str(e)}")
    
    async def test_claim_analysis_tool(self):
        """Test Claim Analysis Tool with various claim sets."""
        logger.info("Testing Claim Analysis Tool (5 tests)...")
        
        for i, claim_set in enumerate(self.claim_sets):
            test_name = f"claim_analysis_{i+1}"
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/legal-tools/claim-analysis",
                    json={
                        "claims": claim_set,
                        "analysis_type": "comprehensive",
                        "focus_areas": ["validity", "quality", "improvements"]
                    },
                    timeout=60
                )
                
                execution_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get("claims_analyzed", 0) > 0 and 
                        "analysis" in data and 
                        "quality_assessment" in data and
                        "recommendations" in data and
                        "analysis_report" in data):
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="claim_analysis",
                            status="PASS",
                            execution_time=execution_time,
                            response_data=data
                        ))
                        logger.info(f"✓ {test_name} - PASSED ({execution_time:.2f}s) - {data.get('claims_analyzed', 0)} claims analyzed")
                    else:
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="claim_analysis",
                            status="FAIL",
                            execution_time=execution_time,
                            error_message="Invalid response structure"
                        ))
                        logger.error(f"✗ {test_name} - FAILED: Invalid response structure")
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        tool="claim_analysis",
                        status="ERROR",
                        execution_time=execution_time,
                        error_message=f"HTTP {response.status_code}: {response.text}"
                    ))
                    logger.error(f"✗ {test_name} - ERROR: HTTP {response.status_code}")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=test_name,
                    tool="claim_analysis",
                    status="ERROR",
                    execution_time=execution_time,
                    error_message=str(e)
                ))
                logger.error(f"✗ {test_name} - ERROR: {str(e)}")
    
    async def test_integration_scenarios(self):
        """Test integration scenarios combining multiple tools."""
        logger.info("Testing Integration Scenarios (5 tests)...")
        
        integration_scenarios = [
            {
                "name": "draft_then_analyze_1",
                "description": "A machine learning system for fraud detection in financial transactions"
            },
            {
                "name": "draft_then_analyze_2", 
                "description": "A blockchain-based supply chain tracking system"
            },
            {
                "name": "draft_then_analyze_3",
                "description": "An IoT-based smart city infrastructure monitoring system"
            },
            {
                "name": "draft_then_analyze_4",
                "description": "A quantum computing algorithm for portfolio optimization"
            },
            {
                "name": "draft_then_analyze_5",
                "description": "A computer vision system for autonomous vehicle navigation"
            }
        ]
        
        for scenario in integration_scenarios:
            test_name = f"integration_{scenario['name']}"
            start_time = time.time()
            
            try:
                # Step 1: Draft claims
                draft_response = self.session.post(
                    f"{self.base_url}/api/v1/legal-tools/claim-drafting",
                    json={
                        "invention_description": scenario["description"],
                        "claim_count": 2,
                        "include_dependent": True
                    },
                    timeout=60
                )
                
                if draft_response.status_code == 200:
                    draft_data = draft_response.json()
                    claims = draft_data.get("claims", [])
                    
                    if claims:
                        # Step 2: Analyze the drafted claims
                        analysis_response = self.session.post(
                            f"{self.base_url}/api/v1/legal-tools/claim-analysis",
                            json={
                                "claims": claims,
                                "analysis_type": "comprehensive"
                            },
                            timeout=60
                        )
                        
                        execution_time = time.time() - start_time
                        
                        if analysis_response.status_code == 200:
                            analysis_data = analysis_response.json()
                            self.test_results.append(TestResult(
                                test_name=test_name,
                                tool="integration",
                                status="PASS",
                                execution_time=execution_time,
                                response_data={"draft": draft_data, "analysis": analysis_data}
                            ))
                            logger.info(f"✓ {test_name} - PASSED ({execution_time:.2f}s)")
                        else:
                            self.test_results.append(TestResult(
                                test_name=test_name,
                                tool="integration",
                                status="FAIL",
                                execution_time=execution_time,
                                error_message=f"Analysis failed: HTTP {analysis_response.status_code}"
                            ))
                            logger.error(f"✗ {test_name} - FAILED: Analysis step failed")
                    else:
                        execution_time = time.time() - start_time
                        self.test_results.append(TestResult(
                            test_name=test_name,
                            tool="integration",
                            status="FAIL",
                            execution_time=execution_time,
                            error_message="No claims generated in draft step"
                        ))
                        logger.error(f"✗ {test_name} - FAILED: No claims generated")
                else:
                    execution_time = time.time() - start_time
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        tool="integration",
                        status="FAIL",
                        execution_time=execution_time,
                        error_message=f"Draft failed: HTTP {draft_response.status_code}"
                    ))
                    logger.error(f"✗ {test_name} - FAILED: Draft step failed")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=test_name,
                    tool="integration",
                    status="ERROR",
                    execution_time=execution_time,
                    error_message=str(e)
                ))
                logger.error(f"✗ {test_name} - ERROR: {str(e)}")
    
    def generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        error_tests = len([r for r in self.test_results if r.status == "ERROR"])
        
        # Group by tool
        tool_stats = {}
        for result in self.test_results:
            tool = result.tool
            if tool not in tool_stats:
                tool_stats[tool] = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
            tool_stats[tool]["total"] += 1
            if result.status == "PASS":
                tool_stats[tool]["passed"] += 1
            elif result.status == "FAIL":
                tool_stats[tool]["failed"] += 1
            else:
                tool_stats[tool]["errors"] += 1
        
        # Calculate average execution times
        avg_execution_times = {}
        for tool in tool_stats.keys():
            tool_results = [r for r in self.test_results if r.tool == tool]
            avg_time = sum(r.execution_time for r in tool_results) / len(tool_results) if tool_results else 0
            avg_execution_times[tool] = avg_time
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time
            },
            "tool_statistics": tool_stats,
            "average_execution_times": avg_execution_times,
            "failed_tests": [
                {
                    "test_name": r.test_name,
                    "tool": r.tool,
                    "error": r.error_message
                }
                for r in self.test_results if r.status in ["FAIL", "ERROR"]
            ],
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "tool": r.tool,
                    "status": r.status,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message
                }
                for r in self.test_results
            ]
        }
        
        return report

async def main():
    """Main test execution function."""
    tester = LegalToolsFinalTester()
    
    try:
        # Check if server is running
        response = requests.get("https://localhost:9000/health", verify=False, timeout=30)
        if response.status_code != 200:
            logger.error("Server is not running or not accessible")
            return
        
        logger.info("Server is accessible, starting final comprehensive tests...")
        
        # Run all tests
        report = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("FINAL COMPREHENSIVE LEGAL TOOLS TEST REPORT")
        print("="*80)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Errors: {report['summary']['errors']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Total Execution Time: {report['summary']['total_execution_time']:.2f} seconds")
        
        print("\nTool Statistics:")
        for tool, stats in report['tool_statistics'].items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {tool}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        print(f"\nAverage Execution Times:")
        for tool, avg_time in report['average_execution_times'].items():
            print(f"  {tool}: {avg_time:.2f}s")
        
        if report['failed_tests']:
            print(f"\nFailed Tests ({len(report['failed_tests'])}):")
            for failed in report['failed_tests'][:10]:  # Show first 10 failures
                print(f"  - {failed['test_name']} ({failed['tool']}): {failed['error']}")
            if len(report['failed_tests']) > 10:
                print(f"  ... and {len(report['failed_tests']) - 10} more failures")
        
        # Save detailed report
        with open(f"final_legal_tools_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: final_legal_tools_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Return success if all tests passed
        if report['summary']['failed'] == 0 and report['summary']['errors'] == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            return True
        else:
            print(f"\n❌ {report['summary']['failed'] + report['summary']['errors']} TESTS FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

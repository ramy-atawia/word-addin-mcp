# Technical Implementation Guide

## Architecture Overview

The MCP tools system follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  (React/TypeScript - Word Add-in Task Pane)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                   API Layer                                 │
│  (FastAPI - REST endpoints, MCP proxy)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ Internal calls
┌─────────────────────▼───────────────────────────────────────┐
│                Agent Service Layer                          │
│  (Intent detection, routing, response formatting)          │
└─────────────────────┬───────────────────────────────────────┘
                      │ Tool execution
┌─────────────────────▼───────────────────────────────────────┐
│                MCP Orchestrator Layer                       │
│  (Unified tool execution, parameter validation)            │
└─────────────────────┬───────────────────────────────────────┘
                      │ Server routing
┌─────────────────────▼───────────────────────────────────────┐
│                Tool Implementation Layer                    │
│  (Web Search, Prior Art, Claim Drafting, Claim Analysis)   │
└─────────────────────┬───────────────────────────────────────┘
                      │ Service calls
┌─────────────────────▼───────────────────────────────────────┐
│                Service Layer                                │
│  (Google API, PatentsView API, Azure OpenAI)               │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Function Flows

### 1. Web Search Tool Flow

```python
# Entry Point: Agent Service
async def process_user_message(self, user_message: str, ...):
    # 1. Intent Detection
    intent_type, tool_name, parameters, reasoning = await self.detect_intent_and_route(...)
    
    # 2. Tool Execution
    if intent_type == "tool_execution":
        execution_result = await orchestrator.execute_tool(tool_name, parameters)
        
    # 3. Response Formatting
    final_response = await self.format_tool_output_with_llm(execution_result, user_message, tool_name)

# Web Search Tool Implementation
async def execute(self, parameters: Dict[str, Any]) -> str:
    # 1. Parameter Validation
    is_valid, error_message = await self.validate_parameters(parameters)
    if not is_valid:
        raise ValueError(error_message)
    
    # 2. Service Call
    async with WebSearchService() as search_service:
        search_results = await search_service.search_google(
            query=parameters["query"],
            max_results=parameters.get("max_results", 10)
        )
    
    # 3. Result Formatting
    return self._format_search_results(search_results, parameters["query"])

# Web Search Service
async def search_google(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    # 1. API Request Preparation
    search_params = {
        'key': self.api_key,
        'cx': self.search_engine_id,
        'q': query,
        'num': min(max_results, 10)
    }
    
    # 2. API Call
    async with aiohttp.ClientSession() as session:
        async with session.get(self.search_url, params=search_params) as response:
            data = await response.json()
    
    # 3. Result Processing
    return self._process_search_results(data)
```

### 2. Prior Art Search Tool Flow

```python
# Prior Art Search Tool
async def execute(self, parameters: Dict[str, Any]) -> str:
    # 1. Parameter Extraction
    query = parameters.get("query", "")
    context = parameters.get("context")
    conversation_history = parameters.get("conversation_history")
    max_results = parameters.get("max_results", 20)
    
    # 2. Patent Search Execution
    search_result, generated_queries = await self.patent_service.search_patents(
        query=query,
        context=context,
        conversation_history=conversation_history,
        max_results=max_results
    )
    
    # 3. Return Report
    return search_result["report"]

# Patent Search Service
async def search_patents(self, query: str, context: str = None, 
                        conversation_history: str = None, max_results: int = 20):
    # 1. Generate Search Queries (LLM)
    search_queries = await self._generate_search_queries(query, context, conversation_history)
    
    # 2. Execute PatentsView API Calls
    all_patents = []
    for search_query in search_queries:
        patents = await self._search_patents_view(search_query)
        all_patents.extend(patents)
    
    # 3. Fetch Patent Claims
    for patent in all_patents:
        claims = await self._fetch_claims(patent['patent_id'])
        patent['claims'] = claims
    
    # 4. Generate Report (LLM)
    report = await self._generate_report(query, search_queries, all_patents)
    
    return {
        "query": query,
        "results_found": len(all_patents),
        "patents": all_patents,
        "report": report
    }, search_queries
```

### 3. Claim Drafting Tool Flow

```python
# Claim Drafting Tool
async def execute(self, parameters: Dict[str, Any]) -> str:
    # 1. Parameter Validation
    user_query = parameters.get("user_query", "")
    if not user_query or len(user_query.strip()) < 3:
        return "Error: Invalid user query - must be at least 3 characters long"
    
    # 2. Service Call
    async with ClaimDraftingService() as drafting_service:
        drafting_result, generated_criteria = await drafting_service.draft_claims(
            user_query=user_query,
            conversation_context=parameters.get("conversation_context"),
            document_reference=parameters.get("document_reference")
        )
    
    # 3. Return Result
    return drafting_result["drafting_report"]

# Claim Drafting Service
async def draft_claims(self, user_query: str, conversation_context: Optional[str] = None, 
                      document_reference: Optional[str] = None):
    # 1. Load Prompts
    system_prompt = self._load_system_prompt()
    user_prompt = self._load_user_prompt(user_query, conversation_context, document_reference)
    
    # 2. Generate Claims (LLM)
    claims_markdown = await self._draft_claims_with_llm_simple(
        user_query, conversation_context, document_reference
    )
    
    # 3. Create Result
    result = {
        "user_query": user_query,
        "drafting_report": claims_markdown,
        "drafting_metadata": {
            "timestamp": datetime.now().isoformat()
        }
    }
    
    return result, []

# LLM Claim Generation
async def _draft_claims_with_llm_simple(self, user_query: str, conversation_context: Optional[str], 
                                       document_reference: Optional[str]) -> str:
    # 1. Load Prompts
    system_prompt = self._load_system_prompt()
    user_prompt = self._load_user_prompt(user_query, conversation_context, document_reference)
    
    # 2. Generate Claims
    response_data = self.llm_client.generate_text(
        prompt=user_prompt,
        system_message=system_prompt,
        max_tokens=4000,
        temperature=0.3
    )
    
    # 3. Return Generated Claims
    return response_data.get("text", "")
```

### 4. Claim Analysis Tool Flow

```python
# Claim Analysis Tool
async def execute(self, parameters: Dict[str, Any]) -> str:
    # 1. Parameter Validation
    claims = parameters.get("claims", [])
    if not claims or not isinstance(claims, list):
        return "Error: Invalid claims input - claims must be a non-empty list"
    
    # 2. Service Call
    async with ClaimAnalysisService() as analysis_service:
        analysis_result, generated_criteria = await analysis_service.analyze_claims(
            claims=claims,
            analysis_type=parameters.get("analysis_type", "comprehensive"),
            focus_areas=parameters.get("focus_areas", [])
        )
    
    # 3. Return Result
    return analysis_result["analysis_report"]

# Claim Analysis Service
async def analyze_claims(self, claims: List[Dict[str, Any]], analysis_type: str = "comprehensive",
                        focus_areas: Optional[List[str]] = None):
    # 1. Load Prompts
    system_prompt = self._load_system_prompt()
    user_prompt = self._load_user_prompt(claims, analysis_type, focus_areas)
    
    # 2. Analyze Claims (LLM)
    analysis_result = await self._analyze_claims_with_llm(claims, analysis_type, focus_areas)
    
    # 3. Generate Analysis Report
    analysis_report = await self._generate_analysis_report(analysis_result, claims)
    
    # 4. Create Result
    result = {
        "claims_analyzed": len(claims),
        "analysis_type": analysis_type,
        "analysis_report": analysis_report,
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
            "focus_areas": focus_areas or []
        }
    }
    
    return result, []
```

## LLM Integration Details

### 1. Intent Detection

```python
# System Prompt for Intent Detection
system_prompt = '''
Analyze user input and determine whether to call a tool or provide a conversational response.

IMPORTANT RULES:
1. For web search requests like "web search [query]" or "search for [query]":
   - Extract the query after "web search" or "search for"
   - Use web_search_tool with {"query": "extracted_query"}

2. For prior art search or patent search:
   - Use prior_art_search_tool with the invention/technology as query

3. For claim drafting:
   - Use claim_drafting_tool with user query, conversation context, and document reference
   - ALWAYS include the document content in document_reference parameter
   - ALWAYS include conversation history in conversation_context parameter

4. For claim analysis:
   - Use claim_analysis_tool with claims array and analysis parameters

Respond with JSON in one of two formats:

Tool Call:
{"action": "tool_call", "tool_name": "tool_name", "parameters": {...}}

Conversation:
{"action": "conversation", "response": "conversational response"}
'''
```

### 2. Response Formatting

```python
# System Prompt for Response Formatting
system_prompt = f"""You are a helpful assistant that formats tool outputs into user-friendly responses.

Your task is to take raw tool output and format it into clean, readable markdown that answers the user's query.

Guidelines:
1. Parse and structure the data intelligently
2. Use proper markdown formatting (headings, lists, links, etc.)
3. Make the content easy to read and understand
4. Include relevant links and references
5. Focus on answering the user's specific question
6. If the data contains search results, format them as a structured list
7. Clean up any escaped characters or formatting issues
8. Keep the response concise but comprehensive

Tool used: {tool_name or 'Unknown tool'}
User query: {user_query}

Format the following tool output into a clean, user-friendly response:"""
```

### 3. Claim Drafting Prompts

```python
# System Prompt for Claim Drafting
system_prompt = """You are a patent claim specialist. Generate high-quality patent claims in markdown format.

OUTPUT FORMAT:
Generate a markdown document with this structure:

# Patent Claims

## Claim 1 (Independent)
[Independent claim text describing the main invention with technical details]

## Claim 2 (Dependent)
The [system/method/apparatus] of claim 1, wherein [specific additional feature]

## Claim 3 (Dependent)
The [system/method/apparatus] of claim 1, further comprising [additional component]

[Continue with additional dependent claims as needed]

RULES:
- Use proper patent terminology (comprising, configured to, wherein, etc.)
- Make claims specific and technically detailed
- Ensure dependent claims properly reference their parent claims
- Focus on the novel and non-obvious aspects of the invention
- Use clear, unambiguous language
- Include technical details that make the invention unique"""

# User Prompt for Claim Drafting
user_prompt = f"""Draft patent claims for the following invention:

User Query: {user_query}

Conversation Context: {conversation_context}

Document Reference: {document_reference}

Please generate comprehensive patent claims that cover the invention described in the user query, taking into account any relevant context from the conversation and document."""
```

### 4. Claim Analysis Prompts

```python
# System Prompt for Claim Analysis
system_prompt = """You are a patent attorney analyzing patent claims for validity, quality, and improvement opportunities. Your expertise includes:

1. CLAIM STRUCTURE ANALYSIS:
   - Independent vs dependent claim relationships
   - Proper claim dependencies and numbering
   - Claim breadth and scope assessment

2. VALIDITY ASSESSMENT:
   - 35 USC 101 (subject matter eligibility)
   - 35 USC 112 (written description, enablement, definiteness)
   - 35 USC 103 (obviousness)
   - 35 USC 102 (novelty)

3. QUALITY EVALUATION:
   - Clarity and definiteness
   - Technical accuracy and specificity
   - Breadth vs. specificity balance
   - Defensibility and enforcement potential

4. IMPROVEMENT RECOMMENDATIONS:
   - Specific language improvements
   - Structural enhancements
   - Additional claim opportunities
   - Risk mitigation strategies

Provide comprehensive, actionable analysis that helps improve patent claim quality and validity."""

# User Prompt for Claim Analysis
user_prompt = f"""Analyze the following patent claims for validity, quality, and improvement opportunities:

{claims_text}

Analysis Type: {analysis_type}
Focus Areas: {focus_areas}

Provide comprehensive analysis covering:
1. Claim structure and dependencies
2. Validity assessment (35 USC 101, 112, 103, 102)
3. Quality evaluation (clarity, breadth, defensibility)
4. Improvement recommendations
5. Risk assessment and mitigation strategies"""
```

## Error Handling Strategy

### 1. Parameter Validation

```python
async def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
    """Validate and sanitize input parameters."""
    # Validate user_query
    user_query = parameters.get("user_query", "").strip()
    if not user_query or len(user_query) < 3:
        return False, "User query must be at least 3 characters long"
    if len(user_query) > 1000:
        return False, "User query too long (max 1000 characters)"
    
    # Sanitize input
    user_query = self._sanitize_input(user_query)
    
    return True, ""
```

### 2. LLM Error Handling

```python
def generate_text(self, prompt: str, max_tokens: int = 1000, 
                 temperature: float = 0.7, system_message: Optional[str] = None, 
                 max_retries: int = 3) -> Dict[str, Any]:
    # Make API call with retry logic
    last_error = None
    for attempt in range(max_retries):
        try:
            response = self.client.chat.completions.create(
                model=self.azure_openai_deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            break  # Success, exit retry loop
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(f"LLM API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise e
```

### 3. Service Error Handling

```python
async def execute(self, parameters: Dict[str, Any]) -> str:
    try:
        # Tool execution logic
        result = await self._execute_tool_logic(parameters)
        return result
    except ImportError:
        logger.error("Service not available, using placeholder")
        return self._create_fallback_response(parameters)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return f"# Error Report\n\n**Error**: {str(e)}"
```

## Performance Optimization

### 1. Caching Strategy

```python
# LLM Response Caching
@lru_cache(maxsize=1000)
def _cached_llm_call(self, prompt_hash: str, system_message_hash: str) -> str:
    # Cache LLM responses for repeated queries
    pass
```

### 2. Rate Limiting

```python
# API Rate Limiting
class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        now = time.time()
        # Remove old calls
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            await asyncio.sleep(self.time_window - (now - self.calls[0]))
        
        self.calls.append(now)
```

### 3. Resource Management

```python
# Proper Resource Cleanup
async def execute(self, parameters: Dict[str, Any]) -> str:
    async with WebSearchService() as search_service:
        # Service automatically cleaned up
        result = await search_service.search_google(...)
    
    return result
```

## Security Considerations

### 1. Input Sanitization

```python
def _sanitize_input(self, text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    # Limit length
    text = text[:1000]
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    return text
```

### 2. API Key Management

```python
# Secure API Key Storage
class SecureConfig:
    def __init__(self):
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Azure OpenAI API key not configured")
    
    def get_llm_client(self):
        return LLMClient(
            azure_openai_api_key=self.api_key,
            azure_openai_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            azure_openai_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT')
        )
```

### 3. Access Control

```python
# Tool Access Control
class ToolAccessControl:
    def __init__(self):
        self.allowed_tools = {
            'web_search_tool': ['user', 'admin'],
            'prior_art_search_tool': ['user', 'admin'],
            'claim_drafting_tool': ['admin'],
            'claim_analysis_tool': ['admin']
        }
    
    def can_access_tool(self, user_role: str, tool_name: str) -> bool:
        return user_role in self.allowed_tools.get(tool_name, [])
```

## Monitoring and Logging

### 1. Performance Monitoring

```python
# Performance Metrics
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'tool_executions': 0,
            'total_execution_time': 0.0,
            'error_count': 0,
            'llm_calls': 0
        }
    
    def record_tool_execution(self, tool_name: str, execution_time: float, success: bool):
        self.metrics['tool_executions'] += 1
        self.metrics['total_execution_time'] += execution_time
        if not success:
            self.metrics['error_count'] += 1
```

### 2. Audit Logging

```python
# Audit Logging
class AuditLogger:
    def log_tool_execution(self, user_id: str, tool_name: str, parameters: Dict, result: str):
        logger.info(f"Tool execution: user={user_id}, tool={tool_name}, parameters={parameters}, success={bool(result)}")
    
    def log_llm_call(self, prompt: str, response: str, tokens_used: int):
        logger.info(f"LLM call: prompt_length={len(prompt)}, response_length={len(response)}, tokens={tokens_used}")
```

This technical implementation guide provides a comprehensive overview of how each tool works internally, including the specific functions, LLM usage, error handling, and security considerations.

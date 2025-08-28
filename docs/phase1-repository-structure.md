# Phase 1 Repository Structure - Word Add-in MCP Project

## Overview
Repository structure for Phase 1 (POC) implementation with clear separation of concerns, following the project requirements for React frontend, Python MCP client middleware, and LangChain agent backend.

## Root Directory Structure
```
word-addin-mcp/
├── README.md                           # Project overview and setup
├── .gitignore                          # Git ignore patterns
├── docker-compose.yml                  # Local development setup
├── .env.example                        # Environment variables template
├── requirements.txt                    # Python dependencies
├── package.json                        # Node.js dependencies
├── tsconfig.json                       # TypeScript configuration
├── webpack.config.js                   # Webpack configuration for Word Add-in
├── manifest.xml                        # Word Add-in manifest
├── src/                                # Frontend React application
├── backend/                            # Python FastAPI backend
├── middleware/                         # Python MCP client middleware
├── docs/                               # Documentation
├── tests/                              # Test files
├── scripts/                            # Build and deployment scripts
└── config/                             # Configuration files
```

## Frontend Structure (`src/`)

### Core Components
```
src/
├── components/
│   ├── ChatInterface.tsx               # Main chat component
│   ├── ChatHistory.tsx                 # Chat history display
│   ├── SettingsModal.tsx               # MCP server configuration
│   ├── WordDocument.tsx                # Document interaction
│   ├── MessageInput.tsx                # Message input component
│   ├── MessageBubble.tsx               # Individual message display
│   ├── LoadingIndicator.tsx            # Loading states
│   └── ErrorBoundary.tsx               # Error handling
├── services/
│   ├── officeService.ts                # Office.js API wrapper
│   ├── chatService.ts                  # Chat API communication
│   ├── mcpService.ts                   # MCP tool communication
│   ├── documentService.ts              # Document operations
│   └── sessionService.ts               # Session management
├── hooks/
│   ├── useChat.ts                      # Chat state management
│   ├── useMCPTools.ts                  # MCP tools management
│   ├── useDocument.ts                  # Document state
│   └── useSession.ts                   # Session management
├── types/
│   ├── index.ts                        # Main type definitions
│   ├── api.ts                          # API response types
│   ├── chat.ts                         # Chat-related types
│   ├── document.ts                     # Document types
│   └── mcp.ts                          # MCP protocol types
├── utils/
│   ├── sessionStorage.ts               # Local session memory
│   ├── constants.ts                    # Application constants
│   ├── helpers.ts                      # Utility functions
│   └── validation.ts                   # Input validation
├── styles/
│   ├── global.css                      # Global styles
│   ├── components.css                  # Component styles
│   └── themes.css                      # Theme variables
├── App.tsx                             # Main application component
├── index.tsx                           # Application entry point
└── office.d.ts                         # Office.js type definitions
```

## Backend Structure (`backend/`)

### FastAPI Application
```
backend/
├── app/
│   ├── main.py                         # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                 # Configuration management
│   │   ├── database.py                 # Database configuration
│   │   └── azure.py                    # Azure OpenAI configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                 # Chat API endpoints
│   │   │   ├── mcp.py                  # MCP tools API endpoints
│   │   │   ├── document.py             # Document API endpoints
│   │   │   ├── session.py              # Session management endpoints
│   │   │   └── health.py               # Health check endpoints
│   │   └── dependencies.py             # API dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py                 # Security utilities
│   │   ├── exceptions.py               # Custom exceptions
│   │   └── logging.py                  # Logging configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py                     # Chat data models
│   │   ├── session.py                  # Session data models
│   │   ├── document.py                 # Document data models
│   │   └── mcp.py                      # MCP tool models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py                     # Chat request/response schemas
│   │   ├── session.py                  # Session schemas
│   │   ├── document.py                 # Document schemas
│   │   └── mcp.py                      # MCP tool schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_openai.py             # Azure OpenAI integration
│   │   ├── chat_service.py             # Chat business logic
│   │   ├── session_service.py          # Session management
│   │   └── document_service.py         # Document operations
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── langchain_agent.py          # LangChain agent implementation
│   │   ├── agent_factory.py            # Agent creation factory
│   │   └── prompts.py                  # Agent prompts
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── session_memory.py           # Session-based conversation memory
│   │   ├── conversation_memory.py      # Conversation history
│   │   └── document_memory.py          # Document context memory
│   └── middleware/
│       ├── __init__.py
│       ├── cors.py                      # CORS middleware
│       ├── rate_limiting.py            # Rate limiting
│       └── logging.py                  # Request logging
├── requirements.txt                     # Python dependencies
├── Dockerfile                          # Container configuration
├── alembic/                            # Database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
└── tests/
    ├── __init__.py
    ├── conftest.py                      # Test configuration
    ├── test_api/
    │   ├── test_chat.py
    │   ├── test_mcp.py
    │   ├── test_document.py
    │   └── test_session.py
    ├── test_services/
    ├── test_agents/
    └── test_memory/
```

## Middleware Structure (`middleware/`)

### MCP Client Implementation
```
middleware/
├── mcp_client/
│   ├── __init__.py
│   ├── client.py                       # Main MCP client implementation
│   ├── connection.py                    # Server connection management
│   ├── protocol.py                     # MCP protocol handling
│   ├── tools.py                        # Tool interface definitions
│   ├── errors.py                       # MCP-specific errors
│   └── utils.py                        # Utility functions
├── config/
│   ├── __init__.py
│   ├── mcp_config.yaml                 # MCP server configurations
│   ├── settings.py                     # Middleware settings
│   └── logging.py                      # Logging configuration
├── requirements.txt                     # Python dependencies
├── Dockerfile                          # Container configuration
└── tests/
    ├── __init__.py
    ├── test_client.py
    ├── test_connection.py
    ├── test_protocol.py
    └── test_tools.py
```

## Configuration Files

### Environment Configuration
```
config/
├── .env.example                        # Environment variables template
├── development.env                     # Development environment
├── production.env                      # Production environment
└── docker.env                          # Docker environment
```

### Application Configuration
```
config/
├── app/
│   ├── settings.yaml                   # Application settings
│   ├── azure.yaml                      # Azure configuration
│   └── mcp.yaml                        # MCP server configuration
├── logging/
│   ├── logging.yaml                    # Logging configuration
│   └── logrotate.conf                  # Log rotation
└── nginx/
    └── nginx.conf                      # Nginx configuration
```

## Documentation Structure (`docs/`)

### Technical Documentation
```
docs/
├── README.md                           # Documentation overview
├── api/
│   ├── openapi.yaml                    # OpenAPI specification
│   ├── endpoints.md                    # API endpoint documentation
│   └── examples.md                     # API usage examples
├── architecture/
│   ├── overview.md                     # System architecture
│   ├── components.md                   # Component details
│   └── data-flow.md                    # Data flow diagrams
├── development/
│   ├── setup.md                        # Development setup
│   ├── contributing.md                 # Contribution guidelines
│   └── testing.md                      # Testing procedures
├── deployment/
│   ├── local.md                        # Local deployment
│   ├── docker.md                       # Docker deployment
│   └── production.md                   # Production deployment
└── user-guides/
    ├── installation.md                 # Add-in installation
    ├── usage.md                        # User manual
    └── troubleshooting.md              # Common issues
```

## Test Structure

### Frontend Tests
```
tests/
├── frontend/
│   ├── unit/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   ├── integration/
│   └── e2e/
```

### Backend Tests
```
tests/
├── backend/
│   ├── unit/
│   │   ├── api/
│   │   ├── services/
│   │   ├── agents/
│   │   └── memory/
│   ├── integration/
│   └── e2e/
```

### Middleware Tests
```
tests/
├── middleware/
│   ├── unit/
│   │   ├── client/
│   │   ├── connection/
│   │   └── protocol/
│   └── integration/
```

## Scripts Structure (`scripts/`)

### Build and Development
```
scripts/
├── build/
│   ├── build-frontend.sh               # Frontend build script
│   ├── build-backend.sh                # Backend build script
│   └── build-all.sh                    # Complete build script
├── development/
│   ├── start-dev.sh                    # Development environment startup
│   ├── setup-dev.sh                    # Development setup
│   └── reset-dev.sh                    # Development reset
├── deployment/
│   ├── deploy-local.sh                 # Local deployment
│   ├── deploy-docker.sh                # Docker deployment
│   └── deploy-production.sh            # Production deployment
└── testing/
    ├── run-tests.sh                    # Test execution
    ├── coverage.sh                     # Coverage reports
    └── e2e-tests.sh                    # End-to-end tests
```

## Docker Configuration

### Docker Compose
```
docker-compose.yml                      # Local development services
docker-compose.prod.yml                 # Production services
```

### Container Configurations
```
docker/
├── frontend/
│   └── Dockerfile                      # Frontend container
├── backend/
│   └── Dockerfile                      # Backend container
├── middleware/
│   └── Dockerfile                      # Middleware container
└── nginx/
    └── Dockerfile                      # Nginx container
```

## Key Implementation Notes

### Phase 1 Focus Areas
1. **Single MCP Tool Integration**: Implement one MCP tool connection
2. **Real LLM Integration**: No mockups, direct Azure OpenAI integration
3. **Basic Word Add-in**: Core chat functionality with document context
4. **Session Management**: Local session storage and management
5. **Error Handling**: Comprehensive error handling and logging

### File Naming Conventions
- **Components**: PascalCase (e.g., `ChatInterface.tsx`)
- **Services**: camelCase (e.g., `chatService.ts`)
- **Hooks**: camelCase with `use` prefix (e.g., `useChat.ts`)
- **Types**: camelCase (e.g., `chatTypes.ts`)
- **Python**: snake_case (e.g., `chat_service.py`)
- **Configuration**: kebab-case (e.g., `mcp-config.yaml`)

### Import Organization
- **Frontend**: Absolute imports from `src/`
- **Backend**: Absolute imports from `app/`
- **Middleware**: Absolute imports from `mcp_client/`
- **Tests**: Relative imports within test directories

### Dependencies Management
- **Frontend**: `package.json` with exact versions
- **Backend**: `requirements.txt` with pinned versions
- **Middleware**: Separate `requirements.txt` for isolation
- **Development**: `requirements-dev.txt` for development dependencies

# Word Add-in MCP Project

## Overview
Enterprise-grade Word Add-in with Model Context Protocol (MCP) integration, providing AI-powered document creation and analysis capabilities through Azure OpenAI and MCP tools.

## Architecture
- **Frontend**: React TypeScript Word Add-in with Office.js integration
- **Backend**: FastAPI Python backend with LangChain agent
- **Middleware**: MCP client for tool integration
- **AI**: Azure OpenAI integration with real LLM processing
- **Protocol**: Full MCP v1.0 compliance

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Azure OpenAI API access

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd word-addin-mcp

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up Node.js environment
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose up -d
```

### Environment Variables
```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# MCP Server
MCP_SERVER_URL=your_mcp_server_url
MCP_SERVER_TOKEN=your_token

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/wordaddin
```

## Project Structure
```
word-addin-mcp/
├── src/                    # Frontend React application
├── backend/                # FastAPI Python backend
├── middleware/             # MCP client middleware
├── docs/                   # Documentation
├── tests/                  # Test files
├── scripts/                # Build and deployment scripts
├── config/                 # Configuration files
└── docker/                 # Docker configurations
```

## Development

### Frontend Development
```bash
cd src
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run tests
```

### Backend Development
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/backend/
pytest tests/frontend/
pytest tests/integration/
```

## API Documentation
- **OpenAPI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Endpoints**: See `docs/api/` directory

## MCP Tools
- **File Reader**: Read local files with security validation
- **Text Processor**: AI-powered text processing via Azure OpenAI
- **Document Analyzer**: Document quality and readability analysis
- **Web Content Fetcher**: Fetch and process web content
- **Data Formatter**: Format data for Word document insertion

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License
MIT License - see LICENSE file for details

## Support
For questions and support, please open an issue in the repository.

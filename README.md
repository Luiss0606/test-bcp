# Financial Restructuring Assistant

AI-powered financial debt restructuring assistant for bank customers with multiple debts.

## Overview

This application helps bank customers optimize their debt payment strategies by analyzing three scenarios:

1. **Minimum Payment**: Analysis of paying only required minimums
2. **Optimized Plan**: Debt avalanche strategy prioritizing high-interest debts  
3. **Consolidation**: Evaluation of debt consolidation opportunities

The system uses specialized LangChain agents running in parallel to generate natural language explanations for each scenario, with a master agent consolidating all reports into a comprehensive analysis.

## Features

- 🧮 **Multi-scenario debt analysis** with financial calculations
- 🤖 **AI-powered agents** using OpenAI GPT models for natural language reports
- ⚡ **Parallel execution** of analysis agents for better performance
- 🏦 **Consolidation matching** with available bank offers
- 📊 **Comprehensive reporting** with savings calculations and recommendations
- 🐳 **Containerized** with UV package manager for fast, reproducible builds

## Architecture

### Agent System
- **Minimum Payment Agent**: Explains risks and consequences of minimum payments
- **Optimized Payment Agent**: Details benefits of strategic debt payoff (debt avalanche)
- **Consolidation Agent**: Analyzes consolidation options and eligibility requirements
- **Master Consolidator**: Synthesizes all analyses into a unified report

### Technology Stack
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with SQLite
- **LangChain**: AI agent framework with OpenAI integration
- **UV**: Fast Python package manager
- **Docker**: Containerization with official UV images
- **Pydantic**: Data validation and serialization

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:
```bash
git clone <repository>
cd bcp_test
cp .env.example .env
```

2. **Configure environment**:
Edit `.env` file with your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
LOAD_SAMPLE_DATA=true
DEBUG=true
```

3. **Run with Docker Compose**:
```bash
docker-compose up --build
```

The API will be available at http://localhost:8000

### Local Development

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Setup project**:
```bash
uv sync
```

3. **Run the application**:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

### Load Sample Data
```bash
curl -X POST "http://localhost:8000/api/v1/load-data"
```

### Get Customers
```bash
curl "http://localhost:8000/api/v1/customers"
```

### Analyze Customer Debt
```bash
curl -X POST "http://localhost:8000/api/v1/customers/CU-001/analyze"
```

### Generate Client Report
```bash
curl -X POST "http://localhost:8000/api/v1/customers/CU-001/report"
```

### Get Specific Scenario Analysis
```bash
curl "http://localhost:8000/api/v1/customers/CU-001/scenarios/optimized"
```

## Data Structure

The application processes the following data files:

- `loans.csv`: Personal loans and microloans
- `cards.csv`: Credit card balances and terms
- `payment_history.csv`: Customer payment records
- `credit_score_history.csv`: Credit score tracking
- `customer_cashflow.csv`: Income and expense data
- `bank_offers.json`: Available consolidation offers

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/customers` | GET | List all customers |
| `/api/v1/customers/{id}/analyze` | POST | Complete debt analysis |
| `/api/v1/customers/{id}/report` | POST | Formatted client report |
| `/api/v1/customers/{id}/scenarios/{type}` | GET | Individual scenario analysis |
| `/api/v1/offers` | GET | Available consolidation offers |
| `/api/v1/analytics/summary` | GET | System analytics |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | SQLite database path | `sqlite:///./financial_assistant.db` |
| `LOAD_SAMPLE_DATA` | Auto-load sample data on startup | `false` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Agent Configuration

The agents use GPT-4.1-nano for individual analyses and GPT-4.1-mini for the master consolidation report. This provides a good balance of cost and quality.

## Development

### Project Structure
```
app/
├── main.py              # FastAPI application
├── core/
│   └── database.py      # Database configuration
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── agents/              # LangChain agents
└── api/
    └── endpoints.py     # API routes
```

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black .
uv run isort .
```

## Deployment

### Docker Production Build
```bash
docker build -t financial-assistant .
docker run -d -p 8000:8000 --env-file .env financial-assistant
```

### Environment-specific Configurations

For production, ensure:
- Set `DEBUG=false`
- Use a secure database (PostgreSQL recommended)
- Configure proper CORS origins
- Set up monitoring and logging
- Use environment-specific secrets management

## Monitoring

The application includes:
- Health check endpoint at `/api/v1/health`
- Comprehensive error handling with proper HTTP status codes
- Structured logging for debugging
- Analytics endpoint for system metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Submit a pull request

## License

This project is for demonstration purposes. Please ensure compliance with financial regulations in your jurisdiction.

## Support

For questions or issues:
- Check the API documentation at `/docs`
- Review the application logs
- Ensure OpenAI API key is properly configured
- Verify sample data is loaded correctly

"""Main FastAPI application."""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.core.database import create_tables
from app.services.data_loader import load_sample_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Financial Restructuring Assistant...")
    
    # Create database tables
    create_tables()
    print("📊 Database tables created")
    
    # Load sample data if in development
    if os.getenv("LOAD_SAMPLE_DATA", "false").lower() == "true":
        try:
            results = load_sample_data()
            print(f"📈 Sample data loaded: {results}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load sample data: {e}")
    
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Financial Restructuring Assistant...")


# Create FastAPI app
app = FastAPI(
    title="Financial Restructuring Assistant",
    description="""
    AI-powered financial debt restructuring assistant for bank customers.
    
    ## Features
    
    * **Debt Analysis**: Comprehensive analysis of customer debt portfolios
    * **Scenario Modeling**: Three payment scenarios (minimum, optimized, consolidation)
    * **AI Agents**: Specialized LangChain agents for natural language explanations
    * **Parallel Processing**: Concurrent execution of multiple analysis agents
    * **Consolidation Offers**: Smart matching with available bank offers
    
    ## Scenarios
    
    1. **Minimum Payment**: Analysis of paying only required minimums
    2. **Optimized Plan**: Debt avalanche strategy prioritizing high-interest debts
    3. **Consolidation**: Evaluation of debt consolidation opportunities
    
    ## Agent Architecture
    
    - **Minimum Payment Agent**: Explains risks of minimum payments
    - **Optimized Payment Agent**: Details benefits of strategic debt payoff
    - **Consolidation Agent**: Analyzes consolidation options and eligibility
    - **Master Consolidator**: Synthesizes all analyses into comprehensive report
    
    Built with FastAPI, SQLAlchemy, LangChain, and OpenAI GPT models.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An unexpected error occurred",
            "path": str(request.url)
        }
    )


# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Financial Analysis"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Financial Restructuring Assistant",
        "version": "1.0.0",
        "description": "AI-powered debt restructuring analysis for bank customers",
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "features": [
            "Multi-scenario debt analysis",
            "AI-powered natural language reports", 
            "Parallel agent execution",
            "Debt consolidation optimization",
            "Customer eligibility assessment"
        ]
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "api_version": "v1",
        "endpoints": {
            "health": "GET /api/v1/health",
            "load_data": "POST /api/v1/load-data",
            "customers": "GET /api/v1/customers",
            "customer_profile": "GET /api/v1/customers/{customer_id}/profile",
            "analyze_debt": "POST /api/v1/customers/{customer_id}/analyze",
            "generate_report": "POST /api/v1/customers/{customer_id}/report",
            "scenario_analysis": "GET /api/v1/customers/{customer_id}/scenarios/{scenario_type}",
            "consolidation_offers": "GET /api/v1/offers",
            "eligibility_check": "POST /api/v1/customers/{customer_id}/consolidation-eligibility",
            "analytics": "GET /api/v1/analytics/summary"
        },
        "agent_types": ["minimum", "optimized", "consolidation"],
        "supported_debt_types": ["loan", "card"]
    }


if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"🌟 Starting server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        access_log=True
    )

"""Cancer Care Coordinator - FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Application state for services
class AppState:
    """Application state container for services."""
    patient_service = None
    llm_service = None
    analysis_service = None
    vector_store_service = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting Cancer Care Coordinator API...")

    # Initialize database
    from database import init_db_async
    await init_db_async()

    # Initialize services
    from services.patient_service import PatientService
    from services.llm_service import LLMService

    app_state.patient_service = PatientService()
    app_state.llm_service = LLMService(use_mock=settings.USE_MOCK_LLM)

    logger.info(f"Mock mode: LLM={settings.USE_MOCK_LLM}, VectorStore={settings.USE_MOCK_VECTOR_STORE}")
    logger.info("Services initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Cancer Care Coordinator API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered multi-agent system for oncology treatment recommendations",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": str(exc.detail),
            "status_code": exc.status_code
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic liveness check."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check with dependency status."""
    return {
        "status": "ready",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "dependencies": {
            "patient_service": app_state.patient_service is not None,
            "llm_service": app_state.llm_service is not None,
        },
        "config": {
            "mock_llm": settings.USE_MOCK_LLM,
            "mock_vector_store": settings.USE_MOCK_VECTOR_STORE,
            "rag_enabled": settings.ENABLE_RAG,
        }
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers
from routers import patients, analysis, genomics, trials, treatment, evidence, chat, treatment_cycles, treatment_procedures, clinical_notes

app.include_router(patients.router, prefix=settings.API_PREFIX, tags=["Patients"])
app.include_router(analysis.router, prefix=settings.API_PREFIX, tags=["Analysis"])
app.include_router(genomics.router, prefix=settings.API_PREFIX, tags=["Genomics"])
app.include_router(trials.router, prefix=settings.API_PREFIX, tags=["Clinical Trials"])
app.include_router(treatment.router, prefix=settings.API_PREFIX, tags=["Treatment"])
app.include_router(evidence.router, prefix=settings.API_PREFIX, tags=["Evidence"])
app.include_router(chat.router, prefix=settings.API_PREFIX, tags=["Chat"])
app.include_router(treatment_cycles.router, prefix=settings.API_PREFIX, tags=["Treatment Cycles"])
app.include_router(treatment_procedures.router, prefix=settings.API_PREFIX, tags=["Treatment Procedures"])
app.include_router(clinical_notes.router, prefix=settings.API_PREFIX, tags=["Clinical Notes"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

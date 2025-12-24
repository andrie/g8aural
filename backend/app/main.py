"""
FastAPI application entry point for ABRSM Grade 8 Cadence Training.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

# Create FastAPI app
app = FastAPI(
    title="ABRSM Grade 8 Cadence Training API",
    description="Backend API for aural training cadence identification",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5500",  # Common for Live Server
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ABRSM Grade 8 Cadence Training API",
        "version": "1.0.0",
        "docs": "/docs"
    }

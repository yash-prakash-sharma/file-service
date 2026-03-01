from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.db.database import engine
from app.db import models
from app.core.config import settings

# Create database tables (in production, usually handled by Alembic migrations)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/files/openapi.json",
    docs_url="/files/docs",
    redoc_url="/files/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://d1vyb8a355t0zz.cloudfront.net",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/files/api/v1")

@app.get("/files/")
def root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}

@app.get("/files/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

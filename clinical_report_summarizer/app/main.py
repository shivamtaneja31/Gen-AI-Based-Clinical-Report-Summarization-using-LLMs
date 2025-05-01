import logging
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api.endpoints import router
from app.core.config import settings
from app.services.storage import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events
    """
    # Startup
    logger.info("Initializing application...")
    try:
        # Initialize database connection and schema
        await db_service.init_pool()
        await db_service.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing")
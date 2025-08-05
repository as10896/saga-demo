"""
Redis configuration and connection management
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis

from .session_manager import AsyncSessionManager

logger = logging.getLogger(__name__)

# Global session manager instance
session_manager: AsyncSessionManager | None = None


def get_redis_url() -> str:
    """Get Redis URL from environment or use default."""
    return os.getenv("REDIS_URL", "redis://localhost:6379")


async def create_redis_client() -> redis.Redis:
    """Create and test Redis client connection."""
    redis_url = get_redis_url()
    client = redis.from_url(redis_url, decode_responses=False)

    # Test the connection
    await client.ping()
    logger.info(f"Successfully connected to Redis at {redis_url}")

    return client


async def initialize_session_manager(redis_client: redis.Redis) -> AsyncSessionManager:
    """Initialize the async session manager with Redis client."""
    manager = AsyncSessionManager(redis_client)
    logger.info("Session manager initialized")
    return manager


@asynccontextmanager
async def redis_lifespan() -> AsyncGenerator[AsyncSessionManager, None]:
    """
    Manage Redis connection and session manager lifecycle.

    This context manager:
    1. Connects to Redis on startup
    2. Initializes the session manager
    3. Yields the session manager for use
    4. Closes Redis connection on shutdown
    """
    global session_manager

    try:
        # Startup: Initialize Redis and session manager
        logger.info("Starting Redis connection...")
        redis_client = await create_redis_client()

        session_manager = await initialize_session_manager(redis_client)
        logger.info("Redis and session manager ready")

        yield session_manager

    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.error("Make sure Redis is running and accessible")
        raise

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    finally:
        # Shutdown: Clean up Redis connection
        if session_manager:
            await session_manager.redis_client.aclose()
            session_manager = None
            logger.info("Redis connection closed")


def get_session_manager() -> AsyncSessionManager:
    """
    Get the current session manager instance.

    Raises:
        RuntimeError: If session manager is not initialized
    """
    if not session_manager:
        raise RuntimeError(
            "Session manager not available. Make sure Redis is connected."
        )
    return session_manager

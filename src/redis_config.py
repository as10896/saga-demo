"""
Redis configuration and connection utilities.

This module contains Redis-specific implementation details.
The main session manager interface is in session_manager.py.
"""

import logging
import os

import redis.asyncio as redis

logger = logging.getLogger(__name__)


def get_redis_url() -> str:
    """Get Redis URL from environment or use default."""
    return os.getenv("REDIS_URL", "redis://localhost:6379")


async def create_redis_client(redis_url: str | None = None) -> redis.Redis:
    """Create and test Redis client connection."""
    if redis_url is None:
        redis_url = get_redis_url()

    client = redis.from_url(redis_url, decode_responses=False)

    # Test the connection
    await client.ping()
    logger.info(f"Successfully connected to Redis at {redis_url}")

    return client

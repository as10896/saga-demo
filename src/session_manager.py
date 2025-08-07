"""
Session manager for handling user sessions and database isolation using Redis.

This module provides session management for the Saga Pattern demo, where each user gets their own isolated database state.
This is particularly useful when deployed online, as it prevents interference between different users.

Key Concepts:
- Each user gets a unique session with isolated data (orders, inventory, balances)
- Session data is stored in Redis for persistence across server restarts
- Sessions have automatic expiration handled by Redis
- All data is serialized/deserialized automatically for Redis storage
"""

import logging
import secrets
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from pydantic import BaseModel, Field

from .database import (
    InventoryDB,
    OrdersDB,
    SagaTransactions,
    UserBalances,
    create_default_inventory_db,
    create_default_orders_db,
    create_default_saga_transactions,
    create_default_user_balances,
)

logger = logging.getLogger(__name__)


class UserSession(BaseModel):
    """
    Represents a user session with isolated database state.

    Each user session contains:
    - Unique session ID for identification
    - Creation timestamp for reference
    - Isolated database state (orders, inventory, balances, sagas)

    As a Pydantic BaseModel, this class automatically handles serialization/deserialization to/from JSON for Redis storage.
    Redis handles session expiration automatically.
    """

    session_id: str
    created_at: float

    # Isolated database state for this user - each user sees their own data
    orders_db: OrdersDB = Field(default_factory=create_default_orders_db)
    inventory_db: InventoryDB = Field(default_factory=create_default_inventory_db)
    user_balances: UserBalances = Field(default_factory=create_default_user_balances)
    saga_transactions: SagaTransactions = Field(
        default_factory=create_default_saga_transactions
    )


class AsyncSessionManager:
    """
    Manages user sessions with isolated database state using Redis.

    This class provides:
    - Session creation with unique IDs
    - Session retrieval with automatic Redis expiration
    - Redis-based persistence
    - Session data serialization/deserialization

    Usage:
        manager = AsyncSessionManager(redis_client)
        session = await manager.create_session()
        # ... use session ...
        await manager.save_session(session)
    """

    def __init__(self, redis_client: redis.Redis, session_timeout: int = 3600):
        """
        Initialize the session manager.

        Args:
            redis_client: Connected Redis client for data storage
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.redis_client: redis.Redis = redis_client
        self.session_timeout: int = session_timeout  # 1 hour default
        self.session_prefix: str = "session:"

    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for a session ID."""
        return f"{self.session_prefix}{session_id}"

    async def create_session(self) -> UserSession:
        """
        Create a new session with unique ID and default data.

        The session is automatically saved to Redis with expiration.
        """
        # Generate cryptographically secure session ID
        session_id = secrets.token_urlsafe(32)
        current_time = time.time()

        session = UserSession(session_id=session_id, created_at=current_time)

        # Store in Redis with automatic expiration using Pydantic's built-in JSON serialization
        session_key = self._get_session_key(session_id)
        await self.redis_client.setex(
            session_key, self.session_timeout, session.model_dump_json()
        )

        return session

    async def get_session(self, session_id: str) -> UserSession | None:
        """
        Retrieve a session by ID.

        Returns None if session not found or expired (Redis handles expiration automatically).
        """
        session_key = self._get_session_key(session_id)
        session_json: bytes = await self.redis_client.get(session_key)

        if not session_json:
            return None

        try:
            # Deserialize from Redis JSON using Pydantic's built-in method
            return UserSession.model_validate_json(session_json)

        except Exception:
            # If deserialization fails, delete corrupted session
            await self.redis_client.delete(session_key)
            return None

    async def get_or_create_session(self, session_id: str | None = None) -> UserSession:
        """
        Get existing session or create new one if not found.

        This is the main method used by the API to ensure every request has a valid session.
        """
        if session_id:
            session = await self.get_session(session_id)
            if session:
                return session

        # Create new session if session_id not found or invalid
        return await self.create_session()

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis."""
        session_key = self._get_session_key(session_id)
        result = await self.redis_client.delete(session_key)
        return result > 0

    async def save_session(self, session: UserSession) -> None:
        """
        Save session data to Redis.

        This method is called after saga execution to persist any changes made to the session data.
        The session expiration is reset on each save.
        """
        session_key = self._get_session_key(session.session_id)
        await self.redis_client.setex(
            session_key, self.session_timeout, session.model_dump_json()
        )

    async def reset_session_db(self, session_id: str) -> None:
        """
        Reset mock databases to their initial state for a specific session.

        This is useful for the demo to allow users to reset their data and try different scenarios.
        """
        session = await self.get_session(session_id)
        if session:
            # Reset all databases to default values
            session.orders_db = create_default_orders_db()
            session.inventory_db = create_default_inventory_db()
            session.user_balances = create_default_user_balances()
            session.saga_transactions = create_default_saga_transactions()
            # Save the reset session
            await self.save_session(session)


# ============================================================================
# Redis Integration and Lifecycle Management
# ============================================================================


async def create_session_manager_with_redis(
    redis_url: str = "redis://localhost:6379", session_timeout: int = 3600
) -> AsyncSessionManager:
    """Create a session manager with Redis backend."""
    from .redis_config import create_redis_client

    redis_client = await create_redis_client(redis_url)
    return AsyncSessionManager(redis_client, session_timeout)


@asynccontextmanager
async def session_manager_lifespan(
    session_timeout: int = 3600,
) -> AsyncGenerator[AsyncSessionManager, None]:
    """
    Manage session manager lifecycle with Redis backend.

    This context manager:
    1. Creates Redis connection and session manager on startup
    2. Yields the session manager for use
    3. Closes connections on shutdown
    """
    global _session_manager

    try:
        # Startup: Initialize session manager with Redis
        logger.info("Starting session manager...")
        from .redis_config import get_redis_url

        redis_url = get_redis_url()
        _session_manager = await create_session_manager_with_redis(
            redis_url, session_timeout
        )
        logger.info("Session manager ready")

        yield _session_manager

    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.error("Make sure Redis is running and accessible")
        raise

    except Exception as e:
        logger.error(f"Session manager startup error: {e}")
        raise

    finally:
        # Shutdown: Clean up connections
        if _session_manager:
            await _session_manager.redis_client.aclose()
            _session_manager = None
            logger.info("Session manager connections closed")


def get_session_manager() -> AsyncSessionManager:
    """
    Get the current session manager instance.

    Raises:
        RuntimeError: If session manager is not initialized
    """
    if not _session_manager:
        raise RuntimeError(
            "Session manager not available. Make sure it's initialized in lifespan."
        )
    return _session_manager


# Global session manager instance (will be initialized in lifespan)
_session_manager: AsyncSessionManager | None = None

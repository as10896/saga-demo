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

import secrets
import time
from dataclasses import dataclass, field

import redis.asyncio as redis
from pydantic import BaseModel

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
from .models import Order, SagaTransaction


class SessionData(BaseModel):
    """
    Serializable session data for Redis storage.

    This model converts the complex session data into a format that can be stored in Redis as JSON.
    Pydantic handles the serialization automatically.
    """

    session_id: str
    created_at: float

    # Store serialized versions of complex objects
    orders_db: dict[str, dict]  # Serialized Order objects
    inventory_db: InventoryDB  # Simple dict, no serialization needed
    user_balances: UserBalances  # Simple dict, no serialization needed
    saga_transactions: dict[str, dict]  # Serialized SagaTransaction objects


@dataclass
class UserSession:
    """
    Represents a user session with isolated database state.

    Each user session contains:
    - Unique session ID for identification
    - Creation timestamp for reference
    - Isolated database state (orders, inventory, balances, sagas)

    The session can be converted to/from Redis-storable format automatically.
    Redis handles session expiration automatically, so no manual timeout tracking needed.
    """

    session_id: str
    created_at: float

    # Isolated database state for this user - each user sees their own data
    orders_db: OrdersDB = field(default_factory=create_default_orders_db)
    inventory_db: InventoryDB = field(default_factory=create_default_inventory_db)
    user_balances: UserBalances = field(default_factory=create_default_user_balances)
    saga_transactions: SagaTransactions = field(
        default_factory=create_default_saga_transactions
    )

    def to_session_data(self) -> SessionData:
        """
        Convert session to Redis-storable format.

        This method serializes complex objects (Orders, SagaTransactions) to dictionaries that can be stored as JSON in Redis.
        """
        return SessionData(
            session_id=self.session_id,
            created_at=self.created_at,
            # Convert Pydantic models to dicts for Redis storage
            orders_db={k: v.model_dump() for k, v in self.orders_db.items()},
            inventory_db=self.inventory_db,
            user_balances=self.user_balances,
            saga_transactions={
                k: v.model_dump() for k, v in self.saga_transactions.items()
            },
        )

    @classmethod
    def from_session_data(cls, data: SessionData) -> "UserSession":
        """
        Create UserSession from Redis data.

        This method deserializes the stored JSON data back into proper Python objects with full type safety.
        """
        return cls(
            session_id=data.session_id,
            created_at=data.created_at,
            # Convert dicts back to Pydantic models
            orders_db={k: Order(**v) for k, v in data.orders_db.items()},
            inventory_db=data.inventory_db,
            user_balances=data.user_balances,
            saga_transactions={
                k: SagaTransaction(**v) for k, v in data.saga_transactions.items()
            },
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

        # Store in Redis with automatic expiration
        session_key = self._get_session_key(session_id)
        session_data = session.to_session_data()
        await self.redis_client.setex(
            session_key, self.session_timeout, session_data.model_dump_json()
        )

        return session

    async def get_session(self, session_id: str) -> UserSession | None:
        """
        Retrieve a session by ID.

        Returns None if session not found or expired (Redis handles expiration automatically).
        """
        session_key = self._get_session_key(session_id)
        session_json = await self.redis_client.get(session_key)

        if not session_json:
            return None

        try:
            # Deserialize from Redis JSON
            session_data = SessionData.model_validate_json(session_json)
            return UserSession.from_session_data(session_data)

        except Exception:
            # If deserialization fails, delete corrupted session
            await self.redis_client.delete(session_key)
            return None

    async def get_or_create_session(self, session_id: str | None = None) -> UserSession:
        """
        Get existing session or create new one if not found.

        This is the main method used by the API to ensure every request
        has a valid session.
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

        This method is called after saga execution to persist any changes
        made to the session data. The session expiration is reset on each save.
        """
        session_key = self._get_session_key(session.session_id)
        session_data = session.to_session_data()
        await self.redis_client.setex(
            session_key, self.session_timeout, session_data.model_dump_json()
        )

    async def reset_session_db(self, session_id: str) -> None:
        """
        Reset mock databases to their initial state for a specific session.

        This is useful for the demo to allow users to reset their data
        and try different scenarios.
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


# Global async session manager instance (will be initialized in lifespan)
async_session_manager: AsyncSessionManager | None = None

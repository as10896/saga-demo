"""
Session manager for handling user sessions and database isolation.
This is useful when deployed online, as each user receives their own isolated database state, preventing interference between users.
"""

import secrets
import time
from dataclasses import dataclass, field
from typing import TypeAlias

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

SessionId: TypeAlias = str


@dataclass
class UserSession:
    """Represents a user session with isolated database state"""

    session_id: SessionId
    created_at: float
    last_accessed: float

    # Isolated database state for this user
    orders_db: OrdersDB = field(default_factory=create_default_orders_db)
    inventory_db: InventoryDB = field(default_factory=create_default_inventory_db)
    user_balances: UserBalances = field(default_factory=create_default_user_balances)
    saga_transactions: SagaTransactions = field(
        default_factory=create_default_saga_transactions
    )


class SessionManager:
    """
    Manages user sessions with isolated database state for each user
    """

    def __init__(self, session_timeout: int = 3600):  # 1 hour default
        self.sessions: dict[SessionId, UserSession] = {}
        self.session_timeout: int = session_timeout

    def create_session(self) -> UserSession:
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)
        current_time = time.time()
        session = UserSession(
            session_id=session_id,
            created_at=current_time,
            last_accessed=current_time,
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: SessionId) -> UserSession | None:
        """Get a session by ID, updating last accessed time"""
        session = self.sessions.get(session_id)
        if session:
            # Check if session has expired
            current_time = time.time()
            if current_time - session.last_accessed > self.session_timeout:
                del self.sessions[session_id]
                return None

            session.last_accessed = current_time
            return session
        return None

    def get_or_create_session(self, session_id: SessionId | None = None) -> UserSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session

        # Create new session if session_id not found
        return self.create_session()

    def delete_session(self, session_id: SessionId) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def reset_session_db(self, session_id: str) -> None:
        """Reset mock databases to their initial state for a specific session."""
        session = session_manager.get_session(session_id)
        if session:
            session.orders_db = create_default_orders_db()
            session.inventory_db = create_default_inventory_db()
            session.user_balances = create_default_user_balances()
            session.saga_transactions = create_default_saga_transactions()


# Global session manager instance
session_manager = SessionManager()

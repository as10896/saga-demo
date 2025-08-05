"""
FastAPI dependency injection functions.

This module contains all the dependency injection logic used by API endpoints,
making it easy to understand how sessions and other dependencies work.
"""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status

from .redis_config import get_session_manager
from .session_manager import UserSession


async def get_user_session(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None,
) -> UserSession:
    """
    Get or create a user session with isolated database state.

    This dependency:
    1. Extracts session ID from cookies (if present)
    2. Gets existing session or creates a new one
    3. Sets/updates the session cookie
    4. Returns the user session with isolated data

    Args:
        response: FastAPI response object for setting cookies
        session_id: Session ID from cookie (optional)

    Returns:
        UserSession: Session with isolated database state

    Raises:
        HTTPException: If session manager is not available
    """
    try:
        session_manager = get_session_manager()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )

    # Get existing session or create new one
    session = await session_manager.get_or_create_session(session_id)

    # Set/update session cookie
    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        max_age=3600,  # 1 hour
    )

    return session


# Type alias for cleaner endpoint signatures
SessionDep = Annotated[UserSession, Depends(get_user_session)]

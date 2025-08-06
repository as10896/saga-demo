"""
Main FastAPI application with Saga Pattern demonstration endpoints.
"""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import schemas
from .dependencies import SessionDep
from .models import Order
from .orchestrator import SagaOrchestrator
from .redis_config import get_session_manager, redis_lifespan
from .utils import url_for

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

description = """
A demonstration of the Saga Pattern for distributed transactions.

This API showcases how to implement saga orchestration for order processing,
including validation, inventory management, payment processing, and shipping.

## Features

* **Order Management**: Create and retrieve orders
* **Saga Transactions**: Monitor distributed transaction progress
* **Inventory Tracking**: Check product availability
* **User Balances**: Monitor user account balances
* **Compensation Logic**: Automatic rollback on failures
* **Session Isolation**: Each user has isolated database state
* **Redis Persistence**: Session data persists across server restarts

## How it works

1. Create an order using the `/orders` endpoint
2. The system automatically executes a saga with these steps:
    - Validate order
    - Reserve inventory
    - Process payment
    - Ship order
3. If any step fails, compensation actions are executed in reverse order
4. Monitor progress using the `/sagas/{saga_id}` endpoint
5. Each user session maintains isolated database state stored in Redis
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles Redis connection and cleanup using the redis_config module.
    """
    async with redis_lifespan():
        yield


# Initialize FastAPI app
app = FastAPI(
    title="Saga Pattern Demo API",
    version="1.0.0",
    description=description,
    lifespan=lifespan,
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")
templates.env.globals["url_for"] = url_for

# Initialize saga orchestrator
saga_orchestrator = SagaOrchestrator()


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.post(
    "/orders",
    response_class=ORJSONResponse,
    response_model=schemas.CreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order and execute the saga pattern transaction.",
    tags=["Orders"],
)
async def create_order(
    order_data: schemas.CreateOrderRequest,
    session: SessionDep,
):
    """Create a new order and execute saga transaction."""
    # Create the order
    order = Order(
        id=str(uuid.uuid4()),
        user_id=order_data.user_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        amount=order_data.amount,
    )

    # Add order to session
    session.orders_db[order.id] = order

    # Execute saga with session manager
    session_manager = get_session_manager()
    saga = await saga_orchestrator.execute_saga(
        order, session.session_id, session_manager
    )

    return {
        "order_id": order.id,
        "saga_id": saga.id,
        "status": saga.status,
        "steps": [
            {"name": step.name, "status": step.status.value} for step in saga.steps
        ],
    }


@app.get(
    "/orders/{order_id}",
    response_class=ORJSONResponse,
    response_model=schemas.OrderResponse,
    responses={404: {"model": schemas.ErrorResponse, "description": "Order not found"}},
    summary="Get order details",
    description="Retrieve detailed information about a specific order by its ID.",
    tags=["Orders"],
)
async def get_order(order_id: str, session: SessionDep):
    """Get order details by ID."""
    if order_id not in session.orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return session.orders_db[order_id]


@app.get(
    "/orders",
    response_class=ORJSONResponse,
    response_model=list[schemas.OrderResponse],
    summary="List all orders",
    description="Retrieve a list of all orders, most recent first.",
    tags=["Orders"],
)
async def list_orders(session: SessionDep):
    """List all orders, most recent first."""
    orders = list(reversed(session.orders_db.values()))
    return orders


@app.get(
    "/sagas/{saga_id}",
    response_class=ORJSONResponse,
    response_model=schemas.SagaTransactionResponse,
    responses={404: {"model": schemas.ErrorResponse, "description": "Saga not found"}},
    summary="Get saga transaction details",
    description="Retrieve detailed information about a specific saga transaction.",
    tags=["Saga Transactions"],
)
async def get_saga(saga_id: str, session: SessionDep):
    """Get saga transaction details by ID."""
    if saga_id not in session.saga_transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saga not found"
        )

    return session.saga_transactions[saga_id]


@app.get(
    "/inventory",
    response_class=ORJSONResponse,
    response_model=schemas.InventoryResponse,
    summary="Get current inventory levels",
    description="Retrieve the current inventory levels for all available products.",
    tags=["Session Info"],
)
async def get_inventory(session: SessionDep):
    """Get current inventory levels."""
    return {"inventory": session.inventory_db}


@app.get(
    "/balances",
    response_class=ORJSONResponse,
    response_model=schemas.BalancesResponse,
    summary="Get user balances",
    description="Retrieve the current balance for all users in the system.",
    tags=["Session Info"],
)
async def get_balances(session: SessionDep):
    """Get user balances."""
    return {"balances": session.user_balances}


@app.post(
    "/reset",
    response_class=ORJSONResponse,
    response_model=schemas.ResetResponse,
    summary="Reset mock database",
    description="Reset all mock data (orders, inventory, balances, sagas) to initial state.",
    tags=["Session Info"],
)
async def reset_db(session: SessionDep):
    """Reset mock database to initial state."""
    session_manager = get_session_manager()
    await session_manager.reset_session_db(session.session_id)
    return {"message": "Mock database reset to initial state."}


@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Saga Pattern Demo UI",
    description="Interactive web interface for the Saga Pattern demonstration.",
    tags=["UI"],
)
async def root(request: Request, session: SessionDep):
    """Serve the main HTML UI using Jinja2 template"""
    response = templates.TemplateResponse(request=request, name="index.html")

    # Manually set the session cookie since TemplateResponse doesn't inherit from dependency
    # Refs:
    # - https://stackoverflow.com/questions/77008824/how-to-set-cookies-on-jinja2-templateresponse-in-fastapi
    # - https://fastapi.tiangolo.com/advanced/response-cookies/#return-a-response-directly
    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        max_age=3600,  # 1 hour
    )

    return response


@app.get(
    "/health",
    response_class=ORJSONResponse,
    response_model=schemas.HealthResponse,
    summary="Health check",
    description="Check the health status of the API service.",
    tags=["System"],
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

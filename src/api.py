import logging
import uuid
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import schemas
from .models import Order
from .orchestrator import SagaOrchestrator
from .session_manager import UserSession, session_manager

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

## How it works

1. Create an order using the `/orders` endpoint
2. The system automatically executes a saga with these steps:
    - Validate order
    - Reserve inventory
    - Process payment
    - Ship order
3. If any step fails, compensation actions are executed in reverse order
4. Monitor progress using the `/sagas/{saga_id}` endpoint
5. Each user session maintains isolated database state
"""

app = FastAPI(
    title="Saga Pattern Demo API",
    version="1.0.0",
    description=description,
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="src/templates")

# Initialize orchestrator
saga_orchestrator = SagaOrchestrator()


def get_session(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None,
) -> UserSession:
    """Extracts the session ID from the cookie and gets or creates a session if not specified or if the session has expired."""
    session = session_manager.get_or_create_session(session_id)
    response.set_cookie(
        key="session_id", value=session.session_id, httponly=True, max_age=3600
    )
    return session


@app.post(
    "/orders",
    response_class=ORJSONResponse,
    response_model=schemas.CreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order and execute the saga pattern transaction to process it through all required steps including validation, inventory reservation, payment processing, and shipping.",
    tags=["Orders"],
)
async def create_order(
    order_data: schemas.CreateOrderRequest,
    session: Annotated[UserSession, Depends(get_session)],
):
    """Create a new order and execute saga"""
    orders_db = session.orders_db

    order = Order(
        id=str(uuid.uuid4()),
        user_id=order_data.user_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        amount=order_data.amount,
    )

    orders_db[order.id] = order

    # Execute saga
    saga = await saga_orchestrator.execute_saga(order, session.session_id)

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
    responses={
        404: {"model": schemas.ErrorResponse, "description": "Order not found"},
    },
    summary="Get order details",
    description="Retrieve detailed information about a specific order by its ID.",
    tags=["Orders"],
)
async def get_order(
    order_id: str,
    session: Annotated[UserSession, Depends(get_session)],
):
    """Get order details"""
    orders_db = session.orders_db

    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return orders_db[order_id]


@app.get(
    "/orders",
    response_class=ORJSONResponse,
    response_model=list[schemas.OrderResponse],
    summary="List all orders",
    description="Retrieve a list of all orders, most recent first.",
    tags=["Orders"],
)
async def list_orders(session: Annotated[UserSession, Depends(get_session)]):
    """List all orders, most recent first"""
    orders_db = session.orders_db

    orders = list(reversed(orders_db.values()))
    return orders


@app.get(
    "/sagas/{saga_id}",
    response_class=ORJSONResponse,
    response_model=schemas.SagaTransactionResponse,
    responses={
        404: {"model": schemas.ErrorResponse, "description": "Saga not found"},
    },
    summary="Get saga transaction details",
    description="Retrieve detailed information about a specific saga transaction including all steps and their current status.",
    tags=["Saga Transactions"],
)
async def get_saga(saga_id: str, session: Annotated[UserSession, Depends(get_session)]):
    """Get saga transaction details"""
    saga_transactions = session.saga_transactions

    if saga_id not in saga_transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saga not found"
        )

    return saga_transactions[saga_id]


@app.get(
    "/inventory",
    response_class=ORJSONResponse,
    response_model=schemas.InventoryResponse,
    summary="Get current inventory levels",
    description="Retrieve the current inventory levels for all available products.",
    tags=["Session Info"],
)
async def get_inventory(session: Annotated[UserSession, Depends(get_session)]):
    """Get current inventory levels"""
    inventory_db = session.inventory_db

    return {"inventory": inventory_db}


@app.get(
    "/balances",
    response_class=ORJSONResponse,
    response_model=schemas.BalancesResponse,
    summary="Get user balances",
    description="Retrieve the current balance for all users in the system.",
    tags=["Session Info"],
)
async def get_balances(session: Annotated[UserSession, Depends(get_session)]):
    """Get user balances"""
    user_balances = session.user_balances

    return {"balances": user_balances}


@app.post(
    "/reset",
    response_class=ORJSONResponse,
    response_model=schemas.ResetResponse,
    summary="Reset mock database",
    description="Reset all mock data (orders, inventory, balances, sagas) to initial state.",
    tags=["Session Info"],
)
async def reset_db(session: Annotated[UserSession, Depends(get_session)]):
    session_manager.reset_session_db(session.session_id)
    return {"message": "Mock database reset to initial state."}


@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Saga Pattern Demo UI",
    description="Saga Pattern Demo UI",
    tags=["Session Info"],
)
async def root(request: Request, session: Annotated[UserSession, Depends(get_session)]):
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
    """Health check endpoint"""
    return {"status": "healthy"}

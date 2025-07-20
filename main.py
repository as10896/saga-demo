import logging
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.database import inventory_db, orders_db, saga_transactions, user_balances
from src.models import Order
from src.orchestrator import SagaOrchestrator
from src.schemas import (
    BalancesResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    ErrorResponse,
    HealthResponse,
    InventoryResponse,
    OrderResponse,
    RootResponse,
    SagaTransactionResponse,
)

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

## How it works

1. Create an order using the `/orders` endpoint
2. The system automatically executes a saga with these steps:
    - Validate order
    - Reserve inventory
    - Process payment
    - Ship order
3. If any step fails, compensation actions are executed in reverse order
4. Monitor progress using the `/sagas/{saga_id}` endpoint
"""

app = FastAPI(
    title="Saga Pattern Demo API",
    version="1.0.0",
    description=description,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize orchestrator
saga_orchestrator = SagaOrchestrator()


@app.post(
    "/orders",
    response_model=CreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid order data"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    summary="Create a new order",
    description="Create a new order and execute the saga pattern transaction to process it through all required steps including validation, inventory reservation, payment processing, and shipping.",
    tags=["Orders"],
)
async def create_order(order_data: CreateOrderRequest):
    """Create a new order and execute saga"""
    order = Order(
        id=str(uuid.uuid4()),
        user_id=order_data.user_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        amount=order_data.amount,
    )

    orders_db[order.id] = order

    # Execute saga
    saga = await saga_orchestrator.execute_saga(order)

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
    response_model=OrderResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Order not found"},
    },
    summary="Get order details",
    description="Retrieve detailed information about a specific order by its ID.",
    tags=["Orders"],
)
async def get_order(order_id: str):
    """Get order details"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return orders_db[order_id]


@app.get(
    "/sagas/{saga_id}",
    response_model=SagaTransactionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Saga not found"},
    },
    summary="Get saga transaction details",
    description="Retrieve detailed information about a specific saga transaction including all steps and their current status.",
    tags=["Saga Transactions"],
)
async def get_saga(saga_id: str):
    """Get saga transaction details"""
    if saga_id not in saga_transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saga not found"
        )

    return saga_transactions[saga_id]


@app.get(
    "/inventory",
    response_model=InventoryResponse,
    summary="Get current inventory levels",
    description="Retrieve the current inventory levels for all available products.",
    tags=["System Info"],
)
async def get_inventory():
    """Get current inventory levels"""
    return {"inventory": inventory_db}


@app.get(
    "/balances",
    response_model=BalancesResponse,
    summary="Get user balances",
    description="Retrieve the current balance for all users in the system.",
    tags=["System Info"],
)
async def get_balances():
    """Get user balances"""
    return {"balances": user_balances}


@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Root endpoint",
    description="Saga Pattern Demo UI",
    tags=["System"],
)
async def root(request: Request):
    """Serve the main HTML UI using Jinja2 template"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get(
    "/api",
    response_model=RootResponse,
    summary="API root endpoint",
    description="Welcome endpoint for the Saga Pattern Demo API.",
    tags=["System"],
)
async def api_root():
    return {"message": "Saga Pattern Demo API"}


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API service.",
    tags=["System"],
)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("Starting Saga Pattern Demo...")
    print("Available products:", list(inventory_db.keys()))
    print("User balances:", user_balances)

    uvicorn.run(app, host="0.0.0.0", port=8000)

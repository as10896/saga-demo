import logging
import uuid

from fastapi import FastAPI, HTTPException

from src.database import inventory_db, orders_db, user_balances
from src.models import Order, OrderStatus
from src.orchestrator import SagaOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Saga Pattern Demo", version="1.0.0")

# Initialize orchestrator
saga_orchestrator = SagaOrchestrator()


@app.post("/orders")
async def create_order(order_data: dict):
    """Create a new order and execute saga"""
    order = Order(
        id=str(uuid.uuid4()),
        user_id=order_data["user_id"],
        product_id=order_data["product_id"],
        quantity=order_data["quantity"],
        amount=order_data["amount"],
    )

    orders_db[order.id] = order

    # Execute saga
    saga = await saga_orchestrator.execute_saga(order)

    return {
        "order_id": order.id,
        "saga_id": saga.id,
        "status": saga.status,
        "steps": saga.steps,
    }


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")

    return orders_db[order_id]


@app.get("/sagas/{saga_id}")
async def get_saga(saga_id: str):
    """Get saga transaction details"""
    from src.database import saga_transactions

    if saga_id not in saga_transactions:
        raise HTTPException(status_code=404, detail="Saga not found")

    return saga_transactions[saga_id]


@app.get("/inventory")
async def get_inventory():
    """Get current inventory levels"""
    return inventory_db


@app.get("/balances")
async def get_balances():
    """Get user balances"""
    return user_balances


@app.get("/")
async def root():
    return {"message": "Saga Pattern Demo API"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("Starting Saga Pattern Demo...")
    print("Available products:", list(inventory_db.keys()))
    print("User balances:", user_balances)

    uvicorn.run(app, host="0.0.0.0", port=8000)

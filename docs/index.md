# Saga Pattern Demo with FastAPI

A comprehensive implementation of the **Saga Pattern** for handling distributed transactions in microservices architecture, built with Python and FastAPI.

## 📋 Overview

This project demonstrates how to implement the Saga pattern to maintain data consistency across multiple services without using traditional ACID transactions. The example simulates an e-commerce order processing system with multiple steps that can succeed or fail independently.

## 🏗️ What is the Saga Pattern?

The Saga pattern is a design pattern for managing distributed transactions across multiple microservices. Instead of using a single database transaction, it breaks down a business transaction into a series of smaller, local transactions. If any step fails, the pattern executes compensating transactions to undo the completed steps.

### Key Benefits:

- **Data Consistency**: Maintains consistency across distributed services
- **Fault Tolerance**: Handles failures gracefully with automatic compensation
- **Scalability**: Works well with microservices architecture
- **Observability**: Provides clear audit trail of transaction steps

## 🚀 Features

- **Orchestrator-based Saga**: Centralized coordination of transaction steps
- **Automatic Compensation**: Failed transactions trigger compensating actions
- **Step Tracking**: Detailed status tracking for each transaction step
- **REST API**: Complete FastAPI implementation with endpoints
- **Mock Services**: Simulated inventory, payment, and shipping services
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🛠️ Installation & Setup

### Prerequisites

- [Docker Compose](https://docs.docker.com/compose/)

### Installation Steps

1. **Build the image**
   ```bash
   COMPOSE_BAKE=true docker compose build
   ```

2. **Run the application:**
   ```bash
   docker compose up
   ```

3. **Access the application:**
    - **Interactive UI**: [http://localhost:8000](http://localhost:8000)
    - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
    - **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📊 API Endpoints

### Core Endpoints

| Method | Endpoint             | Description                         |
| ------ | -------------------- | ----------------------------------- |
| `POST` | `/orders`            | Create a new order and execute saga |
| `GET`  | `/orders/{order_id}` | Get order details                   |
| `GET`  | `/sagas/{saga_id}`   | Get saga transaction details        |
| `GET`  | `/inventory`         | Get current inventory levels        |
| `GET`  | `/balances`          | Get user account balances           |
| `GET`  | `/health`            | Health check endpoint               |
| `POST` | `/reset`             | Reset all mock data to initial state|

### Interactive API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📚 Saga Workflow Diagrams
For complete workflow diagrams and visual representations of the Saga pattern implementation, please refer to the **[Saga Flowchart](flowchart.md)**.

## 🧪 Testing the Saga Pattern

### Test Data

The application comes with pre-loaded test data:

**Products:**

- `product_1`: 100 units
- `product_2`: 50 units
- `product_3`: 25 units

**Users:**

- `user_1`: $1000 balance
- `user_2`: $500 balance
- `user_3`: $200 balance

### Example Test Cases

#### 1. Successful Order (Happy Path)

```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_1",
    "product_id": "product_1",
    "quantity": 2,
    "amount": 100.0
  }'
```

**Expected Result:** All steps complete successfully, order status = "completed"

#### 2. Insufficient Funds (Payment Failure)

```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_3",
    "product_id": "product_1",
    "quantity": 1,
    "amount": 500.0
  }'
```

**Expected Result:** Payment fails, inventory is automatically released, order status = "failed"

#### 3. Shipping Failure

```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_3",
    "product_id": "product_1",
    "quantity": 1,
    "amount": 50.0
  }'
```

**Expected Result:** Shipping fails (simulated), payment is refunded and inventory released

#### 4. Check System State

```bash
# Check inventory levels
curl "http://localhost:8000/inventory"

# Check user balances
curl "http://localhost:8000/balances"

# Get specific order details
curl "http://localhost:8000/orders/{order_id}"
```

### Resetting Demo Data

You can reset all mock data (orders, inventory, balances, and saga transactions) to their initial state using the following endpoint:

```bash
curl -X POST "http://localhost:8000/reset"
```

**Expected Result:** All demo data is restored to its original state. This is useful for quickly resetting the environment during testing or demonstrations.

## 🔄 Saga Workflow

The saga executes the following steps in sequence:

1. **Validate Order** → Check quantity, amount, user existence
2. **Reserve Inventory** → Reduce available stock
3. **Process Payment** → Deduct amount from user balance
4. **Ship Order** → Create shipment (simulated)

### Compensation Flow

If any step fails, compensating actions execute in **reverse order**:

- **Cancel Shipment** ← Undo shipping
- **Refund Payment** ← Add money back to user
- **Release Inventory** ← Add stock back
- **No compensation** ← Validation doesn't need compensation

## 📈 Monitoring & Observability

### Logging

The application provides comprehensive logging at INFO level:

```bash
INFO:orchestrator:Starting saga abc-123 for order def-456
INFO:services:Reserved 2 units of product_1
INFO:services:Processed payment of $100.0 for user_1
INFO:orchestrator:Saga abc-123 completed successfully
```

### Transaction Status Tracking

Each saga maintains detailed step-by-step status:

```json
{
  "saga_id": "abc-123",
  "order_id": "def-456",
  "status": "completed",
  "steps": [
    { "name": "validate_order", "status": "completed" },
    { "name": "reserve_inventory", "status": "completed" },
    { "name": "process_payment", "status": "completed" },
    { "name": "ship_order", "status": "completed" }
  ]
}
```

## 🏛️ Architecture Components

### Services Layer

- **ValidationService**: Order validation logic
- **InventoryService**: Stock management
- **PaymentService**: Payment processing
- **ShippingService**: Order fulfillment

### Orchestrator

- **SagaOrchestrator**: Coordinates step execution and compensation
- Maintains transaction state and handles failures

### Data Layer

- **Mock Database**: In-memory storage for demo purposes
- **Models**: Pydantic schemas for type safety

## 🔧 Extending the Demo

### Adding New Saga Steps

1. Create a new service in `services.py`
2. Add step configuration to orchestrator's `steps` array
3. Implement both action and compensation methods

### Adding Real Services

Replace mock implementations with actual service calls:

```python
# src/services.py
class PaymentService:
    @staticmethod
    async def process_payment(order: Order):
        # Call actual payment gateway
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://payment-service/charge",
                json={"amount": order.amount, "user_id": order.user_id}
            )
```

### Database Integration

Replace mock database with real database:

```python
# src/database.py
import asyncpg

async def get_order(order_id: str) -> Order:
    conn = await asyncpg.connect("postgresql://...")
    # Implement actual database queries
```

## 📚 Learn More

### Additional Resources

- [Microservices.io - Saga Pattern](https://microservices.io/patterns/data/saga.html)

### Related Patterns

- **Event Sourcing**: Store events instead of current state
- **CQRS**: Separate read and write operations
- **Circuit Breaker**: Handle service failures gracefully

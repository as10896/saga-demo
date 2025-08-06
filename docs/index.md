# Saga Pattern Demo with FastAPI

A comprehensive implementation of the **Saga Pattern** for handling distributed transactions in microservices architecture, built with Python and FastAPI.

A live version is available <a href="https://involved-aubry-as10896-270cd4f4.koyeb.app/" target="_blank">here</a>.

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
- **Interactive Web UI**: User-friendly interface for testing saga workflows
- **Mock Services**: Simulated inventory, payment, and shipping services
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🛠️ Installation & Setup

### Prerequisites

- <a href="https://docs.docker.com/get-docker/" target="_blank">Docker</a> and <a href="https://docs.docker.com/compose/" target="_blank">Docker Compose</a>

### Installation Steps

1. **Build the image:**
  ```bash
  COMPOSE_BAKE=true docker compose build
  ```

2. **Start the application:**
  ```bash
  docker compose up
  ```

3. **Access the application:**
    - **Interactive Web UI**: <a href="http://localhost:8000" target="_blank">http://localhost:8000</a>
    - **Swagger UI Documentation**: <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a>


## 📊 API Endpoints

### Core Endpoints

| Method | Endpoint             | Description                          |
| ------ | -------------------- | ------------------------------------ |
| `POST` | `/orders`            | Create a new order and execute saga  |
| `GET`  | `/orders`            | List all orders (most recent first)  |
| `GET`  | `/orders/{order_id}` | Get order details                    |
| `GET`  | `/sagas/{saga_id}`   | Get saga transaction details         |
| `GET`  | `/inventory`         | Get current inventory levels         |
| `GET`  | `/balances`          | Get user account balances            |
| `POST` | `/reset`             | Reset all mock data to initial state |


## 📚 Saga Workflow Diagrams

For complete workflow diagrams and visual representations of the Saga pattern implementation, please refer to the **[Saga Workflow](workflow.md)**.

## 🧪 Testing the Saga Pattern

### Test Data

Each user session starts with pre-loaded test data:

**Products:**

- `product_1`: 100 units
- `product_2`: 50 units
- `product_3`: 25 units

**Users:**

- `user_1`: $1000 balance
- `user_2`: $500 balance
- `user_3`: $200 balance

### Test Scenarios

1. Successful Order (Happy Path)
    - Create an order with sufficient inventory and funds (e.g., `user_1`, `product_1`, `quantity=2`, `amount=$100`).
    - **Expected Result:** All steps complete successfully, order status = `"completed"`

2. Insufficient Inventory
    - Create an order with quantity exceeding available inventory (e.g., `user_1`, `product_1`, `quantity=200`).
    - **Expected Result:** Inventory step fails, validation is compensated, order status = `"failed"`

3. Insufficient Funds
    - Create an order where the user doesn't have enough balance (e.g., `user_3`, `product_1`, `amount=$500`).
    - **Expected Result:** Payment fails, inventory is automatically released, order status = `"failed"`

4. Shipping Failure
    - For errors that are not caused by insufficient inventory or insufficient funds (i.e., unknown or unexpected failures), we use a shipping failure as an example in this test case.
    - <mark>To simplify the demo, we simulate this failure by hardcoding the logic: if the order is placed by user_3, and both the product inventory and the user’s balance are sufficient, we intentionally force an error at the final shipping step.</mark>
    - **Expected Result:** Shipping fails, payment is refunded and inventory released, order status = `"failed"`


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
- **Compensate Validation** ← Mark as compensated (no actual action needed)

### Step Status Tracking

Each step can have one of these statuses:

- `pending`: Not yet started
- `completed`: Successfully executed
- `failed`: Execution failed
- `compensated`: Successfully compensated after failure

## 📈 Monitoring & Observability

### Logging

The application provides comprehensive logging for saga execution:

```bash
INFO:src.orchestrator:🚀 Starting saga abc-123 for order def-456
INFO:src.services:✅ Reserved 2 units of product_1 for user_1
INFO:src.services:💰 Processed payment of $100.0 for user_1
INFO:src.orchestrator:✅ Saga abc-123 completed successfully
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
- **ShippingService**: Order fulfillment simulation

### Orchestrator

- **SagaOrchestrator**: Coordinates step execution and compensation
- **Transaction State**: Maintains saga status and step details
- **Error Handling**: Manages failures and triggers compensation

### Data Layer

- **Mock Databases**: In-memory storage for demo purposes
- **Pydantic Models**: Type-safe data validation

## 🔧 Extending the Demo

### Adding New Saga Steps

1. **Create service methods** in `src/services.py`:

      ```python
      class NewService:
          @staticmethod
          async def execute_action(order: Order, session: UserSession):
              # Implementation
              pass

          @staticmethod
          async def compensate_action(order: Order, session: UserSession):
              # Compensation logic
              pass
      ```

2. **Add to orchestrator** in `src/orchestrator.py`:
    ```python
    self.steps = [
        # ... existing steps ...
        {
            "name": "new_step",
            "action": NewService.execute_action,
            "compensate": NewService.compensate_action,
        },
    ]
    ```

### Adding Real Services

Replace mock implementations with actual service calls:

```python
# src/services.py
class PaymentService:
    @staticmethod
    async def process_payment(order: Order, session: UserSession):
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

- <a href="https://microservices.io/patterns/data/saga.html" target="_blank">Microservices.io - Saga Pattern</a>

### Related Patterns

- **Event Sourcing**: Store events instead of current state
- **CQRS**: Separate read and write operations
- **Circuit Breaker**: Handle service failures gracefully
- **Outbox Pattern**: Reliable event publishing

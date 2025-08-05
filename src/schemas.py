"""
Pydantic schemas for FastAPI request and response models
"""

from pydantic import BaseModel, Field

from .models import OrderStatus, StepStatus


class SagaStepResponse(BaseModel):
    """Response schema for saga step details"""

    name: str = Field(..., description="Name of the saga step")
    status: StepStatus = Field(..., description="Current status of the step")
    error_message: str | None = Field(
        None, description="Error message if the step failed"
    )


# Request Schemas
class CreateOrderRequest(BaseModel):
    """Request schema for creating a new order"""

    user_id: str = Field(
        ..., description="ID of the user placing the order", example="user_1"
    )
    product_id: str = Field(
        ..., description="ID of the product being ordered", example="product_1"
    )
    quantity: int = Field(..., gt=0, description="Quantity of the product", example=2)
    amount: float = Field(
        ..., gt=0, description="Total amount for the order", example=99.99
    )


# Response Schemas
class CreateOrderResponse(BaseModel):
    """Response schema for order creation"""

    order_id: str = Field(
        ...,
        description="Unique identifier for the order",
        example="550e8400-e29b-41d4-a716-446655440000",
    )
    saga_id: str = Field(
        ...,
        description="Unique identifier for the saga transaction",
        example="550e8400-e29b-41d4-a716-446655440001",
    )
    status: OrderStatus = Field(
        ..., description="Current status of the saga transaction"
    )
    steps: list[SagaStepResponse] = Field(
        ..., description="List of saga steps with their status"
    )


class OrderResponse(BaseModel):
    """Response schema for order details"""

    id: str = Field(..., description="Unique identifier for the order")
    user_id: str = Field(..., description="ID of the user who placed the order")
    product_id: str = Field(..., description="ID of the product ordered")
    quantity: int = Field(..., description="Quantity of the product")
    amount: float = Field(..., description="Total amount for the order")
    status: OrderStatus = Field(..., description="Current status of the order")


class SagaTransactionResponse(BaseModel):
    """Response schema for saga transaction details"""

    id: str = Field(..., description="Unique identifier for the saga transaction")
    order_id: str = Field(..., description="ID of the associated order")
    steps: list[SagaStepResponse] = Field(
        ..., description="List of saga steps with their details"
    )
    status: OrderStatus = Field(
        ..., description="Current status of the saga transaction"
    )


class InventoryResponse(BaseModel):
    """Response schema for inventory levels"""

    inventory: dict[str, int] = Field(
        ..., description="Product ID to available quantity mapping"
    )


class BalancesResponse(BaseModel):
    """Response schema for user balances"""

    balances: dict[str, float] = Field(..., description="User ID to balance mapping")


class HealthResponse(BaseModel):
    """Response schema for health check"""

    status: str = Field(
        ..., description="Health status of the service", example="healthy"
    )


class ResetResponse(BaseModel):
    """Response schema for reset endpoint"""

    message: str = Field(
        ...,
        description="Mock DB reset message",
        example="Mock database reset to initial state.",
    )


# Error Response Schemas
class ErrorResponse(BaseModel):
    """Standard error response schema"""

    detail: str = Field(..., description="Error message describing what went wrong")

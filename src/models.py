"""
Data models for the Saga Pattern demo
"""

from enum import Enum

from pydantic import BaseModel


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"


class StepStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


class Order(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int
    amount: float
    status: OrderStatus = OrderStatus.PENDING


class SagaStep(BaseModel):
    name: str
    status: StepStatus = StepStatus.PENDING
    error_message: str | None = None


class SagaTransaction(BaseModel):
    id: str
    order_id: str
    steps: list[SagaStep]
    status: OrderStatus = OrderStatus.PENDING

"""
Mock database implementations for the Saga Pattern demo
"""

from .models import Order, SagaTransaction

# Mock databases
orders_db: dict[str, Order] = {}

inventory_db: dict[str, int] = {"product_1": 100, "product_2": 50, "product_3": 25}

user_balances: dict[str, float] = {"user_1": 1000.0, "user_2": 500.0, "user_3": 200.0}

saga_transactions: dict[str, SagaTransaction] = {}

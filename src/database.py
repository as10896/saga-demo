"""
Mock database implementations for the Saga Pattern demo
"""

from typing import TypeAlias

from .models import Order, SagaTransaction

OrderId: TypeAlias = str
ProductId: TypeAlias = str
UserId: TypeAlias = str
SagaId: TypeAlias = str

OrdersDB: TypeAlias = dict[OrderId, Order]
InventoryDB: TypeAlias = dict[ProductId, int]
UserBalances: TypeAlias = dict[UserId, float]
SagaTransactions: TypeAlias = dict[SagaId, SagaTransaction]


def create_default_orders_db() -> OrdersDB:
    """Factory method to create default orders database"""
    return {}


def create_default_inventory_db() -> InventoryDB:
    """Factory method to create default inventory database"""
    return {"product_1": 100, "product_2": 50, "product_3": 25}


def create_default_user_balances() -> UserBalances:
    """Factory method to create default user balances database"""
    return {"user_1": 1000.0, "user_2": 500.0, "user_3": 200.0}


def create_default_saga_transactions() -> SagaTransactions:
    """Factory method to create default saga transactions database"""
    return {}

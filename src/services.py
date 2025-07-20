"""
Business service implementations for individual saga steps
"""

import asyncio
import logging

from .database import inventory_db, user_balances
from .models import Order

logger = logging.getLogger(__name__)


class ValidationService:
    """Handles order validation logic"""

    @staticmethod
    async def validate_order(order: Order) -> None:
        """Validate order details"""
        if order.quantity <= 0:
            raise Exception("Invalid quantity")
        if order.amount <= 0:
            raise Exception("Invalid amount")
        if order.user_id not in user_balances:
            raise Exception("User not found")

        # Simulate async processing
        await asyncio.sleep(0.1)
        logger.info(f"Order {order.id} validated successfully")

    @staticmethod
    async def compensate_validation(order: Order) -> None:
        """No compensation needed for validation"""
        logger.info(f"No compensation needed for validation of order {order.id}")


class InventoryService:
    """Handles inventory management operations"""

    @staticmethod
    async def reserve_inventory(order: Order) -> None:
        """Reserve inventory for the order"""
        if order.product_id not in inventory_db:
            raise Exception("Product not found")

        if inventory_db[order.product_id] < order.quantity:
            raise Exception("Insufficient inventory")

        inventory_db[order.product_id] -= order.quantity
        await asyncio.sleep(0.1)
        logger.info(f"Reserved {order.quantity} units of {order.product_id}")

    @staticmethod
    async def release_inventory(order: Order) -> None:
        """Release reserved inventory"""
        if order.product_id in inventory_db:
            inventory_db[order.product_id] += order.quantity
        logger.info(f"Released {order.quantity} units of {order.product_id}")


class PaymentService:
    """Handles payment processing operations"""

    @staticmethod
    async def process_payment(order: Order) -> None:
        """Process payment for the order"""
        if user_balances[order.user_id] < order.amount:
            raise Exception("Insufficient funds")

        user_balances[order.user_id] -= order.amount
        await asyncio.sleep(0.1)
        logger.info(f"Processed payment of ${order.amount} for user {order.user_id}")

    @staticmethod
    async def refund_payment(order: Order) -> None:
        """Refund payment"""
        user_balances[order.user_id] += order.amount
        logger.info(f"Refunded ${order.amount} to user {order.user_id}")


class ShippingService:
    """Handles shipping operations"""

    @staticmethod
    async def ship_order(order: Order) -> None:
        """Ship the order"""
        # Simulate potential shipping failure
        if order.user_id == "user_3":  # Simulate shipping failure for user_3
            raise Exception("Shipping address invalid")

        await asyncio.sleep(0.2)
        logger.info(f"Order {order.id} shipped successfully")

    @staticmethod
    async def cancel_shipment(order: Order) -> None:
        """Cancel shipment"""
        logger.info(f"Shipment cancelled for order {order.id}")

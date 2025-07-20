"""
Saga orchestrator implementation
"""

import logging
import uuid

from .database import orders_db, saga_transactions
from .models import Order, OrderStatus, SagaStep, SagaTransaction, StepStatus
from .services import (
    InventoryService,
    PaymentService,
    ShippingService,
    ValidationService,
)

logger = logging.getLogger(__name__)


class SagaOrchestrator:
    """
    Orchestrates the execution of saga transactions with compensation logic
    """

    def __init__(self):
        self.steps = [
            {
                "name": "validate_order",
                "action": ValidationService.validate_order,
                "compensate": ValidationService.compensate_validation,
            },
            {
                "name": "reserve_inventory",
                "action": InventoryService.reserve_inventory,
                "compensate": InventoryService.release_inventory,
            },
            {
                "name": "process_payment",
                "action": PaymentService.process_payment,
                "compensate": PaymentService.refund_payment,
            },
            {
                "name": "ship_order",
                "action": ShippingService.ship_order,
                "compensate": ShippingService.cancel_shipment,
            },
        ]

    async def execute_saga(self, order: Order) -> SagaTransaction:
        """
        Execute a saga transaction for the given order

        Args:
            order: The order to process

        Returns:
            SagaTransaction: The completed saga transaction with status and steps
        """
        saga_id = str(uuid.uuid4())
        saga = SagaTransaction(
            id=saga_id,
            order_id=order.id,
            steps=[SagaStep(name=step["name"]) for step in self.steps],
        )
        saga_transactions[saga_id] = saga

        logger.info(f"Starting saga {saga_id} for order {order.id}")

        try:
            # Execute each step
            for i, step_config in enumerate(self.steps):
                step = saga.steps[i]
                logger.info(f"Executing step: {step.name} for order {order.id}")

                try:
                    await step_config["action"](order)
                    step.status = StepStatus.COMPLETED
                    logger.info(f"Step {step.name} completed successfully")
                except Exception as e:
                    step.status = StepStatus.FAILED
                    step.error_message = str(e)
                    logger.error(f"Step {step.name} failed: {str(e)}")

                    # Start compensation
                    await self._compensate_saga(saga, i)
                    saga.status = OrderStatus.FAILED
                    order.status = OrderStatus.FAILED
                    orders_db[order.id] = order
                    return saga

            # All steps completed successfully
            saga.status = OrderStatus.COMPLETED
            order.status = OrderStatus.COMPLETED
            orders_db[order.id] = order
            logger.info(f"Saga {saga_id} completed successfully for order {order.id}")

        except Exception as e:
            saga.status = OrderStatus.FAILED
            order.status = OrderStatus.FAILED
            orders_db[order.id] = order
            logger.error(f"Saga {saga_id} failed for order {order.id}: {str(e)}")

        return saga

    async def _compensate_saga(
        self, saga: SagaTransaction, failed_step_index: int
    ) -> None:
        """
        Execute compensation actions for completed steps in reverse order

        Args:
            saga: The saga transaction to compensate
            failed_step_index: Index of the step that failed
        """
        logger.info(f"Starting compensation for saga {saga.id}")
        saga.status = OrderStatus.COMPENSATING

        # Compensate completed steps in reverse order
        for i in range(failed_step_index - 1, -1, -1):
            step = saga.steps[i]
            if step.status == StepStatus.COMPLETED:
                step_config = self.steps[i]
                try:
                    await step_config["compensate"](orders_db[saga.order_id])
                    step.status = StepStatus.COMPENSATED
                    logger.info(f"Compensated step: {step.name}")
                except Exception as e:
                    logger.error(f"Compensation failed for step {step.name}: {str(e)}")

        logger.info(f"Compensation completed for saga {saga.id}")

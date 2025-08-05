"""
Saga orchestrator implementation.

This module implements the core Saga pattern orchestration logic.
The Saga pattern is used to manage distributed transactions across multiple services by breaking them into a sequence of smaller, local transactions.

Key Concepts:
- Each saga consists of multiple steps (validate, reserve, pay, ship)
- If any step fails, compensation actions are executed in reverse order
- The orchestrator manages the entire transaction lifecycle
- All state changes are persisted to maintain consistency

Learn more about the Saga pattern:
https://microservices.io/patterns/data/saga.html
"""

import logging
import uuid

from .models import Order, OrderStatus, SagaStep, SagaTransaction, StepStatus
from .services import (
    InventoryService,
    PaymentService,
    ShippingService,
    ValidationService,
)
from .session_manager import AsyncSessionManager, UserSession

logger = logging.getLogger(__name__)


class SagaOrchestrator:
    """
    Orchestrates the execution of saga transactions with compensation logic.

    The orchestrator defines the sequence of steps for processing an order:
    1. Validate order (check data validity)
    2. Reserve inventory (ensure products are available)
    3. Process payment (charge the user)
    4. Ship order (arrange delivery)

    If any step fails, compensation actions are executed in reverse order to undo any changes made by previous steps.

    Example flow:
    - Success: validate → reserve → pay → ship → COMPLETED
    - Failure: validate → reserve → pay → [ship fails] → refund → release → FAILED
    """

    def __init__(self):
        """
        Initialize the orchestrator with the saga step definitions.

        Each step has:
        - name: Human-readable step name
        - action: Function to execute the step
        - compensate: Function to undo the step if needed
        """
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

    async def execute_saga(
        self, order: Order, session_id: str, session_manager: AsyncSessionManager
    ) -> SagaTransaction:
        """
        Execute a saga transaction for the given order.

        This is the main orchestration method that:
        1. Creates a new saga transaction
        2. Executes each step in sequence
        3. Handles failures with compensation
        4. Persists all state changes

        Args:
            order: The order to process
            session_id: Session ID for database isolation
            session_manager: The async session manager instance

        Returns:
            SagaTransaction: The completed saga with status and step details
        """
        # Get the user's session with isolated data
        session = await session_manager.get_session(session_id)
        if not session:
            raise RuntimeError(f"Session {session_id} not found")

        orders_db = session.orders_db
        saga_transactions = session.saga_transactions

        # Create a new saga transaction
        saga_id = str(uuid.uuid4())
        saga = SagaTransaction(
            id=saga_id,
            order_id=order.id,
            steps=[SagaStep(name=step["name"]) for step in self.steps],
        )
        saga_transactions[saga_id] = saga

        logger.info(f"🚀 Starting saga {saga_id} for order {order.id}")

        try:
            # Execute each step in the defined sequence
            for i, step_config in enumerate(self.steps):
                step = saga.steps[i]
                logger.info(f"⚡ Executing step: {step.name} for order {order.id}")

                try:
                    # Execute the step action with session data
                    await step_config["action"](order, session)
                    step.status = StepStatus.COMPLETED
                    logger.info(f"✅ Step {step.name} completed successfully")

                except Exception as e:
                    # Step failed - mark it and start compensation
                    step.status = StepStatus.FAILED
                    step.error_message = str(e)
                    logger.error(f"❌ Step {step.name} failed: {e}")

                    # Execute compensation for all completed steps
                    await self._compensate_saga(
                        saga, i, order, session, session_manager
                    )

                    # Mark saga and order as failed
                    saga.status = OrderStatus.FAILED
                    order.status = OrderStatus.FAILED
                    orders_db[order.id] = order

                    # Save session after failure
                    await session_manager.save_session(session)
                    return saga

            # All steps completed successfully! 🎉
            saga.status = OrderStatus.COMPLETED
            order.status = OrderStatus.COMPLETED
            orders_db[order.id] = order
            logger.info(
                f"🎉 Saga {saga_id} completed successfully for order {order.id}"
            )

        except Exception as e:
            # Unexpected error during saga execution
            saga.status = OrderStatus.FAILED
            order.status = OrderStatus.FAILED
            orders_db[order.id] = order
            logger.error(f"💥 Saga {saga_id} failed for order {order.id}: {e}")

        # Save session after saga completion (success or failure)
        await session_manager.save_session(session)
        return saga

    async def _compensate_saga(
        self,
        saga: SagaTransaction,
        failed_step_index: int,
        order: Order,
        session: UserSession,
        session_manager: AsyncSessionManager,
    ) -> None:
        """
        Execute compensation actions for completed steps in reverse order.

        This is the key part of the Saga pattern - when something fails,
        we need to undo all the changes made by previous steps to maintain data consistency.

        Example: If payment fails after inventory was reserved, we need to
        release the inventory to make it available for other orders.

        Args:
            saga: The saga transaction to compensate
            failed_step_index: Index of the step that failed
            order: The original order object to compensate
            session: The user session containing database state
            session_manager: The async session manager instance
        """
        saga_transactions = session.saga_transactions

        logger.info(f"🔄 Starting compensation for saga {saga.id}")
        saga.status = OrderStatus.COMPENSATING

        # Compensate completed steps in reverse order (LIFO - Last In, First Out)
        for i in range(failed_step_index - 1, -1, -1):
            step = saga.steps[i]

            # Only compensate steps that were successfully completed
            if step.status == StepStatus.COMPLETED:
                step_config = self.steps[i]
                try:
                    logger.info(f"↩️  Compensating step: {step.name}")

                    # Execute the compensation action with the original order object
                    await step_config["compensate"](order, session)

                    # Mark the step as compensated
                    step.status = StepStatus.COMPENSATED
                    logger.info(f"✅ Compensated step: {step.name}")

                except Exception as e:
                    # Compensation failed - this is a serious issue
                    logger.error(f"💥 Compensation failed for step {step.name}: {e}")
                    logger.error(f"💥 Exception type: {type(e)}")
                    import traceback

                    logger.error(f"💥 Traceback: {traceback.format_exc()}")
                    # Note: In a real system, this might trigger alerts or manual intervention

        # Ensure the updated saga is saved back to the session
        saga_transactions[saga.id] = saga
        logger.info(f"🔄 Compensation completed for saga {saga.id}")

        # Save session after compensation
        await session_manager.save_session(session)

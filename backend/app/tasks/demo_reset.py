import asyncio
import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal
from ..core.security import get_password_hash
from ..models.employee import Employee
from ..models.task import Task
from ..models.abnormality import Abnormality, AdminAction
from ..models.work_rule import WorkRule

logger = logging.getLogger(__name__)

DEMO_ADMIN_EMAIL = "demo-admin@sentinel.com"
DEMO_ADMIN_PASSWORD = "demo123"

async def revert_demo_admin_changes():
    """
    Finds the demo admin account. If it doesn't exist, creates it.
    Then wipes any data (like tasks) created by the demo admin, ensuring
    changes made by visitors are temporary and reverted hourly.
    """
    try:
        async with AsyncSessionLocal() as session:
            # 1. Find or create demo admin
            result = await session.execute(
                select(Employee).where(Employee.email == DEMO_ADMIN_EMAIL)
            )
            demo_admin = result.scalar_one_or_none()

            if not demo_admin:
                logger.info(f"Demo Admin not found. Creating {DEMO_ADMIN_EMAIL}...")
                demo_admin = Employee(
                    email=DEMO_ADMIN_EMAIL,
                    password_hash=get_password_hash(DEMO_ADMIN_PASSWORD),
                    full_name="Demo Admin",
                    role="admin",
                    department="Administration"
                )
                session.add(demo_admin)
                await session.commit()
                await session.refresh(demo_admin)
            
            demo_admin_id = demo_admin.id

            # 2. Delete Tasks assigned by demo admin
            stmt_tasks = delete(Task).where(Task.assigned_by == demo_admin_id)
            result = await session.execute(stmt_tasks)
            deleted_tasks = result.rowcount

            # 3. Clean up generic dummy employees (just in case they figured out how to add employees)
            # We delete employees whose email starts with demo-temp- to be safe.
            stmt_emps = delete(Employee).where(Employee.email.like("demo-temp-%"))
            result_emps = await session.execute(stmt_emps)
            deleted_emps = result_emps.rowcount

            # 4. (Optional) Revert global work rules to standard baseline
            # Here we just make sure standard work rule isn't permanently messed up.
            # E.g., setting detection_sensitivity to medium, and work target to 400
            # If the user has a specific rule they want to protect, we could hardcode it.
            # But skipping for now unless the user says they mess with it a lot.

            await session.commit()

            if deleted_tasks > 0 or deleted_emps > 0:
                logger.info(f"Demo Reset Complete: Deleted {deleted_tasks} tasks and {deleted_emps} dummy employees created by Demo Admin.")
            
    except Exception as e:
        logger.error(f"Error during demo admin reset: {e}")

async def hourly_demo_reset_task():
    """
    Background worker that sleeps for 1 hour and reverts demo admin changes.
    """
    logger.info("Hourly Demo Reset Background Task Started.")
    while True:
        try:
            # Initial run happens after the first interval
            await asyncio.sleep(3600)  # 60 minutes
            await revert_demo_admin_changes()
        except asyncio.CancelledError:
            logger.info("Hourly Demo Reset Background Task Stopped.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in hourly_demo_reset_task: {e}")
            await asyncio.sleep(60) # Pause shortly before retrying

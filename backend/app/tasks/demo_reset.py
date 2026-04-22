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
    # Step 1: Ensure demo admin account exists (separate session so it always commits)
    demo_admin_id = None
    try:
        async with AsyncSessionLocal() as session:
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
                    department="Administration",
                    is_active=True,
                )
                session.add(demo_admin)
                await session.commit()
                await session.refresh(demo_admin)
                logger.info(f"Demo Admin created successfully with id={demo_admin.id}")
            else:
                # Also ensure password is always reset to demo123
                demo_admin.password_hash = get_password_hash(DEMO_ADMIN_PASSWORD)
                demo_admin.is_active = True
                await session.commit()

            demo_admin_id = demo_admin.id
    except Exception as e:
        logger.error(f"Error ensuring demo admin account exists: {e}", exc_info=True)
        return  # Don't proceed to cleanup if account step failed

    # Step 2: Clean up temp data (separate session so failures don't affect account)
    try:
        async with AsyncSessionLocal() as session:
            stmt_tasks = delete(Task).where(Task.assigned_by == demo_admin_id)
            result = await session.execute(stmt_tasks)
            deleted_tasks = result.rowcount

            stmt_emps = delete(Employee).where(Employee.email.like("demo-temp-%"))
            result_emps = await session.execute(stmt_emps)
            deleted_emps = result_emps.rowcount

            await session.commit()

            logger.info(f"Demo Reset Complete: deleted {deleted_tasks} tasks, {deleted_emps} temp employees.")
    except Exception as e:
        logger.error(f"Error during demo cleanup: {e}", exc_info=True)


async def hourly_demo_reset_task():
    """
    Background worker that immediately creates/resets demo admin on startup,
    then runs again every hour.
    """
    logger.info("Hourly Demo Reset Background Task Started.")
    while True:
        try:
            # Run immediately on startup, then sleep 60 minutes before next run
            await revert_demo_admin_changes()
            await asyncio.sleep(3600)  # 60 minutes
        except asyncio.CancelledError:
            logger.info("Hourly Demo Reset Background Task Stopped.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in hourly_demo_reset_task: {e}")
            await asyncio.sleep(60) # Pause shortly before retrying


import asyncio
import logging
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal
from ..core.security import get_password_hash
from ..models.employee import Employee
from ..models.task import Task
from ..models.abnormality import Abnormality, AdminAction
from ..models.leave import Leave
from ..models.appeal import Appeal

logger = logging.getLogger(__name__)

DEMO_ADMIN_EMAIL    = "demo-admin@sentinel.com"
DEMO_ADMIN_PASSWORD = "demo123"


async def revert_demo_admin_changes():
    """
    Full demo reset. Runs on startup and every hour.
    Step 1 — Ensure the demo admin account exists and is clean.
    Step 2 — Revert every action the demo admin took.
    """

    # ── Step 1: Ensure demo admin exists & is reset ──────────────────────────
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
                    email         = DEMO_ADMIN_EMAIL,
                    password_hash = get_password_hash(DEMO_ADMIN_PASSWORD),
                    full_name     = "Demo Admin",
                    role          = "admin",
                    department    = "Administration",
                    is_active     = True,
                )
                session.add(demo_admin)
                await session.commit()
                await session.refresh(demo_admin)
                logger.info(f"Demo Admin created: id={demo_admin.id}")
            else:
                # Reset everything that a visitor might have changed
                demo_admin.password_hash = get_password_hash(DEMO_ADMIN_PASSWORD)
                demo_admin.full_name     = "Demo Admin"
                demo_admin.department    = "Administration"
                demo_admin.position      = None
                demo_admin.phone         = None
                demo_admin.avatar_url    = None
                demo_admin.is_active     = True
                await session.commit()

            demo_admin_id = demo_admin.id

    except Exception as e:
        logger.error(f"Error ensuring demo admin account: {e}", exc_info=True)
        return  # Don't run cleanup if we can't confirm the admin id

    # ── Step 2: Revert all actions taken by demo admin ───────────────────────
    try:
        async with AsyncSessionLocal() as session:

            # 1. Delete tasks assigned by demo admin
            r = await session.execute(delete(Task).where(Task.assigned_by == demo_admin_id))
            deleted_tasks = r.rowcount

            # 2. Delete temp employees created by demo admin
            r = await session.execute(delete(Employee).where(Employee.email.like("demo-temp-%")))
            deleted_emps = r.rowcount

            # 3. Revert abnormality reviews done by demo admin → back to unreviewed
            r = await session.execute(
                update(Abnormality)
                .where(Abnormality.reviewed_by == demo_admin_id)
                .values(
                    reviewed        = False,
                    reviewed_by     = None,
                    review_decision = None,
                    reviewed_at     = None,
                )
            )
            reverted_flags = r.rowcount

            # 4. Delete admin actions (warnings/escalations) by demo admin
            r = await session.execute(delete(AdminAction).where(AdminAction.admin_id == demo_admin_id))
            deleted_actions = r.rowcount

            # 5. Revert leave decisions made by demo admin → back to pending
            r = await session.execute(
                update(Leave)
                .where(Leave.reviewed_by == demo_admin_id)
                .values(
                    status         = "pending",
                    reviewed_by    = None,
                    reviewed_at    = None,
                    admin_response = None,
                )
            )
            reverted_leaves = r.rowcount

            # 6. Revert appeal decisions made by demo admin → back to pending
            r = await session.execute(
                update(Appeal)
                .where(Appeal.reviewed_by == demo_admin_id)
                .values(
                    status         = "pending",
                    reviewed_by    = None,
                    reviewed_at    = None,
                    admin_response = None,
                )
            )
            reverted_appeals = r.rowcount

            await session.commit()

            logger.info(
                f"Demo Reset Complete — "
                f"tasks:{deleted_tasks} | temp_emps:{deleted_emps} | "
                f"flags:{reverted_flags} | actions:{deleted_actions} | "
                f"leaves:{reverted_leaves} | appeals:{reverted_appeals}"
            )

    except Exception as e:
        logger.error(f"Error during demo cleanup: {e}", exc_info=True)


async def hourly_demo_reset_task():
    """
    Background worker — runs immediately on startup then every 60 minutes.
    """
    logger.info("Hourly Demo Reset Background Task Started.")
    while True:
        try:
            await revert_demo_admin_changes()
            await asyncio.sleep(3600)  # 60 minutes
        except asyncio.CancelledError:
            logger.info("Hourly Demo Reset Background Task Stopped.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in hourly_demo_reset_task: {e}")
            await asyncio.sleep(60)

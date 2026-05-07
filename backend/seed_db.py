import sys
import os
import uuid
import random
from datetime import datetime, timedelta, timezone
import json
import asyncio
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.employee import Employee
from app.models.session import Session, WorkTimeLog
from app.models.abnormality import Abnormality

async def seed():
    async with AsyncSessionLocal() as db:
        try:
            # 1. Load employees from the context directory
            context_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supabase context")
            employees_file = os.path.join(context_dir, "employees_rows.json")
            
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees_data = json.load(f)
                
            print(f"Loaded {len(employees_data)} employees from context.")
            
            # Make sure they exist in the DB or we use existing ones
            result = await db.execute(select(Employee))
            db_employees = result.scalars().all()
            employee_map = {str(e.id): e for e in db_employees}
            employee_list = list(employee_map.values())
            
            if not employee_list:
                print("No employees in DB, cannot seed sessions.")
                return
                
            now = datetime.now(timezone.utc)
            
            # Generate data for the last 7 days (to fill out the current week)
            for i in range(7):
                day = now - timedelta(days=6-i)
                print(f"Generating data for {day.strftime('%Y-%m-%d')}...")
                
                # Select a random subset of employees to "work" this day
                daily_workers = random.sample(employee_list, k=int(len(employee_list) * 0.8)) # 80% attendance
                
                for emp in daily_workers:
                    # Create 1-2 sessions per day per employee
                    for _ in range(random.randint(1, 2)):
                        start_time = day.replace(hour=random.randint(8, 10), minute=random.randint(0, 59))
                        end_time = start_time + timedelta(hours=random.randint(3, 5))
                        if end_time > now:
                            end_time = now # Don't go into the future
                            if start_time > now: continue
                        
                        # 10% chance of being flagged
                        is_flagged = random.random() < 0.1
                        status = "flagged" if is_flagged else "completed"
                        risk = random.uniform(30, 95) if is_flagged else random.uniform(0, 20)
                        
                        sess = Session(
                            id=uuid.uuid4(),
                            employee_id=emp.id,
                            start_time=start_time,
                            end_time=end_time,
                            total_work_minutes=int((end_time - start_time).total_seconds() / 60) - random.randint(10, 30),
                            total_break_minutes=random.randint(10, 50),
                            lunch_taken=True,
                            status=status,
                            session_quality_score=random.uniform(50, 100),
                            risk_score=risk,
                        )
                        db.add(sess)
                        await db.commit()
                        
                        # Add work logs
                        wt_log = WorkTimeLog(
                            session_id=sess.id,
                            log_type="work",
                            start_time=start_time,
                            end_time=end_time,
                            duration_minutes=sess.total_work_minutes
                        )
                        db.add(wt_log)
                        
                        # Add abnormality if flagged
                        if is_flagged:
                            detections = {}
                            types = ["long_idle", "rapid_paste", "mouse_jiggler", "burst_typing", "off_target"]
                            for _ in range(random.randint(1, 3)):
                                dtype = random.choice(types)
                                detections[dtype] = {
                                    "occurrences": random.randint(1, 10),
                                    "confidence": round(random.uniform(0.7, 0.99), 2),
                                    "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                                }
                            
                            ab = Abnormality(
                                session_id=sess.id,
                                employee_id=emp.id,
                                overall_severity=random.choice(["MEDIUM", "HIGH", "CRITICAL"]),
                                confidence_score=round(random.uniform(0.7, 0.99), 2),
                                detections=detections,
                                first_detected_at=start_time + timedelta(minutes=random.randint(10, 60)),
                                last_updated_at=end_time - timedelta(minutes=10)
                            )
                            db.add(ab)
            await db.commit()
            print("Successfully seeded 7 days of session and abnormality data.")
        except Exception as e:
            print(f"Error seeding: {e}")
            await db.rollback()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())

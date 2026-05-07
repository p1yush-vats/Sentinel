import json
import uuid
import random
from datetime import datetime, timedelta, timezone

def generate_sql():
    # Read employees
    with open('../supabase context/employees_rows.json', 'r', encoding='utf-8') as f:
        employees = json.load(f)

    if not employees:
        print("No employees found.")
        return

    now = datetime.now(timezone.utc)
    sql_statements = []
    
    # We will generate data for the last 7 days
    for i in range(7):
        day = now - timedelta(days=6-i)
        
        # 80% of employees work today
        daily_workers = random.sample(employees, k=int(len(employees) * 0.8))
        
        for emp in daily_workers:
            for _ in range(random.randint(1, 2)):
                sess_id = str(uuid.uuid4())
                emp_id = emp['id']
                
                # Times - generate 2 to 8 hours to get a good spread of mins
                start_time = day.replace(hour=random.randint(8, 10), minute=random.randint(0, 59))
                end_time = start_time + timedelta(hours=random.randint(2, 8))
                if end_time > now:
                    end_time = now
                    if start_time > now: continue
                
                work_mins = int((end_time - start_time).total_seconds() / 60) - random.randint(10, 30)
                if work_mins < 0: work_mins = 0
                break_mins = random.randint(10, 50)
                
                is_flagged = random.random() < 0.4
                
                # Apply new status rules based on work_mins
                if is_flagged:
                    status = "flagged"
                elif work_mins < 200:
                    status = "incomplete"
                elif 250 <= work_mins <= 350:
                    status = "partial"
                else:
                    status = "completed"
                    
                risk = round(random.uniform(30, 95), 2) if is_flagged else round(random.uniform(0, 20), 2)
                qual = round(random.uniform(50, 100), 2)
                
                start_str = start_time.strftime('%Y-%m-%d %H:%M:%S+00')
                end_str = end_time.strftime('%Y-%m-%d %H:%M:%S+00')
                
                # Session
                sql = f"INSERT INTO sessions (id, employee_id, start_time, end_time, total_work_minutes, total_break_minutes, lunch_taken, status, session_quality_score, risk_score, created_at, updated_at) VALUES ('{sess_id}', '{emp_id}', '{start_str}', '{end_str}', {work_mins}, {break_mins}, true, '{status}', {qual}, {risk}, '{start_str}', '{end_str}');"
                sql_statements.append(sql)
                
                # Work Time Log
                wt_id = str(uuid.uuid4())
                sql = f"INSERT INTO work_time_logs (id, session_id, log_type, start_time, end_time, duration_minutes, break_token_used, created_at) VALUES ('{wt_id}', '{sess_id}', 'work', '{start_str}', '{end_str}', {work_mins}, false, '{start_str}');"
                sql_statements.append(sql)
                
                if is_flagged:
                    ab_id = str(uuid.uuid4())
                    detections = {}
                    types = ["long_idle", "rapid_paste", "mouse_jiggler", "burst_typing", "off_target"]
                    for _ in range(random.randint(2, 5)):  # Increased occurrences slightly too
                        dtype = random.choice(types)
                        detections[dtype] = {
                            "occurrences": random.randint(3, 15),
                            "confidence": round(random.uniform(0.75, 0.99), 2),
                            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                        }
                    
                    det_json = json.dumps(detections).replace("'", "''")
                    sev = random.choice(["MEDIUM", "HIGH", "CRITICAL"])
                    conf = round(random.uniform(0.75, 0.99), 2)
                    fd = (start_time + timedelta(minutes=random.randint(10, 60))).strftime('%Y-%m-%d %H:%M:%S+00')
                    lu = (end_time - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S+00')
                    
                    sql = f"INSERT INTO abnormalities (id, session_id, employee_id, overall_severity, confidence_score, detections, first_detected_at, last_updated_at, reviewed, created_at) VALUES ('{ab_id}', '{sess_id}', '{emp_id}', '{sev}', {conf}, '{det_json}'::jsonb, '{fd}', '{lu}', false, '{fd}');"
                    sql_statements.append(sql)

    with open('seed_data.sql', 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_statements))
    print(f"Generated {len(sql_statements)} SQL statements in seed_data.sql.")

if __name__ == '__main__':
    generate_sql()

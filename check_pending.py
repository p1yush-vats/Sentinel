import sqlite3

db = sqlite3.connect(r'C:\Users\Piyush\.sentinel\sentinel.db')
db.row_factory = sqlite3.Row

print("=== UNSYNCED ABNORMALITIES ===")
rows = db.execute(
    "SELECT a.session_id, a.overall_severity, a.confidence_score, a.synced, "
    "s.backend_session_id FROM abnormalities a "
    "LEFT JOIN sessions s ON s.id = a.session_id WHERE a.synced = 0"
).fetchall()

for r in rows:
    print(f"  session_id      : {r['session_id']}")
    print(f"  backend_sess_id : {r['backend_session_id']}")
    print(f"  severity        : {r['overall_severity']} | conf={r['confidence_score']}")
    print()

print(f"Total unsynced: {len(rows)}")

print("\n=== ALL SESSIONS ===")
sessions = db.execute("SELECT id, backend_session_id, status, synced FROM sessions ORDER BY created_at DESC LIMIT 5").fetchall()
for s in sessions:
    print(f"  local={s['id'][:12]}... | backend={s['backend_session_id']} | status={s['status']} | synced={s['synced']}")

db.close()

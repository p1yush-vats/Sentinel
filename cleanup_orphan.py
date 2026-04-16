import sqlite3

db = sqlite3.connect(r'C:\Users\Piyush\.sentinel\sentinel.db')
db.execute("DELETE FROM abnormalities WHERE session_id = 'e8ae752a-f99a-4eb4-a9a9-c7a4aa5815fe'")
db.execute("DELETE FROM sessions WHERE id = 'e8ae752a-f99a-4eb4-a9a9-c7a4aa5815fe'")
db.commit()
print("Cleaned up orphaned session e8ae752a...")
rows = db.execute("SELECT COUNT(*) FROM abnormalities WHERE synced=0").fetchone()
print(f"Unsynced abnormalities remaining: {rows[0]}")
db.close()

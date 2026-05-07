"""
Utility script: interactively ends any active session for a given account.
Run from the project root: python -m app.api.cleanup_sessions
"""
import httpx

API_URL = "https://sentinel-ny7w.onrender.com"

# Get credentials
email = input("Email: ")
password = input("Password: ")

# Login
print("Logging in...")
response = httpx.post(
    f"{API_URL}/api/v1/auth/login",
    json={"email": email, "password": password}
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get active session
print("Checking for active sessions...")
response = httpx.get(f"{API_URL}/api/v1/sessions/active", headers=headers)

if response.status_code == 200:
    data = response.json()
    active = data.get("active_session")
    
    if active:
        print(f"✓ Found active session: {active['id']}")
        print(f"  Started: {active['start_time']}")
        
        # End it
        print("Ending session...")
        response = httpx.post(
            f"{API_URL}/api/v1/sessions/{active['id']}/end",
            headers=headers,
            json={
                "total_work_minutes": active.get("total_work_minutes", 0),
                "total_break_minutes": active.get("total_break_minutes", 0),
                "lunch_taken": active.get("lunch_taken", False)
            }
        )
        
        if response.status_code == 200:
            print("✅ Session ended successfully!")
        else:
            print(f"❌ Failed to end session: {response.text}")
    else:
        print("✅ No active sessions found")
else:
    print(f"❌ Failed to check sessions: {response.text}")
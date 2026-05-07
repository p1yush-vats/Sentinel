# CHAPTER 4: TESTING AND IMPLEMENTATION

## 4.1 Testing Methodology

Software testing is an ongoing process of evaluating and verifying that a software product or application does what it is supposed to do. The benefits of testing include preventing bugs, lowering development costs, and improving organizational performance. For Sentinel—a complex distributed system spanning native and web platforms—a multi-tiered testing strategy was adopted.

### 4.1.1 Unit Testing
Unit testing involves examining individual components to ensure they function independently. In the context of the FastAPI backend, this meant testing internal utility functions and Pydantic schema validations using `pytest`. For instance, ensuring that the Pydantic models correctly reject malformed email addresses or negative values in productivity metrics before reaching the Supabase database.

### 4.1.2 Module Testing
Module testing groups multiple interconnected units and tests their synergy. The core module tested here was the MindCompass Abnormality Detection Engine inside the `backend/app/services` directory. The module was isolated, and synthetic desktop payloads (with unusually high keystroke counts or banned application usage) were fed into it to validate that the severity algorithms calculated confidence scores accurately.

### 4.1.3 Integration Testing
Integration testing determines if independently developed units of software work correctly when connected. The critical integration point was the Python Desktop Client connecting to the FastAPI backend and simultaneously dispatching WebSocket events. An integration test suite verified that when the client emitted a data payload, the backend successfully processed it, updated the Supabase DB, and pushed a real-time WebSocket update to the React Dashboard.

### 4.1.4 System Testing
System testing is performed on a complete, integrated system to evaluate its compliance with its specified requirements. The environment was deployed mimicking production (Vercel for frontend, backend hosted on a cloud instance). We verified the complete flow: An employee launches the compiled `.exe`, starts a session, the system records inputs natively, the backend processes them, and the Admin dashboard visualizes the data instantaneously.

### 4.1.5 White Box / Black Box Testing

- **White Box Testing:** This involves testing internal structures or workings. The routing and background task loops were white-box tested. The Python code (like `demo_reset.py`) was explicitly analyzed to track the execution flow of cron-style tasks resetting database states to ensure "Demo Mode" security.
- **Black Box Testing:** This examines functionality without peering into internal structures. It was heavily utilized for UI and Client testing. Simulating an end-user, we attempted to bypass the desktop tracker by manipulating local network settings or inputting massive text payloads in the Appeal form, observing the system's resilience strictly from external feedback.

### 4.1.6 Acceptance Testing
Acceptance testing is the final phase, verifying if the system is ready for release. Beta users were given the `SENTINEL_DEMO.exe` and asked to execute regular tasks while the Admin dashboard was monitored, validating UX assumptions, detection sensitivity, and overall system stability.

## 4.2 Test Data & Test Cases

The following tables document the explicit Black Box system test cases executed to validate the core non-negotiable functionalities of the application.

### Table 4.1: Authentication & Authorization Module

| Test Case ID | Scenario / Description | Input Data | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-001** | Employee logs in with valid Supabase credentials via Dashboard. | Email: `test@company.com`<br>Pass: `Valid123!` | System validates JWT and redirects to Employee Dashboard route. | Redirected to Employee Layout | **PASS** |
| **TC-002** | Employee attempts to access an Admin-only route (e.g. `/admin/abnormalities`). | *Direct URL Navigation* | React Router intercepts request and redirects back to unauthorized view. | Redirected successfully | **PASS** |

### Table 4.2: Abnormality Detection & Tracking Module

| Test Case ID | Scenario / Description | Input Data | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-003** | Desktop client triggers tracking while "Demo Mode" is active. | *Session Start* | MindCompass engine lowers severity thresholds to immediately flag any idle behavior for demonstration purposes. | Abnormalities flagged rapidly | **PASS** |
| **TC-004** | Employee launches an unauthorized application (e.g., a known game executable). | *Active Window Title change* | Desktop app logs the app. MindCompass categorizes it as High Severity and flags the DB. | Flagged as 'HIGH' severity | **PASS** |
| **TC-005** | Network disconnects temporarily during an active tracking session. | *Network drop* | Desktop app caches payload locally and resyncs automatically once the connection is restored. | Payload buffered & sent later | **PASS** |

### Table 4.3: Task & Leave Management

| Test Case ID | Scenario / Description | Input Data | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-006** | Admin approves a pending leave request via Dashboard. | *Admin clicks "Approve"* | Backend updates Supabase status and triggers `email_tasks.py` to notify the employee. | Status updated, Email sent | **PASS** |
| **TC-007** | Employee submits an appeal for a flagged abnormality. | Reason: "Testing software" | Abnormality status updates to 'Appealed', Admin sees notification in UI. | Appeal linked to Abnormality | **PASS** |

## 4.3 Test Reports and Debugging

During the integration testing phase, a few critical issues were discovered and rectified:
- **The Bug:** During live demonstrations, the system's data would become cluttered with test values, and manually deleting rows before every pitch was tedious. Furthermore, some users encountered persistent 404 routing errors on Vercel due to SPA routing misconfigurations.
- **Debugging Process:** Vercel deployment logs indicated that the React Router was failing on direct URL hits because `vercel.json` was missing routing rewrites.
- **The Fix:** We implemented a robust `vercel.json` config to handle SPA fallbacks. For the clutter issue, we developed `demo_reset.py`, an automated server-side task that restores the sandbox state hourly, reverting administrator modifications to ensure a pristine and secure "Demo Mode" environment for every presentation.

## 4.4 Implementation Manual

Deploying a replica of Sentinel requires setting up the three fundamental towers of the architecture: Supabase, the Backend API, and the Frontend/Desktop environments.

### 4.4.1 Database Implementation (Supabase)
1. Register for a Supabase Cloud account and initialize a new Project.
2. Execute the provided `supabase schema v2.txt` in the SQL Editor to generate the tables (`employees`, `abnormalities`, `sessions`, etc.).
3. Configure Authentication settings to allow Email/Password sign-ups.

### 4.4.2 Backend Implementation (FastAPI)
1. Clone the repository and navigate to the `backend/` directory.
2. Create a `.env` file containing the `SUPABASE_URL`, `SUPABASE_KEY`, and SMTP email configurations.
3. Install dependencies via `pip install -r requirements.txt`.
4. Deploy the server using `uvicorn app.main:app --host 0.0.0.0 --port 8000` (or deploy via Docker to a cloud provider).

### 4.4.3 Application Implementation (Vercel & PyInstaller)
1. **Dashboard:** Navigate to `dashboard/`, install Node modules (`npm install`), configure the `.env` with the backend API URL, and deploy directly to Vercel via the Vercel CLI or Dashboard.
2. **Desktop App:** Navigate to `desktop-app/`, install Python requirements, and run `pyinstaller sentinel.spec` to compile the raw Python source into a standalone executable (`SENTINEL_DEMO.exe`) for Windows deployment.

## 4.5 Users’ Training

The platform was engineered for radical simplicity. However, standard operating procedures are enforced:
1. **Employee Training:** Employees are instructed to simply log into the Desktop application and press "Start Session". Minimal interaction is required as tracking is passive.
2. **Administrator Training:** HR/Admins are guided through the Web Dashboard via intuitive layouts. A "Tasks" and "Abnormalities" feed provides clear actionable buttons to resolve issues efficiently.

## 4.6 Post Implementation Maintenance

Maintenance strategies ensure long-term stability:
1. **Executable Updates:** If the internal desktop monitoring scripts change, a new `.exe` must be compiled and distributed to the workforce.
2. **Database Pruning:** Real-time keystroke and productivity metric databases grow rapidly. A scheduled background task must periodically archive metrics older than 6 months to cold storage to maintain high query performance on Supabase.

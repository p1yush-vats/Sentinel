# CHAPTER 3: SYSTEM DESIGN

## 3.1 Design Methodology

System Design is the process of defining the architecture, components, modules, interfaces, and data for a system to satisfy specified requirements. For the **Sentinel Work Integrity System**, an architectural synthesis of **Client-Server** and **Micro-services** design patterns was employed. 

Rather than building a brittle monolith, the application was decoupled into three core components:
1. **Frontend Dashboard (React/Vite):** Handles purely UI rendering, administrative controls, data visualization, and reporting.
2. **Backend Services (FastAPI/Python):** Acts as the central orchestrator, exposing RESTful APIs, managing WebSockets, running background automated tasks (e.g., demo resets, email notifications), and housing the MindCompass Abnormality Engine.
3. **Desktop Application (PySide6/Python):** A localized native client that operates on the employee's machine to securely monitor keystrokes, application usage, and system events.
4. **Database & Auth (Supabase/PostgreSQL):** A highly scalable backend-as-a-service (BaaS) handling identity, Role-Based Access Control (RBAC), and relational data persistence.

This decoupled methodology ensures that intensive background tasks like email processing or running diagnostic models do not block the main dashboard execution or interrupt the continuous data ingestion from the desktop clients.

## 3.2 UML Modeling

Unified Modeling Language (UML) is the industry standard for visualizing, specifying, constructing, and documenting the artifacts of a software-intensive system. By establishing a standardized set of visual modeling constructs, UML enables software engineers, system architects, and stakeholders to clearly communicate the structural and behavioral blueprints of complex applications before extensive coding begins. For the Sentinel Work Integrity System, UML acts as a critical bridge between the high-level business requirements of employee monitoring and the intricate, event-driven technical implementations in the backend.

*(Note: The following architectural diagrams are programmatically rendered using Mermaid.js syntax for precise, version-controlled documentation)*

### 3.2.1 Use Case Diagram

A Use Case diagram captures the system's core functional requirements by mapping the dynamic interactions between external entities (known as actors) and the internal boundaries of the system. It abstracts the technical complexity to focus entirely on *what* the system does rather than *how* it does it. 

In the context of the Sentinel ecosystem, the diagram delineates the stark privilege separation between two primary actors: the **Employee** (who interacts passively with the desktop client to record sessions and manually requests leaves/appeals) and the **Administrator** (who commands the dashboard to review detected anomalies, generate comprehensive audit reports, and govern task assignments). The **Sentinel Engine** itself acts as an autonomous background actor, continuously evaluating productivity metrics and triggering abnormality alerts when predefined heuristic thresholds are breached.

```mermaid
flowchart LR
    Employee([Employee])
    Admin([Administrator])
    System([Sentinel Engine])

    subgraph Sentinel System
        UC1(Authenticate / Login)
        UC2(Start/Stop Tracking Session)
        UC3(Request Leave / Appeal)
        UC4(View Tasks & Productivity)
        UC5(Review Abnormalities)
        UC6(Generate Audit Reports)
        UC7(Assign Tasks)
        UC8(Detect Anomalous Behavior)
    end

    Employee --> UC1
    Employee --> UC2
    Employee --> UC3
    Employee --> UC4

    Admin --> UC1
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7

    System --> UC8
    UC8 -.-> UC5
```

<p align="center"><i>Figure 3.2.1: Use Case Diagram</i></p>


### 3.2.2 Sequence Diagrams

The Sequence Diagrams illustrate the critical flows of the system, detailing how objects interact in sequential order across various modules.

#### 3.2.2.1 Module 1: Authentication

```mermaid
sequenceDiagram
    actor User as "Employee / Admin"
    participant App as "Dashboard / Desktop Client"
    participant FastAPI as "Backend (FastAPI)"
    participant Supabase as "Supabase Auth"
    
    User->>App: Enter Credentials
    activate App
    App->>FastAPI: POST /login (email, password)
    activate FastAPI
    FastAPI->>Supabase: Verify Credentials
    activate Supabase
    Supabase-->>FastAPI: JWT Token & User Data
    deactivate Supabase
    FastAPI-->>App: Session Token & Role
    deactivate FastAPI
    App-->>User: Redirect to Dashboard / Start Client
    deactivate App
```

<p align="center"><i>Figure 3.2.2.1: Module 1: Authentication</i></p>


#### 3.2.2.2 Module 2: Desktop Tracking & Input Collection

```mermaid
sequenceDiagram
    actor Employee as "Employee"
    participant DesktopApp as "Sentinel Desktop App"
    participant FastAPI as "Backend (FastAPI)"
    participant Supabase as "PostgreSQL DB"
    
    Employee->>DesktopApp: Click "Start Session"
    activate DesktopApp
    DesktopApp->>FastAPI: Initialize Session API
    FastAPI->>Supabase: Create Session Record
    DesktopApp-->>Employee: Tracking Started
    
    loop Every minute
        DesktopApp->>DesktopApp: Collect Keystrokes & App Focus
        DesktopApp->>FastAPI: POST /metrics (Batch Sync)
        activate FastAPI
        FastAPI->>Supabase: Insert Productivity Metrics
        deactivate FastAPI
    end
    deactivate DesktopApp
```

<p align="center"><i>Figure 3.2.2.2: Module 2: Desktop Tracking & Input Collection</i></p>


#### 3.2.2.3 Module 3: MindCompass Abnormality Detection

```mermaid
sequenceDiagram
    participant DesktopApp as "Desktop App"
    participant FastAPI as "FastAPI (MindCompass)"
    participant Supabase as "PostgreSQL DB"
    actor Admin as "Administrator"
    
    DesktopApp->>FastAPI: Send Activity Payload
    activate FastAPI
    FastAPI->>FastAPI: Run ML Classification (MindCompass)
    alt Anomaly Detected (Score > Threshold)
        FastAPI->>Supabase: Insert into Abnormalities Table
        FastAPI->>Admin: Trigger WebSocket / Email Alert
    end
    deactivate FastAPI
    
    activate Admin
    Admin->>Supabase: Fetch Pending Abnormalities
    Admin->>Admin: Review Context
    Admin->>Supabase: Submit Review Decision (Penalize/Dismiss)
    deactivate Admin
```

<p align="center"><i>Figure 3.2.2.3: Module 3: MindCompass Abnormality Detection</i></p>


#### 3.2.2.4 Module 4: Tasks & Appeals

```mermaid
sequenceDiagram
    actor Employee as "Employee"
    participant Dashboard as "Frontend Dashboard"
    participant FastAPI as "Backend (FastAPI)"
    participant Supabase as "PostgreSQL DB"
    
    Employee->>Dashboard: Submit Appeal against Abnormality
    activate Dashboard
    Dashboard->>FastAPI: POST /api/appeals
    activate FastAPI
    FastAPI->>Supabase: Create Appeal Record
    FastAPI-->>Dashboard: 201 Created
    deactivate FastAPI
    Dashboard-->>Employee: Show Success Toast
    deactivate Dashboard
```

<p align="center"><i>Figure 3.2.2.4: Module 4: Tasks & Appeals</i></p>


### 3.2.3 Activity Diagram

The Activity diagram illustrates the dynamic nature of the system by modeling the flow of control from activity to activity. Here is the activity flow for **Session Lifecycle & Abnormality Handling**.

```mermaid
flowchart TD
    Start((Start)) --> StartSession

    subgraph Desktop Client
        StartSession([Initialize Session])
        RecordInputs([Record Keystrokes & Apps])
        SyncData([Sync Payload to Cloud])
        EndSession([End Session])
        
        StartSession --> RecordInputs
        RecordInputs --> SyncData
    end

    subgraph Backend Engine
        AnalyzeData([MindCompass Analysis])
        IsAbnormal{Anomaly?}
        FlagDb([Flag in Database])
        StoreNormal([Store Metrics])
        
        SyncData --> AnalyzeData
        AnalyzeData --> IsAbnormal
        IsAbnormal -- Yes --> FlagDb
        IsAbnormal -- No --> StoreNormal
    end

    subgraph Admin Dashboard
        ReviewAlert([Admin Reviews Alert])
        TakeAction([Accept/Reject])
        
        FlagDb --> ReviewAlert
        ReviewAlert --> TakeAction
    end

    TakeAction --> EndSession
    StoreNormal --> EndSession
    EndSession --> End(((End)))
```

<p align="center"><i>Figure 3.2.3: Activity Diagram</i></p>


### 3.2.4 Class Diagram

The Class Diagram highlights the logical representation of the major data structures and their relationships in the application code.

```mermaid
classDiagram
    class Employee {
        +UUID id
        +String email
        +String full_name
        +String role
        +String department
        +login()
    }
    class Session {
        +UUID id
        +UUID employee_id
        +DateTime start_time
        +DateTime end_time
        +String status
        +endSession()
    }
    class Abnormality {
        +UUID id
        +UUID session_id
        +String overall_severity
        +Float confidence_score
        +Boolean reviewed
        +flagAnomaly()
    }
    class Task {
        +UUID id
        +String title
        +String status
        +UUID assigned_to
        +updateStatus()
    }
    Employee "1" --> "*" Session
    Employee "1" --> "*" Task
    Session "1" --> "*" Abnormality
```

<p align="center"><i>Figure 3.2.4: Class Diagram</i></p>


## 3.3 Database Design

Sentinel utilizes Supabase (PostgreSQL) to ensure relational integrity, highly structured schemas, and robust querying capabilities suitable for enterprise resource tracking.

### 3.3.1 Entity Relationship Diagrams (ERD)

To ensure the database schema remains readable and fits appropriately on a standard document page, it has been divided into two logical modules.

#### 3.3.1.1 Core Activity & Tracking ERD

This module highlights the core real-time tracking architecture, detailing how employee sessions trigger productivity metrics and abnormality events.

```mermaid
erDiagram
    EMPLOYEES {
        uuid id PK
        string email
        string full_name
        string role
        string department
    }
    SESSIONS {
        uuid id PK
        uuid employee_id FK
        datetime start_time
        datetime end_time
        string status
    }
    ABNORMALITIES {
        uuid id PK
        uuid session_id FK
        uuid employee_id FK
        string overall_severity
        float confidence_score
        boolean reviewed
    }
    APPEALS {
        uuid id PK
        uuid employee_id FK
        uuid abnormality_id FK
        string status
    }
    PRODUCTIVITY_METRICS {
        uuid id PK
        uuid session_id FK
        uuid employee_id FK
        numeric activity_intensity
    }
    WORK_TIME_LOGS {
        uuid id PK
        uuid session_id FK
        string log_type
    }

    EMPLOYEES ||--o{ SESSIONS : "creates"
    SESSIONS ||--o{ ABNORMALITIES : "triggers"
    SESSIONS ||--o{ PRODUCTIVITY_METRICS : "records"
    SESSIONS ||--o{ WORK_TIME_LOGS : "logs"
    ABNORMALITIES ||--o{ APPEALS : "challenged_by"
```

<p align="center"><i>Figure 3.3.1.1: Core Activity & Tracking ERD</i></p>


#### 3.3.1.2 Administrative & HR ERD

This module maps the organizational entities, detailing how tasks, leaves, and administrative rules map to the workforce.

```mermaid
erDiagram
    EMPLOYEES {
        uuid id PK
        string email
        string full_name
        string role
    }
    TASKS {
        uuid id PK
        string title
        uuid assigned_to FK
        uuid assigned_by FK
        string status
    }
    LEAVES {
        uuid id PK
        uuid employee_id FK
        string leave_type
        string status
    }
    ADMIN_ACTIONS {
        uuid id PK
        uuid admin_id FK
        uuid employee_id FK
        uuid session_id FK
        string action_type
    }
    AUDIT_LOG {
        uuid id PK
        string event_type
        uuid actor_id FK
        string action
    }
    NOTIFICATION_PREFERENCES {
        uuid id PK
        uuid employee_id FK
        boolean email_notifications
    }
    REPORTS {
        uuid id PK
        string report_type
        uuid generated_by FK
    }
    WORK_RULES {
        uuid id PK
        uuid employee_id FK
        integer work_minutes_per_hour
    }

    EMPLOYEES ||--o{ TASKS : "assigned"
    EMPLOYEES ||--o{ LEAVES : "requests"
    EMPLOYEES ||--o{ NOTIFICATION_PREFERENCES : "has"
    EMPLOYEES ||--o{ WORK_RULES : "follows"
    EMPLOYEES ||--o{ REPORTS : "generates"
    EMPLOYEES ||--o{ AUDIT_LOG : "performs"
    EMPLOYEES ||--o{ ADMIN_ACTIONS : "receives"
```

<p align="center"><i>Figure 3.3.1.2: Administrative & HR ERD</i></p>


### 3.3.2 Data Flow Diagrams (DFD)

A DFD maps out the flow of information for any process or system. Below are the 3 levels of DFD for the Sentinel Core workflow.

#### 3.3.2.1 Level 0 DFD (Context Diagram)

```mermaid
flowchart LR
    Employee[Employee]
    SentinelSystem((Sentinel Work Integrity System))
    Admin[Admin / HR]

    Employee -- "Login, Activity Metrics, Leave Requests" --> SentinelSystem
    SentinelSystem -- "Tasks, Status, Alerts" --> Employee
    Admin -- "Policy configs, Task Assignments, Reviews" --> SentinelSystem
    SentinelSystem -- "Audit Reports, Abnormality Alerts" --> Admin
```

<p align="center"><i>Figure 3.3.2.1: Level 0 DFD (Context Diagram)</i></p>


#### 3.3.2.2 Level 1 DFD (Module Level)

```mermaid
flowchart TD
    Employee[Employee]
    Admin[Admin]

    DesktopApp((1.0 Desktop Client))
    Dashboard((2.0 Web Dashboard))
    Backend((3.0 FastAPI Engine))

    SupabaseDB[(D1 PostgreSQL Database)]

    Employee -- "Keystrokes, App Focus" --> DesktopApp
    DesktopApp -- "Sync Activity Batches" --> Backend
    
    Admin -- "Review Anomalies, Create Tasks" --> Dashboard
    Employee -- "Submit Appeals, Manage Tasks" --> Dashboard
    Dashboard -- "REST API / WebSockets" --> Backend
    
    Backend -- "Read/Write Data" --> SupabaseDB
    Backend -- "Trigger Alerts" --> Dashboard
```

<p align="center"><i>Figure 3.3.2.2: Level 1 DFD (Module Level)</i></p>


#### 3.3.2.3 Level 2 DFD (MindCompass & Activity Module)

```mermaid
flowchart TD
    DesktopClient[Desktop Client]

    DataIngest((3.1 Activity Ingestion API))
    MindCompass((3.2 MindCompass ML Classifier))
    AlertSystem((3.3 Notification System))

    MetricsTable[(D2 Productivity Metrics)]
    AbnormalityTable[(D3 Abnormalities Table)]

    DesktopClient -- "Raw Activity Payload" --> DataIngest
    DataIngest -- "Persist Raw Data" --> MetricsTable
    DataIngest -- "Forward to Engine" --> MindCompass
    
    MindCompass -- "Evaluate Thresholds" --> MindCompass
    MindCompass -- "Store Flags" --> AbnormalityTable
    MindCompass -- "Trigger Event" --> AlertSystem
    AlertSystem -- "Email / Socket Notification" --> Admin[Admin Dashboard]
```

<p align="center"><i>Figure 3.3.2.3: Level 2 DFD (MindCompass & Activity Module)</i></p>


## 3.4 Input Design

Input design dictates how data is entered into the system. For an enterprise integrity platform, validation, security, and silent ingestion are paramount.

1. **Desktop Activity Tracking (Automated Input):**
   - **Mechanism:** The PySide6 client silently hooks into the OS to capture active window titles, keystroke intensity, and mouse movement deltas.
   - **Validation:** Inputs are locally aggregated, structured into JSON batches, and transmitted securely over HTTPS to avoid network payload overload.
   
2. **Dashboard Forms (Manual Input):**
   - **Fields:** Leave Requests, Task Creation, and Appeals forms.
   - **Validation:** Managed via strict React state hooks on the frontend, combined with FastAPI Pydantic schemas on the backend which enforce field lengths, type safety, and valid enumerations (e.g., Status must be `pending`, `approved`, or `rejected`).

## 3.5 Output Design

Output design determines how processed information is presented back to the user or downstream systems in an intelligible, aesthetic format.

1. **Administrator Dashboard Grids & Charts:**
   - The primary UI outputs statistical aggregations of employee productivity. Data is visualized via charts mapping focus hours and break intervals. Real-time anomalous events appear at the top of the feed with high-visibility red markers.
   
2. **Automated Email Notifications:**
   - Sentinel utilizes `smtplib` and MIME formatting to dispatch beautifully branded HTML emails for critical events, such as when a leave request is approved by an administrator or an appeal is updated.
   
3. **Desktop Toasts (Employee UI):**
   - The desktop client provides localized, non-intrusive systemic feedback via system tray notifications (e.g., "Session Started", "Take a Break").

## 3.6 Code Design and Development

The source code directory structure was architected utilizing a "Monorepo" strategy to manage multiple distinct operational domains efficiently:

1. `backend/`: A FastAPI Python server holding API endpoints (`app/api/`), the MindCompass diagnostic models (`app/services/`), Pydantic schemas, and background tasks (like `demo_reset.py` and `email_tasks.py`).
2. `dashboard/`: A React Single-Page Application (SPA) handling the comprehensive web interface, contextual state, routing, and WebSocket listeners.
3. `desktop-app/`: A self-contained PySide6 Python application equipped with PyInstaller configurations (`sentinel.spec`) to build executable binaries for end-users, housing the native OS monitoring modules (`src/detection/`).

This strict separation of concerns means algorithmic updates to the detection engine on the backend do not require rebuilding the desktop binaries, and dashboard visual redesigns do not risk halting background API operations.

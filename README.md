# SENTINEL: Work Integrity System

SENTINEL is a comprehensive workforce monitoring and productivity optimization ecosystem designed for high-trust corporate environments. It combines AI-driven behavioral analysis with real-time reporting to ensure operational integrity and employee well-being.

## 🚀 System Architecture

SENTINEL consists of three integrated components:

1.  **Backend API**: A high-performance FastAPI service connected to Supabase (PostgreSQL), handling session management, anomaly aggregation, and HR reporting.
2.  **Admin Dashboard**: A modern React-based workspace for HR and Managers to monitor live feeds, analyze organizational health, and manage employee tasks.
3.  **Desktop Agent**: A privacy-aware Python application that runs on employee workstations, collecting metadata (keystroke intervals, mouse patterns) to detect burn-out or integrity breaches without recording sensitive text.

---

## 🛠️ Infrastructure Setup

### 1. Backend Service (`/backend`)
Powering the logic and data storage.

**Prerequisites**: Python 3.9+, PostgreSQL (Supabase recommended), Redis (optional for Celery).

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure your DB and SMTP credentials
uvicorn app.main:app --reload
```

### 2. Admin Dashboard (`/dashboard`)
The central monitoring hub.

**Prerequisites**: Node.js 18+, NPM/Yarn.

```bash
cd dashboard
npm install
cp .env.example .env      # Point VITE_API_URL to your backend
npm run dev
```

### 3. Desktop Application (`/desktop-app`)
The native client for employees.

**Prerequisites**: Python 3.10+ (Windows 10/11 Required).

```bash
cd desktop-app
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd src
python main.py
```

---

## 📦 Building & Distribution

### Desktop App Compilation (`.exe`)

The desktop app can be compiled into a single executable for distribution.

1.  **Direct Build**:
    Run the provided batch script from the `desktop-app` directory:
    ```cmd
    cd desktop-app
    build.bat
    ```
    This uses PyInstaller and the `sentinel.spec` configuration to generate `dist\SENTINEL.exe`.

2.  **Installer Creation**:
    Use the `installer.iss` file with **Inno Setup** to create a professional Windows installer (`SENTINEL-Setup.exe`).

### Deployment

- **Backend**: Pre-configured for deployment on **Render** (see `render.yaml`).
- **Dashboard**: Optimal for **Vercel** or **Netlify** (see `vercel.json` and `netlify.toml`).

---

## 🛡️ Privacy & Security

- **Metadata Only**: The Desktop Agent records timing and size metadata (e.g., "100 keys/min", "large paste detected"). It **NEVER** records actual characters, passwords, or screen contents.
- **Local Cache**: In case of network failure, the agent caches detections locally in an encrypted SQLite database and syncs automatically when the connection is restored.

---

## 📄 Project Documentation

This repository contains the full academic documentation and reports:
- `SENTINEL_Major_Project_Report_Piyush_Vats.docx`: Detailed project dissertation.
- `report_markdowns/`: Source markdown chapters for the report.

---

Developed by **Piyush Vats** | Part of BCA 2023-26 Major Project.

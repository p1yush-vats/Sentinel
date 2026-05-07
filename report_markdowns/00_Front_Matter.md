# COVER PAGE

**GURU GOBIND SINGH INDRAPRASTHA UNIVERSITY**  
**BACHELOR OF COMPUTER APPLICATIONS**  
*(BCA 2023–2026)*

<br>

## MAJOR PROJECT REPORT

### **SENTINEL**
**An AI-Driven Work Integrity & Productivity Monitoring Ecosystem**

<br>

*Submitted in partial fulfillment of the requirements for the award of the degree of*  
**Bachelor of Computer Applications**

<br>

**Submitted by**  
**PIYUSH VATS**  
Roll No.: 03913702023  
BCA – Semester VI  

<br>

**Under the Guidance of**  
**[Faculty Guide Name]**  
Designation, Department  

<br>

**[Name of the College/Institution]**  
*Affiliated to Guru Gobind Singh Indraprastha University, New Delhi*  
**Academic Year: 2025–2026**

---
*(Page Break)*
---

# CERTIFICATE

This is to certify that the Major Project entitled **"SENTINEL: An AI-Driven Work Integrity & Productivity Monitoring Ecosystem"** submitted by **Mr. Piyush Vats**, Roll No. **03913702023**, in partial fulfillment of the requirements for the award of the degree of Bachelor of Computer Applications from Guru Gobind Singh Indraprastha University, New Delhi, is a bonafide record of the project work carried out by the student under my supervision and guidance.

This project has not been submitted anywhere else for the award of any degree, diploma, or any other similar title.

<br><br><br>

**Faculty Guide**  
*[Faculty Guide Name]*  
*Designation*  
*[Department Name]*  
*[Institution Name]*  

<br>

**Forwarded through:**  
**Head of Department / Director**

---
*(Page Break)*
---

# DECLARATION

I, **Piyush Vats**, Roll No. **03913702023**, student of Bachelor of Computer Applications (BCA), Semester VI, hereby declare that the Major Project entitled **"SENTINEL: An AI-Driven Work Integrity & Productivity Monitoring Ecosystem"** submitted to Guru Gobind Singh Indraprastha University, New Delhi, is an original work done by me under the supervision of **[Faculty Guide Name]**, and has not been submitted in part or in full to any other university or institution for the award of any degree or diploma.

I further declare that all the information, facts, and figures presented in this report are true and correct to the best of my knowledge and belief.

<br><br>

**Date:** ___________  
**Place:** New Delhi  

<br>

**Piyush Vats**  
Roll No.: 03913702023  
BCA – Semester VI

---
*(Page Break)*
---

# ACKNOWLEDGEMENT

I take this opportunity to express my profound sense of gratitude and deep respect to all those who guided and supported me throughout the course of this Major Project.

I would like to express my sincere thanks to **[Faculty Guide Name]**, my project guide, for their invaluable guidance, encouragement, and constant support at every stage of this project. Their insights and expertise have been instrumental in shaping this work.

I am deeply grateful to the Head of Department, and the entire faculty of **[Institution Name]** for providing the facilities and environment that enabled me to pursue this project.

I also extend my gratitude to Guru Gobind Singh Indraprastha University, New Delhi, for its academic framework that allowed me to undertake this project as part of my BCA curriculum.

Special thanks to my family and friends for their unwavering moral support and encouragement throughout the journey.

Lastly, I am grateful to all those who directly or indirectly contributed to the successful completion of this project.

<br><br>
**Piyush Vats**  
Roll No.: 03913702023

---
*(Page Break)*
---

# ABSTRACT

The modern remote and hybrid work environment has introduced significant challenges in maintaining employee accountability, ensuring work integrity, and accurately measuring productivity. Traditional attendance systems and manual supervision are insufficient to address the complexities of distributed work environments where an employee may be physically absent yet digitally clocked in.

**SENTINEL** is a full-stack, AI-driven work integrity and productivity monitoring ecosystem designed to address these challenges. The system operates as a three-tier architecture: a native Windows desktop application deployed on employee workstations, a cloud-hosted FastAPI backend with real-time WebSocket communication, and a React-based administrative web dashboard for centralized monitoring and HR management.

The desktop application performs privacy-safe, continuous behavioral analysis of employee activity — tracking only metadata (keystroke timing intervals, mouse movement patterns, clipboard size, and idle periods) without capturing any actual content. Its AI-powered detection engine identifies eleven categories of workplace malpractice including mechanical typing (bot/macro use), mouse jiggler devices, superhuman typing speeds, suspicious paste operations, extended idle periods, clock-in/clock-out abuse, and scripted activity patterns.

The backend, deployed on Render, provides a comprehensive RESTful API with JWT-based authentication, session lifecycle management, anomaly reporting, leave management, task assignment, appeal workflows, and automatic PDF report generation. PostgreSQL (Supabase) serves as the cloud database with a twelve-table normalized schema. Real-time events are pushed to the admin dashboard via dedicated WebSocket channels, enabling instantaneous oversight.

The React web dashboard offers dual-role interfaces: a full-featured administrative panel for monitoring all employees, reviewing flagged sessions, approving leaves, assigning tasks, and exporting metrics; and an employee self-service portal for viewing personal session history, submitting leave requests, raising appeals, and tracking assigned tasks.

SENTINEL demonstrates the practical application of behavioral AI, real-time networking, and modern full-stack development to solve genuine enterprise HR problems — delivering an end-to-end production-ready system that is privacy-conscious, highly configurable, and remarkably robust against workplace fraud.

*Keywords: Work Monitoring, Behavioral Analysis, FastAPI, React, WebSocket, AI Detection, Employee Productivity, Privacy-Preserving System, HR Management, Remote Work Security.*

---
*(Page Break)*
---

# TABLE OF CONTENTS

- Certificate (ii)
- Declaration (iii)
- Acknowledgement (iv)
- Abstract (v)
- Table of Contents (vi)
- List of Figures (viii)
- List of Tables (ix)

**CHAPTER 1 — INTRODUCTION**
  - 1.1 Background and Motivation (1)
  - 1.2 Problem Statement (4)
  - 1.3 Objectives of the Project (6)
  - 1.4 Scope of the Project (7)
  - 1.5 Organization of the Report (9)

**CHAPTER 2 — LITERATURE SURVEY**
  - 2.1 Existing Work Monitoring Systems (10)
  - 2.2 Behavioral Analysis in Workplace Monitoring (13)
  - 2.3 Privacy-Preserving Monitoring Techniques (16)
  - 2.4 Real-Time Communication Technologies (19)
  - 2.5 Comparative Study (21)
  - 2.6 Research Gap Identified (23)

**CHAPTER 3 — SYSTEM ANALYSIS**
  - 3.1 Feasibility Study (24)
  - 3.2 Requirements Analysis (27)
  - 3.3 Functional Requirements (29)
  - 3.4 Non-Functional Requirements (32)
  - 3.5 Use Case Modeling (34)
  - 3.6 Data Flow Diagrams (Context, Levels 0 and 1) (38)

**CHAPTER 4 — SYSTEM DESIGN**
  - 4.1 System Architecture Topology (43)
  - 4.2 Application Logic & Component Architecture (46)
  - 4.3 Database Schema & Relational Modeling (49)
  - 4.4 Real-Time System Design (53)
  - 4.5 API Interface Blueprint (56)
  - 4.6 User Interface (UX/UI) Strategy (58)

**CHAPTER 5 — IMPLEMENTATION**
  - 5.1 Technology Stack Rationalization (60)
  - 5.2 Desktop Subsystem Implementation Details (63)
  - 5.3 Detection Engine Programming Logic (66)
  - 5.4 Backend Service Logic & Asynchrony (69)
  - 5.5 React SPA Integration & State Management (72)
  - 5.6 CI/CD Deployment Mechanics (75)

**CHAPTER 6 — TESTING**
  - 6.1 Testing Methodologies Framework (77)
  - 6.2 Unit Test Execution Modules (79)
  - 6.3 Integration Testing Matrix (81)
  - 6.4 System and Endurance Testing (83)
  - 6.5 User Acceptance Testing (UAT) Outcomes (85)

**CHAPTER 7 — RESULTS AND DISCUSSION**
  - 7.1 Real-World System Performance Metrics (86)
  - 7.2 Detection Heuristics Algorithm Accuracy (88)
  - 7.3 Dashboard and Feedback Analysis (90)
  - 7.4 System Output Demonstrations (92)
  - 7.5 Current System Limitations (94)

**CHAPTER 8 — CONCLUSION AND FUTURE SCOPE**
  - 8.1 Evaluative Conclusion (96)
  - 8.2 Scope for Future Modifications (98)

- **REFERENCES** (100)
- **APPENDICES**
  - Appendix A: Key Source Code Snippets (102)
  - Appendix B: Database Configuration Code (105)
  - Appendix C: API Endpoint Spec (107)

---
*(Page Break)*
---

# LIST OF FIGURES

1. Figure 3.1: Use Case Diagram for System Administrator
2. Figure 3.2: Use Case Diagram for Enterprise Employee
3. Figure 3.3: Context-Level Data Flow Diagram (DFD)
4. Figure 3.4: Level 1 DFD: Desktop Client Operations
5. Figure 3.5: Level 1 DFD: API Operations
6. Figure 4.1: High-Level System Architecture Diagram
7. Figure 4.2: Entity-Relationship Context Chart
8. Figure 4.3: WebSocket Notification Strategy Tree
9. Figure 5.1: Session TimeEngine Workflow
10. Figure 5.2: Abnormality Aggregation Funnel
11. Figure 7.1: Desktop App Control Interface
12. Figure 7.2: Administrative Alert Interface 
13. Figure 7.3: Admin Interactive Task Assignment

# LIST OF TABLES

1. Table 2.1: Benchmarking Analysis of Active Monitoring Software
2. Table 3.1: Tabulated Functional System Requirements 
3. Table 3.2: NFR Scaling Targets 
4. Table 4.1: Database Entities Reference
5. Table 4.2: Employees Schema Logic
6. Table 4.3: Detection Severities and Weight Mapping 
7. Table 5.1: Software Technology Dependencies Matrix
8. Table 6.1: Heuristics Testing and Precision Table
9. Table 7.1: Server Render Benchmarks Response Table

---
*(Page Break)*

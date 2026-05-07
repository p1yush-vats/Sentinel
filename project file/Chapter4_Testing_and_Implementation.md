# CHAPTER 4: TESTING AND IMPLEMENTATION

## 4.1 Testing Methodology

Software testing is an ongoing process of evaluating and verifying that a software product or application does what it is supposed to do. The benefits of testing include preventing bugs, lowering development costs, and improving organizational performance. For CollabCode—a complex distributed system—a multi-tiered testing strategy was adopted.

### 4.1.1 Unit Testing
Unit testing involves examining individual components to ensure they function independently. In the context of the Next.js frontend, this meant testing stateless components visually and programmatically using Jest. For instance, ensuring the `JoinApprovalToast` component correctly renders the username and avatar passed to it as props without crashing, regardless of whether the avatar string was malformed or empty.

### 4.1.2 Module Testing
Module testing groups multiple interconnected units and tests their synergy. The core module tested here was the Socket.IO event handler in `apps/socket-server`. The module was isolated, and synthetic mock clients were created to connect and emit `register-owner` and `join-request` events, validating that the server’s internal `RoomState` Map correctly added and removed pending requests without race conditions.

### 4.1.3 Integration Testing
Integration testing determines if independently developed units of software work correctly when connected. The critical integration point was the Next.js server connecting to the Appwrite Database and the AWS ECS SDK simultaneously. An integration test suite verified that when a user called the `/api/rooms/[roomId]/start` route, the backend successfully verified the user's JWT with Appwrite before securely invoking the AWS `runTask` API command.

### 4.1.4 System Testing
System testing is performed on a complete, integrated system to evaluate its compliance with its specified requirements. The environment was deployed to a staging URL mimicking production. We verified the complete flow: A user logs in, creates a room, a container boots up, and the VS Code environment is successfully framed and mapped to the Elastic File System (EFS).

### 4.1.5 White Box / Black Box Testing

- **White Box Testing:** This involves testing internal structures or workings. The routing algorithm resolving ECS container IPs was white-box tested. The Node.js code was explicitly analyzed line-by-line using `console.log` traces and AWS CloudWatch logs to track the initialization of Fargate Elastic Network Interfaces (ENIs).
- **Black Box Testing:** This examines functionality without peering into internal structures. It was heavily utilized for UI testing. Simulating a guest user who knows nothing about AWS, we attempted to crash the frontend by pasting malicious payloads into the chat window and rapidly clicking the "Knock" button, observing the system's responses strictly from the browser console.

### 4.1.6 Acceptance Testing
Acceptance testing is the final phase, verifying if the system is ready for release. Beta users (peers) were given access to the staging URL and asked to execute a collaborative coding task (e.g., building a simple React app together in a shared Next.js room) to validate UX assumptions and overall system stability.

## 4.2 Test Data & Test Cases

The following tables document the explicit Black Box system test cases executed to validate the core non-negotiable functionalities of the application.

### Table 4.1: Authentication & Authorization Module

| Test Case ID | Scenario / Description | Input Data | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-001** | User logs in with valid Appwrite credentials. | Email: `test@iitm.edu`<br>Pass: `Valid123!` | System sets JWT HttpOnly cookie and redirects to Dashboard. | Redirected to `/dashboard` | **PASS** |
| **TC-002** | User attempts to access a protected route (e.g. `/dashboard`) while completely unauthenticated. | *Direct URL Navigation* | Middleware intercepts request and redirects instantly to `/login`. | Redirected to `/login` | **PASS** |

### Table 4.2: Knock-to-Enter Security Workflow

| Test Case ID | Scenario / Description | Input Data | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-003** | Guest navigates to Room URL while Owner is offline. | *Room URL* | Guest sees animated Lobby; Socket Server acknowledges no owner present. | Lobby displays "Waiting for Host". | **PASS** |
| **TC-004** | Owner receives join request but explicitly clicks "Reject". | *Owner clicks UI Button* | Socket Server emits rejection; Guest UI transitions to "Access Denied" view. | Guest routed to Error View. | **PASS** |
| **TC-005** | Owner ignores the join request for > 60 seconds (Timeout). | *Timeout Trigger* | The Socket Server’s `setTimeout` auto-clears the request and emits timeout event to Guest. | Toast vanishes; Guest denied. | **PASS** |

### Table 4.3: Cloud Execution Setup (ECS)

| Test Case ID | Scenario / Description | Input Data | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-006** | Creating a Room with Python language enum triggers correct Docker Image. | Language: `python` | The AWS `runTask` API command overwrites the task definition to pull the `openvscode-python` ECR image. | Python image deployed in ECS Logs. | **PASS** |
| **TC-007** | Repeated room startups maintain files (Testing EFS persistence). | Create `test.py` -> Stop Room -> Start Room | The previously written `test.py` file is visible in the VS Code file tree upon reconnection. | File successfully persisted. | **PASS** |

## 4.3 Test Reports and Debugging

During the module testing phase of the WebSocket integration, a significant bug was discovered in the Knock-to-Enter flow. 
- **The Bug:** If a guest user "knocked" and then quickly closed their browser tab before the host could approve, the host's screen would show the toast forever, and attempting to click "Approve" would crash the Node.js socket server due to an unhandled exception when attempting to emit to an orphaned `socket.id`.
- **Debugging Process:** AWS CloudWatch logs for the Socket Server indicated a `Cannot read properties of undefined` error inside the `join-response` listener.
- **The Fix:** We implemented a `disconnect` listener interceptor in `socket.ts` that loops through the `pendingRequests` Map. If the disconnecting user has a pending request, it proactively removes it from the queue and sends a semantic `cancel-request` event to the host, terminating the toast component cleanly.

## 4.4 Implementation Manual

Deploying a replica of CollabCode requires setting up the three fundamental towers of the architecture: Appwrite, AWS, and Vercel.

**Prerequisites:** Node.js (v20+), Docker, AWS CLI configured with Administrator access.

### 4.4.1 Backend/Database Implementation (Appwrite)
1. Register for an Appwrite Cloud account.
2. Initialize a new Project named `CollabCode`.
3. Under the **Databases** tab, create a new Database.
4. Create the `Rooms` collection.
5. Create string attributes: `room_id`, `owner_id`, `name`, `language`, `status`, `access_point_id`, and `ideUrl`.
6. Enforce strict Database-level permissions (Role: `Users` can Read/Write).

### 4.4.2 Cloud Infrastructure Implementation (AWS)
1. **ECR (Elastic Container Registry):** Run `./docker/build-and-push.sh <username>` to compile the 5 specific language Dockerfiles (Node, Python, C++, Java, Nextjs) and push them securely to the AWS ECR registry.
2. **EFS (Elastic File System):** Create a new EFS file system ensuring it is in the same VPC as the ECS cluster. Note the exact File System ID.
3. **ECS Cluster:** Create an AWS Fargate cluster. Define a Base Task Definition utilizing one of the uploaded ECR images, mapping port `3000` to the container. Assign a Task Execution Role with permissions to mount EFS volumes.

### 4.4.3 Application Implementation (Vercel)
1. Clone the Next.js `apps/web` repository locally.
2. Create a `.env.local` file containing the Appwrite Endpoint, Project ID, AWS IAM Access Keys, and the ECS Task Definition ARNs.
3. Push to a GitHub repository and link it to Vercel via the Vercel Dashboard. Vercel will automatically detect the Next.js framework, run `npm run build`, and deploy the frontend to a globally distributed edge network.

## 4.5 Users’ Training

Due to the consumer-facing nature of the SaaS product, formal, physical user training is considered a failure in UI design. The platform was engineered for radical simplicity. However, an onboarding overlay guide is implemented:
1. **Dashboard Training:** A floating tooltip explains that clicking "New Room" requires selecting a language environment.
2. **In-Room Training:** When the IDE mounts for the first time, a specialized `README.md` is populated inside the container instructing the user on how to use the specific terminal to run their code (e.g., typing `python main.py` or `npm run dev`).
3. **Shortcuts Dialog:** A prominent "Keyboard Shortcuts" modal (via `ShortcutsDialog.tsx`) is available to train power users on rapid workflows.

## 4.6 Post Implementation Maintenance

Maintenance strategies ensure long-term stability:
1. **Container Image Updating:** As underlying base images (e.g., Ubuntu, Node versions) receive security patches, the Docker images must be rebuilt and pushed to ECR.
2. **EFS Storage Rotation:** Persistent file storage incurs costs. A specialized Cron Job must be architected to scan Appwrite for rooms that have been inactive for > 90 days, triggering a Lambda function to obliterate the corresponding EFS Access point and directories to maintain economic feasibility.

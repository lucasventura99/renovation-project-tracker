# Renovation Project Tracker

A backend system designed to facilitate collaboration between Contractors and Homeowners on renovation projects. This project helps track job status, costs, and project history with robust data consistency.
## Tech Stack

* **Language:** Python 3.12+
* **Framework:** FastAPI (Async)
* **Database:** PostgreSQL 15
* **ORM:** SQLAlchemy 2.0 (Async)
* **API:** GraphQL (via Strawberry)
* **Infrastructure:** Docker & Docker Compose
* **Migrations:** Alembic
* **CI/CD:** GitHub Actions (Automated Testing)

## Key Features

### 1. User Roles & Security
* **Contractor:**
    * Create and manage renovation jobs.
    * Assign Homeowners to jobs securely.
    * Full CRUD access to all job data.
* **Homeowner:**
    * Read-only access to their assigned projects.
    * View real-time progress and historical changes.

### 2. Job Management (Aggregate Root)
The system manages Jobs as the central entity:
* **Core Data:** Description, Location, Cost (Decimal), and Status workflow (PLANNING -> COMPLETED).
* **Sub-tasks:** Granular tracking of line items (e.g., "Demolition", "Electrical").
* **Cost Aggregation:** Job totals can be aggregated from sub-tasks.

### 3. Advanced Feature: Undo/Redo Engine
Unlike simple audit logs, this system implements Database Version Control:
* **Snapshots:** Every destructive change saves a full JSON snapshot of the job state.
* **Time Travel:** Contractors can Undo changes to revert data to a previous state.
* **Branching History:** If a user Undoes to Version 2 and makes a new change, the system automatically "burns" the old future (Versions 3+) to maintain timeline consistency.

### 4. Automated Quality Assurance
* **Unit & Integration Tests:** Comprehensive test suite covering resolvers and service logic.
* **CI Pipeline:** GitHub Actions automatically runs the test suite on every Push and Pull Request.

## Technical Design & Architecture

### The "Branching Time" Logic
The Undo/Redo system is built on a custom Version Pointer strategy:
1.  **Job Table:** Tracks a `current_version` integer.
2.  **JobHistory Table:** Stores `{ version: 1, snapshot: {...} }`.
3.  **Logic:**
    * **Undo:** Moves the `current_version` pointer backward. Data is restored from the snapshot.
    * **Redo:** Moves the pointer forward (if a future version exists).
    * **Write:** If a write occurs while in the "past", all future history records are deleted to prevent conflicts.

### Database Schema Design
* **ACID Compliance:** Uses PostgreSQL transactions to ensure history records and job updates happen atomically.
* **JSON Snapshots:** Chosen over "Diffs" for faster read/restore performance and simplicity in handling schema evolution.

## Setup Instructions

### Prerequisites
* Docker & Docker Compose

### Quick Start
1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Start the services:**
    ```bash
    docker compose up --build -d
    ```

3.  **Run Database Migrations:**
    This creates the tables and sets up the versioning triggers.
    ```bash
    docker compose exec web alembic upgrade head
    ```

4.  **Access the API:**
    * **GraphQL Playground:** http://localhost:8000/graphql

## Running Tests

The project includes a comprehensive test suite using `pytest`.

### 1. Run inside Docker (Recommended)
Execute the tests within the running container to ensure the environment matches:
```bash
docker compose exec web pytest
```

### 2. Run Locally
If you prefer running tests locally:
```bash
pip install -r requirements.txt
pytest
```

## API Usage Examples

### 1. Register a Contractor
```graphql
mutation {
  register(
    email: "bob@builder.com", 
    password: "securepass", 
    role: "CONTRACTOR"
  ) {
    accessToken
    user { id role }
  }
}
```
### 2. Create a Job
Header: Authorization: Bearer <YOUR_TOKEN>
```graphql
mutation {
  createJob(
    description: "Kitchen Remodel",
    location: "123 Main St",
    cost: "15000.00"
  ) {
    id
    currentVersion
    status
  }
}
```
### 3. Add a Sub-task
```graphql
mutation {
  addSubtask(jobId: 1, description: "Demolition", cost: "500.00") {
    id
    subtasks {
      description
      cost
    }
  }
}
```
### 4. Undo Last Change
If a mistake is made, revert the state instantly:
```graphql

mutation {
  undoLastChange(jobId: 1) {
    id
    description
    cost
    currentVersion # Decrements by 1
  }
}
```
## Assumptions, Risks, & Tradeoffs

### Assumptions
* **Currency:** All costs are handled as Decimals but assumed to be in a single currency (e.g., USD). No multi-currency conversion is currently implemented.
* **Role Rigidity:** A user is strictly either a `CONTRACTOR` or a `HOMEOWNER`. There is no support for a user holding multiple roles simultaneously.
* **Sub-task Independence:** Sub-tasks are currently treated as independent line items without complex dependency graphs (e.g., "Task B cannot start until Task A is finished" is not enforced).

### Risks
* **Snapshot Evolution:** Since snapshots are stored as JSON blobs, significant future schema changes (e.g., renaming the `cost` field to `price` in the Job model) would require a custom data migration script to parse and update historical JSON records.
* **Data Volume:** Infinite history tracking could lead to table bloat over time. A future archiving strategy might be needed for jobs older than X years.

### Tradeoffs
* **Snapshot Storage vs. Diffs:** We store full snapshots for every version.
    * *Benefit:* Restoring state is instant, atomic, and bug-free (no need to replay a stack of complex diffs).
    * *Cost:* Higher storage usage per update compared to storing only changed fields.
* **Async Complexity:** The entire stack uses asynchronous Python (`asyncpg`, `FastAPI`).
    * *Benefit:* High concurrency and throughput suitable for a scalable backend.
    * *Cost:* Increased complexity in debugging and ORM session management compared to synchronous frameworks.
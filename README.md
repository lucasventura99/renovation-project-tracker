# Renovation Project Tracker

A backend system designed to facilitate collaboration between Contractors and Homeowners on renovation projects. This project helps track job status, costs, and project history with robust data consistency.

## Tech Stack

* **Language:** Python 3.11+
* **Framework:** FastAPI (Async)
* **Database:** PostgreSQL 15
* **ORM:** SQLAlchemy 2.0 (Async)
* **API:** GraphQL (via Strawberry)
* **Infrastructure:** Docker & Docker Compose
* **Migrations:** Alembic

## Functional Requirements & Roadmap

### 1. User Roles & Authentication
* **Contractor:**
    * Can create and manage multiple renovation jobs.
    * Can assign Homeowners to specific jobs.
    * Full CRUD access to job details (Cost, Status, Description).
* **Homeowner:**
    * Read-only access to their assigned jobs.
    * Can view job progress and history.

### 2. Job Management (Core)
The system manages `Jobs` with the following data points:
* **Description:** Scope of work.
* **Location:** Property address.
* **Status:** `PLANNING`, `IN_PROGRESS`, `COMPLETED`, `CANCELED`.
* **Cost:** Financial tracking (using safe Decimal types).
* **Timeline:** Creation and update timestamps.

### 3. Advanced Feature: History & Undo/Redo
* **Audit Trail:** Every change to a Job is immutably recorded (Who, What, When).
* **Undo Capability:** Contractors can revert a Job to its previous state.
* **Transparency:** Homeowners can view the full history log of changes to their project.

### 4. Extended Feature: Sub-tasks
* Granular tracking of specific tasks within a Job (e.g., "Install Kitchen Cabinets").
* Each sub-task has its own description, deadline, and cost.

## ⚙️ Technical Design Goals

1.  **Data Consistency:** ACID compliance using PostgreSQL transactions, especially for the Undo/Redo engine.
2.  **Type Safety:** Strict typing across the entire stack (Python Type hints + GraphQL Schema).
3.  **Developer Experience:** One-command setup via Docker Compose.
4.  **Scalability:** Async I/O architecture suitable for high-concurrency environments.

---

## Getting Started

### Prerequisites
* Docker & Docker Compose

### Running the App
1.  Clone the repository.
2.  Run the application stack:
    ```bash
    docker-compose up --build
    ```
3.  Access the GraphQL Playground at:
    `http://localhost:8000/graphql`

---
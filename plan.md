# Master Planning Prompt: AI-Powered Ticket Management System

Act as a **senior software architect, backend engineer, frontend architect, database designer, and AI-agent engineer**.

I want to build a production-ready **AI-powered Ticket Management System** with the following technology stack:

* **Frontend:** Angular
* **Backend:** Python + FastAPI
* **Database:** PostgreSQL
* **AI Agent:** LangGraph
* **Authentication/Authorization:** Role-Based Access Control (RBAC)
* **API communication:** REST APIs
* **Real-time/interactive chatbot:** Design an appropriate approach using streaming/WebSockets/SSE where beneficial
* **Database access:** SQLAlchemy + Alembic
* **Validation:** Pydantic
* **Containerization:** Docker/Docker Compose

The goal is to create a system where predefined users can view and manage their support/grievance tickets through a dashboard, while also interacting with an AI chatbot that can understand their grievance and intelligently create a ticket after obtaining user approval.

---

## 1. Core Business Requirement

The application should have predefined users.

After authentication, a user should have access to a dashboard containing:

* Total tickets
* Open tickets
* In-progress tickets
* Resolved tickets
* Closed tickets
* Recently created tickets
* Previous ticket history
* Ticket status
* Ticket priority
* Ticket creation date
* Last updated date
* Ticket details

The user should have two primary ways to create a ticket:

### Option A — Manual Ticket Creation

The user can click "Create Ticket" and fill out a traditional ticket form.

Example fields:

* Title
* Description
* Category
* Subcategory
* Priority
* Attachments
* Additional metadata

The system should validate the form and create a ticket.

### Option B — AI Chat-Based Ticket Creation

The user can open an interactive chatbot.

The chatbot should allow the user to describe their grievance naturally.

Example:

> "My laptop has become extremely slow since yesterday and I can't work properly."

The AI agent should:

1. Understand the user's grievance.
2. Identify the likely issue/category.
3. Ask relevant follow-up questions.
4. Extract required ticket information.
5. Maintain conversational context.
6. Determine when enough information has been collected.
7. Generate a structured ticket draft.
8. Present the generated ticket form/card to the user inside the chat interface.
9. Allow the user to review and modify the information.
10. Ask for explicit confirmation.
11. Create the ticket only after user approval.
12. Return the created ticket number.
13. Reflect the newly created ticket immediately on the dashboard.
14. Allow the user to track its status.

---

# 2. AI Agent Requirements

Design the chatbot using **LangGraph** rather than a simple linear LLM chain.

The agent should have clearly defined states/nodes.

For example:

```text
User Message
      |
      v
Intent Detection
      |
      v
Grievance Understanding
      |
      v
Information Extraction
      |
      v
Missing Information?
   /          \
 Yes           No
 |              |
 v              v
Ask Question   Generate Ticket Draft
                  |
                  v
             User Review
              /       \
           Modify     Approve
             |          |
             v          v
        Update Draft  Create Ticket
                         |
                         v
                   Confirmation
```

Design a robust LangGraph workflow containing appropriate nodes such as:

* Conversation/Input Node
* Intent Classification Node
* Grievance Extraction Node
* Context/Memory Node
* Missing Information Detection Node
* Follow-Up Question Node
* Ticket Draft Generation Node
* Ticket Validation Node
* Human/User Approval Node
* Ticket Creation Node
* Ticket Status Node
* Response Generation Node
* Error/Recovery Node

Do not blindly follow these nodes if a better architecture exists. Explain the recommended graph.

---

# 3. Human-in-the-Loop Requirement

Ticket creation through AI must require explicit user approval.

The AI must **never automatically create a ticket merely because it believes it has enough information**.

The workflow should be:

```text
Conversation
    ↓
Information Gathering
    ↓
Ticket Draft
    ↓
User Review
    ↓
User Modification (optional)
    ↓
User Approval
    ↓
Ticket Creation
```

The system should distinguish between:

* Draft
* Pending approval
* Approved
* Created
* In Progress
* Resolved
* Closed
* Reopened
* Cancelled

Explain how LangGraph state/checkpointing can be used to pause execution while waiting for user approval and resume the workflow afterward.

---

# 4. AI-Generated Ticket Form

The chatbot should be capable of dynamically generating a structured ticket form/card from the conversation.

For example:

```text
-------------------------------------
Ticket Preview
-------------------------------------

Title:
Laptop Performance Issue

Description:
Laptop has become extremely slow since yesterday,
affecting normal work.

Category:
Hardware

Subcategory:
Laptop Performance

Priority:
High

Affected System:
Employee Laptop

-------------------------------------

[Edit Ticket] [Create Ticket]
-------------------------------------
```

The frontend should not simply render arbitrary HTML generated by the LLM.

Instead, define a **strict structured JSON schema** for AI-generated ticket drafts.

For example:

```json
{
  "title": "...",
  "description": "...",
  "category": "...",
  "subcategory": "...",
  "priority": "...",
  "metadata": {}
}
```

Explain how the backend should validate this structure using Pydantic before sending it to Angular.

---

# 5. AI Safety and Reliability

Design the AI workflow so that the LLM does not directly execute unrestricted database operations.

The AI should interact with the backend through controlled tools/functions.

For example:

```text
get_user_context()
get_ticket_categories()
get_ticket_status()
search_previous_tickets()
create_ticket()
update_ticket_draft()
```

Define which operations should be:

* Read-only
* User-confirmed
* Restricted to specific roles
* Completely unavailable to the LLM

The AI should never be allowed to arbitrarily generate SQL.

Explain how to prevent:

* Hallucinated ticket information
* Unauthorized ticket creation
* Unauthorized access to another user's tickets
* Invalid categories
* Invalid priorities
* Duplicate ticket creation
* Prompt injection
* Tool misuse
* Incorrect status changes
* Missing user approval
* Inconsistent ticket state

---

# 6. User Roles and RBAC

Design a proper role-based access-control model.

At minimum consider:

### User

Can:

* View own dashboard
* View own tickets
* Create tickets
* Create tickets manually
* Create tickets through AI
* View ticket status
* Add comments/replies
* Upload attachments
* Close eligible tickets
* Reopen eligible tickets if allowed
* Interact with chatbot

### Support Agent

Can:

* View assigned tickets
* View relevant user information
* Update ticket status
* Change priority
* Add comments
* Assign/reassign tickets
* Resolve tickets

### Manager

Can:

* View team tickets
* View analytics
* Assign tickets
* Reassign tickets
* Escalate tickets
* Monitor SLA
* View reports

### Administrator

Can:

* Manage users
* Manage roles
* Manage permissions
* Manage categories
* Manage ticket statuses
* Manage system configuration
* View all tickets
* View audit logs

Recommend whether permissions should be represented separately from roles.

Design the RBAC model in PostgreSQL.

---

# 7. Database Design

Create a normalized PostgreSQL schema.

At minimum evaluate these entities:

* users
* roles
* permissions
* user_roles
* role_permissions
* tickets
* ticket_categories
* ticket_subcategories
* ticket_statuses
* ticket_priorities
* ticket_comments
* ticket_attachments
* ticket_assignments
* ticket_history
* notifications
* chat_sessions
* chat_messages
* ai_ticket_drafts
* audit_logs

Do not assume every table is necessary. Explain the reasoning and propose the final schema.

For every table provide:

* Table name
* Purpose
* Columns
* PostgreSQL data types
* Primary key
* Foreign keys
* Unique constraints
* Indexes
* Important check constraints

Pay particular attention to:

* UUID vs integer IDs
* Timestamp handling
* Soft deletion
* Auditability
* Ticket history
* Referential integrity
* Indexing
* Concurrency
* Optimistic locking where appropriate

Provide an ER diagram using Mermaid.

---

# 8. Ticket Lifecycle

Design a clear ticket state machine.

For example:

```text
DRAFT
  |
  v
OPEN
  |
  v
ASSIGNED
  |
  v
IN_PROGRESS
  |
  v
RESOLVED
  |
  v
CLOSED
```

Also consider:

```text
OPEN → CANCELLED
IN_PROGRESS → ESCALATED
RESOLVED → REOPENED
CLOSED → REOPENED
```

Define which roles can perform each transition.

Do not allow arbitrary status updates from the frontend.

The backend should validate every transition.

Provide a state-transition matrix.

---

# 9. FastAPI Backend Architecture

Design a maintainable FastAPI architecture.

Prefer a structure similar to:

```text
backend/
├── app/
│   ├── main.py
│   ├── config/
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── agents/
│   ├── auth/
│   ├── middleware/
│   ├── events/
│   ├── utils/
│   └── db/
├── migrations/
├── tests/
└── Dockerfile
```

Recommend a better structure if appropriate.

Separate:

* API layer
* Business logic
* Repository/data-access layer
* AI agent layer
* Authentication/authorization
* Database models
* Pydantic schemas

Explain the dependency flow.

---

# 10. REST API Design

Design the complete API surface.

Include endpoints for:

### Authentication

```text
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
```

### Users

```text
GET /users/me
GET /users/me/dashboard
```

### Tickets

```text
GET    /tickets
POST   /tickets
GET    /tickets/{ticket_id}
PATCH  /tickets/{ticket_id}
POST   /tickets/{ticket_id}/comments
GET    /tickets/{ticket_id}/history
POST   /tickets/{ticket_id}/reopen
```

### Chat

```text
POST /chat/sessions
GET  /chat/sessions
GET  /chat/sessions/{session_id}
POST /chat/sessions/{session_id}/messages
```

### AI Ticket Draft

Design appropriate endpoints for:

* Getting current draft
* Updating draft
* Approving draft
* Rejecting draft
* Creating ticket from approved draft

Explain whether these operations should be REST endpoints, streaming endpoints, WebSockets, or SSE.

Provide request and response examples.

---

# 11. Angular Frontend Architecture

Design an Angular application with a clean modular structure.

Suggested areas:

```text
frontend/
├── src/
│   ├── app/
│   │   ├── core/
│   │   ├── shared/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── tickets/
│   │   ├── chat/
│   │   ├── admin/
│   │   └── layout/
```

Design:

* Authentication pages
* Dashboard
* Ticket list
* Ticket details
* Manual ticket form
* Chat interface
* AI-generated ticket preview
* Ticket status timeline
* Notifications
* Admin screens
* Agent screens

Use Angular best practices such as:

* Standalone components
* Reactive forms
* Route guards
* HTTP interceptors
* Signals where appropriate
* Lazy loading
* Typed API models
* Centralized authentication state
* Role/permission-aware navigation

---

# 12. Chat UI

Design the chatbot as a first-class application feature.

The UI should support:

* User messages
* AI responses
* Typing/streaming state
* Follow-up questions
* Ticket draft cards
* Editable ticket fields
* Approve button
* Reject button
* Regenerate/refine button
* Attachment support if required
* Ticket creation confirmation
* Link to created ticket
* Conversation history

The user should be able to say things like:

> "Actually, this started three days ago."

or:

> "Change the priority to medium."

The AI should update the draft rather than starting the process over.

Explain how the frontend and LangGraph state should remain synchronized.

---

# 13. Dashboard

Design a useful user dashboard.

Include:

### Summary cards

* Total Tickets
* Open
* In Progress
* Resolved
* Closed

### Ticket table

Columns:

* Ticket ID
* Title
* Category
* Priority
* Status
* Created At
* Updated At

### Ticket details

Display:

* Description
* Category
* Priority
* Current status
* Assigned agent
* Comments
* Attachments
* Status history
* Timeline

The dashboard should update after a ticket is created through the chatbot without requiring the user to manually refresh the browser.

Explain whether polling, SSE, WebSockets, or another mechanism is appropriate.

---

# 14. Ticket Status Tracking

Implement a visual timeline.

Example:

```text
✓ Ticket Created
      |
✓ Assigned
      |
✓ In Progress
      |
● Resolved
      |
○ Closed
```

Each status transition should record:

* Previous status
* New status
* Changed by
* Timestamp
* Optional comment/reason

Store this information in ticket history/audit tables.

---

# 15. Authentication and Security

Design secure authentication.

Discuss:

* JWT access tokens
* Refresh tokens
* Token rotation
* Password hashing
* Session management
* RBAC
* API authorization
* CORS
* CSRF considerations
* Rate limiting
* Input validation
* File upload security
* Audit logging
* Secret management
* PII protection

Explain what should be implemented in development versus production.

---

# 16. Observability

Design production observability.

Include:

* Structured logging
* Request IDs
* Error tracking
* API metrics
* Database metrics
* AI latency
* Token usage
* Agent execution tracing
* Failed agent runs
* Ticket creation failures

Explain how to trace a request such as:

```text
Angular
  ↓
FastAPI
  ↓
LangGraph
  ↓
LLM
  ↓
Tool
  ↓
PostgreSQL
```

using a correlation/request ID.

---

# 17. Testing Strategy

Create a comprehensive testing strategy.

Include:

### Backend

* Unit tests
* Service tests
* Repository tests
* API tests
* Authentication tests
* RBAC tests
* Ticket state-transition tests

### AI

Test conversations such as:

1. Complete grievance provided immediately.
2. Incomplete grievance.
3. User changes information.
4. User rejects draft.
5. User approves draft.
6. User changes priority.
7. Duplicate grievance.
8. Ambiguous grievance.
9. Prompt injection attempt.
10. Unauthorized tool request.
11. LLM produces malformed structured output.
12. Database failure during ticket creation.

### Frontend

* Component tests
* Form validation
* Route guard tests
* Chat interaction tests
* Ticket dashboard tests

### End-to-end

Test:

```text
Login
→ Dashboard
→ Open Chat
→ Describe Grievance
→ Answer Questions
→ Review Ticket
→ Approve
→ Ticket Created
→ Dashboard Updated
→ Open Ticket
→ Track Status
```

---

# 18. Error Handling

Design consistent API errors.

Use a standard structure such as:

```json
{
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "The requested ticket was not found.",
    "request_id": "..."
  }
}
```

Define appropriate error codes for:

* Authentication failures
* Authorization failures
* Validation errors
* Ticket not found
* Invalid status transition
* AI failure
* Draft failure
* Duplicate ticket
* Database failure
* Rate limit
* File upload failure

---

# 19. Concurrency and Idempotency

Pay special attention to the possibility that:

* The user clicks "Create Ticket" twice.
* The frontend retries a request.
* The network reconnects.
* The AI tool call is repeated.
* Two agents update the same ticket simultaneously.

Design idempotency mechanisms for ticket creation and other critical operations.

Explain how database transactions and unique constraints should be used.

---

# 20. Deployment Architecture

Design a production deployment architecture.

Consider:

```text
                 ┌───────────────┐
                 │    Angular    │
                 └───────┬───────┘
                         |
                         v
                 ┌───────────────┐
                 │ Reverse Proxy │
                 └───────┬───────┘
                         |
                         v
                 ┌───────────────┐
                 │    FastAPI    │
                 └───────┬───────┘
                         |
              ┌──────────┼──────────┐
              v          v          v
         PostgreSQL   LangGraph   Storage
                          |
                          v
                         LLM
```

Discuss:

* Docker
* Docker Compose for local development
* Production deployment
* PostgreSQL backups
* Object storage for attachments
* Environment configuration
* Secrets
* HTTPS
* Reverse proxy
* Horizontal scaling
* Background jobs if required

---

# 21. Recommended AI Architecture

Compare the following approaches:

### Approach A

LLM directly calls database functions.

### Approach B

LLM → controlled service tools → business layer → database.

### Approach C

LLM → LangGraph → domain tools → service layer → repository → database.

Recommend the best architecture for this application and explain why.

Prefer strong separation between AI reasoning and business/domain logic.

---

# 22. Data Flow

Explain the complete data flow for:

### Manual ticket creation

```text
Angular Form
→ FastAPI
→ Pydantic Validation
→ Authorization
→ Ticket Service
→ PostgreSQL
→ Response
→ Angular Dashboard
```

### AI ticket creation

```text
Angular Chat
→ FastAPI
→ LangGraph
→ LLM
→ Structured Extraction
→ Validation
→ Follow-up Questions
→ Ticket Draft
→ User Approval
→ Ticket Service
→ PostgreSQL
→ Ticket Created
→ Chat Confirmation
→ Dashboard Update
```

Explain each step in detail.

---

# 23. Database/API/AI Boundary

Clearly define responsibilities.

### Angular

Responsible for:

* Presentation
* User interaction
* Form validation for UX
* Rendering ticket drafts
* Authentication state
* Calling APIs

### FastAPI

Responsible for:

* Authentication
* Authorization
* Business rules
* Validation
* Ticket lifecycle
* Database operations
* AI orchestration APIs

### LangGraph

Responsible for:

* Conversation orchestration
* Context management
* Information extraction
* Asking questions
* Draft generation
* Controlled tool invocation
* Human approval workflow

### PostgreSQL

Responsible for:

* Persistent application state
* Users
* Roles
* Tickets
* Ticket history
* Chat persistence
* Audit records

The LLM must not become the source of truth for application state.

---

# 24. Deliverables

Produce the system design in the following order:

## Phase 1 — Requirements

Identify:

* Functional requirements
* Non-functional requirements
* User personas
* Roles
* Permissions
* Business rules
* Assumptions
* Open questions

## Phase 2 — Architecture

Provide:

* High-level architecture
* Component diagram
* Data-flow diagrams
* AI/LangGraph architecture
* Security architecture

Use Mermaid diagrams where useful.

## Phase 3 — Database

Provide:

* Complete PostgreSQL schema
* ER diagram
* Relationships
* Indexes
* Constraints
* Migration strategy

## Phase 4 — Backend

Provide:

* FastAPI project structure
* API specification
* Pydantic schemas
* SQLAlchemy models
* Service architecture
* Authentication architecture
* RBAC implementation
* Ticket state machine

## Phase 5 — AI

Provide:

* LangGraph state definition
* Graph nodes
* Tool definitions
* Tool permissions
* Structured output schemas
* Human-in-the-loop implementation
* Checkpointing strategy
* Conversation memory strategy
* Failure/retry strategy

## Phase 6 — Frontend

Provide:

* Angular architecture
* Component hierarchy
* Routes
* Guards
* Services
* State management
* Chat UI architecture
* Ticket form architecture
* Dashboard architecture

## Phase 7 — API Contract

Provide representative:

* Request JSON
* Response JSON
* Error JSON

for all important APIs.

## Phase 8 — Testing

Provide:

* Unit-test strategy
* Integration tests
* AI tests
* Security tests
* End-to-end tests

## Phase 9 — Deployment

Provide:

* Docker architecture
* Local development setup
* Production architecture
* Environment variables
* Database migration process
* Monitoring

## Phase 10 — Implementation Roadmap

Break development into incremental milestones.

For example:

```text
Milestone 1
Authentication + Users + RBAC

Milestone 2
Ticket CRUD + Database

Milestone 3
Ticket Lifecycle + History

Milestone 4
Angular Dashboard

Milestone 5
Manual Ticket Creation

Milestone 6
Chat Infrastructure

Milestone 7
LangGraph Agent

Milestone 8
AI Ticket Draft

Milestone 9
Human Approval + Ticket Creation

Milestone 10
Real-time Dashboard Updates

Milestone 11
Testing + Security

Milestone 12
Production Deployment
```

For every milestone provide:

* Objective
* Features
* Database changes
* Backend changes
* Frontend changes
* AI changes
* APIs involved
* Tests required
* Definition of done

---

# 25. Important Design Principles

Follow these principles throughout the design:

1. **PostgreSQL is the source of truth.**
2. **The LLM must not directly manipulate the database.**
3. **AI-generated information must be schema-validated.**
4. **Ticket creation through AI requires explicit user approval.**
5. **RBAC must be enforced server-side, not only in Angular.**
6. **Users must never be able to access another user's tickets unless their role permits it.**
7. **Ticket status changes must follow a controlled state machine.**
8. **All important ticket changes should be auditable.**
9. **AI conversations should be resumable.**
10. **AI failures must not corrupt ticket state.**
11. **Critical operations should be transactional and idempotent.**
12. **The frontend should never be trusted for authorization.**
13. **LLM output should be treated as untrusted input.**
14. **Business rules belong in the backend/domain layer, not inside prompts.**
15. **The architecture should allow the LLM provider to be changed later.**

---

# Final Output Requirement

Do not jump directly into implementation code.

First produce a **complete technical blueprint** for the system.

Clearly identify any ambiguous requirements and make reasonable assumptions.

Where multiple architectural approaches are possible, compare them and recommend one.

The final blueprint should be detailed enough that a development team can use it as the foundation for implementation without having to redesign the system architecture later.

Prioritize:

**security → correctness → maintainability → scalability → AI reliability → developer experience.**

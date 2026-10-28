# Smart Utility & Billing Management Platform

A utility management system built with **Python, Django REST Framework, PostgreSQL, and React**. The platform simulates the management of prepaid electricity or water meters, customer accounts, meter readings, billing, payments, and customer support.

The project is designed to address real engineering challenges such as duplicate payment notifications, unauthorized access, abnormal meter readings, high traffic, and safe software releases.

> **Project status:** Requirements and implementation roadmap  
> **Environment:** Development/demo data only. Do not use real customer financial data or production payment credentials.

## Table of Contents

- [1. Problem Statement](#1-problem-statement)
- [2. Project Objectives](#2-project-objectives)
- [3. Scope and Features](#3-scope-and-features)
- [4. User Roles and Permissions](#4-user-roles-and-permissions)
- [5. Technology Stack](#5-technology-stack)
- [6. High-Level Architecture](#6-high-level-architecture)
- [7. Core Data Models](#7-core-data-models)
- [8. Functional Requirements](#8-functional-requirements)
- [9. Non-Functional Requirements](#9-non-functional-requirements)
- [10. Industry Challenges](#10-industry-challenges)
- [11. API Requirements](#11-api-requirements)
- [12. Testing and Quality Assurance](#12-testing-and-quality-assurance)
- [13. Security Requirements](#13-security-requirements)
- [14. DevOps and Deployment](#14-devops-and-deployment)
- [15. Eight-Week Roadmap](#15-eight-week-roadmap)
- [16. Initial Acceptance Criteria](#16-initial-acceptance-criteria)
- [17. Suggested Repository Structure](#17-suggested-repository-structure)
- [18. Getting Started](#18-getting-started)
- [19. Definition of Done](#19-definition-of-done)
- [20. Future Enhancements](#20-future-enhancements)

---

## 1. Problem Statement

Utility providers need reliable systems for managing customers, smart meters, consumption readings, bills, payments, and fault reports. Poorly designed systems can lead to:

- Payments being credited more than once when a provider retries a callback.
- Customers viewing or changing another customer's information.
- Missing, duplicated, or abnormal meter readings.
- Incorrect account balances caused by concurrent transactions.
- Slow APIs when many meters submit readings at the same time.
- Regressions introduced by software updates.
- Poor visibility into failed transactions and support requests.

This project will implement a realistic demonstration platform that addresses these problems through secure APIs, reliable transaction processing, automated tests, monitoring, and repeatable deployment.

## 2. Project Objectives

The project should demonstrate the ability to:

1. Design and build a maintainable Django REST API.
2. Model relational data and enforce integrity with PostgreSQL.
3. Implement authentication, authorization, and role-based access.
4. Process meter readings and calculate bills using configurable tariffs.
5. Handle payment notifications safely and prevent duplicate credits.
6. Build a customer-support ticket workflow.
7. Write unit, integration, API, security, and regression tests.
8. Use background jobs for suitable asynchronous work.
9. Package services with Docker and automate checks using CI/CD.
10. Document, deploy, monitor, and explain a production-minded application.

## 3. Scope and Features

### 3.1 Authentication and access control

- Customer registration, login, logout, and password-reset flow.
- Token-based API authentication, such as Simple JWT.
- Roles: customer, technician, support agent, and administrator.
- Server-side permission checks for every protected resource.
- Audit logs for sensitive administrative and financial actions.
- Validation and consistent error responses.

### 3.2 Smart meter management

- Register, view, update, activate, and deactivate meters.
- Assign a meter to an authorized customer.
- Store timestamped meter readings.
- Validate reading values, timestamps, meter status, and duplicate submissions.
- Flag missing, out-of-range, or suspicious readings for review.
- Display reading history and consumption trends.
- Provide an API suitable for simulated IoT devices.

### 3.3 Tariffs, billing, and payments

- Create and manage configurable tariffs.
- Calculate charges using documented rules.
- Record payment attempts and provider references.
- Simulate mobile-money callbacks in development.
- Handle repeated callbacks idempotently.
- Maintain an append-only account ledger for credits and debits.
- Reconcile pending, failed, and successful transactions.
- Use database transactions and constraints to protect financial consistency.

**Important:** A payment notification must not be trusted solely because it reaches the endpoint. A real integration must verify the provider's signature or use its approved verification process. The demo callback must be clearly marked as simulated.

### 3.4 Customer support

- Customers create fault or billing tickets.
- Support agents categorize, prioritize, assign, and update tickets.
- Technicians record diagnosis, work performed, and resolution.
- Track ticket status, timestamps, and resolution duration.
- Notify relevant users when important status changes occur.
- Keep a history of ticket changes.

### 3.5 Administration and reporting

- Dashboard summaries for customers, meters, readings, payments, and tickets.
- Search, filtering, sorting, and pagination.
- Reports for usage, billing, payment status, and unresolved tickets.
- Audit-log access restricted to authorized roles.
- Export functionality may be added after core workflows are stable.

## 4. User Roles and Permissions

| Role | Typical permissions |
|---|---|
| Customer | View own profile, assigned meters, readings, bills, payments, and tickets; create support tickets. |
| Technician | View assigned work orders or tickets and record diagnostic and repair updates. |
| Support agent | Manage customer support tickets and view only the customer information needed for support. |
| Administrator | Manage users, meters, tariffs, roles, and operational reports; access sensitive actions with audit logging. |
| Simulated meter/device | Submit readings only for an authorized device identity, using a separate device-authentication mechanism. |

Permissions must be enforced by the backend. Hiding a button in React is not an authorization control.

## 5. Technology Stack

| Area | Technology | Purpose |
|---|---|---|
| Language | Python | Backend implementation |
| Backend framework | Django | Models, admin, authentication, and application structure |
| API | Django REST Framework | REST endpoints, serializers, permissions, and API views |
| Database | PostgreSQL | Relational data and transaction integrity |
| Authentication | Django authentication + Simple JWT | User authentication for API clients |
| Frontend | React + Vite | Responsive customer and administration interface |
| API documentation | OpenAPI / Swagger, e.g. drf-spectacular | Interactive API reference |
| Background jobs | Celery + Redis | Notifications, scheduled reconciliation, and other asynchronous work |
| Backend tests | pytest + pytest-django + DRF APIClient | Unit and API testing |
| Browser automation | Playwright or Selenium | End-to-end regression testing |
| Containerization | Docker + Docker Compose | Reproducible local development and deployment |
| CI/CD | GitHub Actions | Automated linting, tests, and build checks |
| Monitoring/logging | Structured application logs; production monitoring to be selected | Diagnosis and operational visibility |

Use supported, stable dependency versions and pin them in dependency files. Reassess versions before deployment.

## 6. High-Level Architecture

```text
React Web Application
         |
         | HTTPS / JSON API
         v
Django REST Framework
         |
         +---- Authentication and Permissions
         +---- Meter and Reading Services
         +---- Tariff and Billing Services
         +---- Payment and Ledger Services
         +---- Support Ticket Services
         |
         +---------- PostgreSQL
         |
         +---------- Redis <----> Celery Workers
         |
         +---------- Logs / Monitoring

Simulated Meter Device --------> Authenticated Reading API
Simulated Payment Provider ----> Verified/Simulated Callback API
```

Keep business rules in service functions or domain-focused modules rather than duplicating them across API views. Use database constraints and transactions as a final line of protection for critical operations.

## 7. Core Data Models

The following is the initial domain model. Exact fields and relationships should be refined during implementation.

### User

- UUID primary key (recommended).
- Name, unique email, and optional phone number.
- Password hash managed by Django; never store plaintext passwords.
- Role and account status.
- Created and updated timestamps.

Use a custom Django user model before the first migration if the project needs one.

### Meter

- UUID primary key.
- Unique meter number.
- Customer/owner foreign key.
- Active/inactive status.
- Installation and audit timestamps.
- Optional device identifier and last-contact timestamp.

### MeterReading

- UUID or suitable primary key.
- Meter foreign key.
- Reading value using an appropriate decimal/numeric field.
- Device-reported timestamp and server-received timestamp.
- Unique device event or idempotency identifier where available.
- Validation/review status and relevant metadata.

Define whether readings represent cumulative meter values or interval consumption. Reject or flag invalid readings according to the documented meter rules.

### Tariff

- Name and description.
- Rate and currency.
- Effective start/end dates.
- Optional tariff rules or tiers.
- Active status and audit fields.

Use `DecimalField` or an equivalent exact numeric representation for money. Document rounding rules and use integer minor units or fixed-precision decimals consistently where appropriate.

### Bill

- Customer and relevant meter foreign keys.
- Billing period.
- Consumption quantity and tariff snapshot.
- Amount due and currency.
- Status: draft, issued, partially paid, paid, overdue, or cancelled, as applicable.
- Issue and due timestamps.

A bill should retain the tariff/rate used at the time it was calculated so that later tariff changes do not silently rewrite historical bills.

### Payment

- UUID primary key.
- Customer and related bill/account references.
- Unique provider transaction reference when supplied.
- Amount and currency.
- Status: pending, successful, failed, reversed, or another explicitly documented state.
- Idempotency key or provider event identifier.
- Provider timestamps and processing timestamps.

### LedgerEntry

- UUID primary key.
- Account/customer reference.
- Entry type and signed amount or debit/credit direction.
- Currency.
- Related payment or billing transaction reference.
- Unique transaction/idempotency reference where applicable.
- Creation timestamp and audit metadata.

Treat posted ledger entries as immutable. Correct mistakes with reversing/adjustment entries instead of silently editing posted financial history.

### SupportTicket

- UUID primary key.
- Customer, optional meter, assignee, and creator references.
- Category, title, description, priority, and status.
- Created, updated, assigned, and resolved timestamps.
- Resolution notes where appropriate.

### AuditLog

- Actor, action, resource type and identifier.
- Timestamp and request/correlation identifier.
- Carefully selected before/after metadata, excluding passwords, tokens, and other secrets.

## 8. Functional Requirements

Requirements should eventually become tracked issues with acceptance criteria.

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | A user can register and authenticate securely. | Must |
| FR-02 | The API enforces role and object-level permissions. | Must |
| FR-03 | An administrator can register a meter and assign it to a customer. | Must |
| FR-04 | An authorized device can submit a meter reading. | Must |
| FR-05 | The system validates and detects duplicate or suspicious readings. | Must |
| FR-06 | Authorized staff can configure tariffs. | Must |
| FR-07 | The system calculates bills using documented tariff rules. | Must |
| FR-08 | Repeated payment callbacks cannot create duplicate credits. | Must |
| FR-09 | Account changes are represented in an auditable ledger. | Must |
| FR-10 | Customers can create and track support tickets. | Must |
| FR-11 | Staff can assign and resolve tickets according to permissions. | Must |
| FR-12 | API collections support pagination and filtering. | Should |
| FR-13 | The system sends asynchronous notifications. | Should |
| FR-14 | Authorized staff can view operational reports. | Should |
| FR-15 | The system supports documented data export. | Could |

## 9. Non-Functional Requirements

- **Security:** Protect credentials, secrets, personal data, and financial records.
- **Correctness:** Financial operations must be consistent and repeatable.
- **Reliability:** Expected failures should produce clear, recoverable states.
- **Performance:** Establish baseline response-time and throughput targets, then measure them under load.
- **Scalability:** Support pagination, suitable indexes, and asynchronous processing where justified.
- **Maintainability:** Separate responsibilities, use clear names, and document non-obvious business rules.
- **Observability:** Record useful structured logs, error context, and correlation IDs without leaking sensitive data.
- **Accessibility and usability:** Build a responsive interface with clear validation and error messages.
- **Portability:** Make the development environment reproducible using Docker Compose.
- **Data integrity:** Use foreign keys, uniqueness constraints, appropriate decimal types, and transactions.

Do not claim that the system is production-ready until its security, performance, recovery, and deployment requirements have been verified.

## 10. Industry Challenges

### Challenge A: Duplicate payment callbacks

**Scenario:** The payment provider retries a callback three times.

**Expected behavior:**
- The callback is authenticated or verified according to the provider's protocol.
- A stable provider event or transaction reference identifies duplicates.
- Database constraints prevent duplicate financial posting.
- Payment state changes and ledger posting are performed atomically.
- A retry returns a safe response without applying the credit again.
- Concurrent duplicate requests are tested, not just sequential requests.

**Skills:** Idempotency, database transactions, unique constraints, race-condition testing, and reconciliation.

### Challenge B: Unauthorized object access

**Scenario:** Customer A changes a meter ID in the URL to access Customer B's meter.

**Expected behavior:**
- The API denies access and does not expose private data.
- Similar checks apply to readings, bills, payments, and tickets.
- Tests cover read, update, delete, and list endpoints where applicable.
- Administrative and support access is limited to documented permissions.

**Skills:** Object-level authorization, DRF permissions, API security testing, and OWASP API Security concepts.

### Challenge C: High traffic and ingestion

**Scenario:** Many meters submit readings in a short interval.

**Expected behavior:**
- Pagination and appropriate database indexes are used.
- Duplicate submissions are safely handled.
- Load tests measure throughput, latency, and error rates.
- Slow queries and bottlenecks are identified with evidence.
- Background jobs are used for work that does not need to block an API response.

**Skills:** Query optimization, profiling, asynchronous processing, load testing, and capacity planning.

### Challenge D: Safe releases

**Scenario:** A tariff change accidentally breaks existing billing behavior.

**Expected behavior:**
- Automated tests cover critical billing and payment paths.
- CI runs checks on proposed changes.
- Database migrations are reviewed and tested.
- Regression tests catch the issue before release.
- Deployment and rollback/recovery steps are documented.

**Skills:** Test strategy, regression testing, CI/CD, migration safety, and release engineering.

## 11. API Requirements

Use a consistent prefix such as `/api/v1/`. Exact paths can be decided during implementation.

| Resource | Example operations |
|---|---|
| Authentication | Register, login, refresh token, logout/revocation, current user |
| Users | Read/update permitted profile fields; administrative user management |
| Meters | List, create, retrieve, update status, assign owner |
| Readings | Submit reading, list readings, retrieve reading details |
| Tariffs | List active tariffs; authorized tariff administration |
| Bills | List bills, retrieve bill details, calculate/issue bills through authorized workflows |
| Payments | Initiate a simulated payment, receive provider callback, retrieve payment status |
| Ledger | Retrieve permitted account transactions; restricted administrative reports |
| Tickets | Create, list, retrieve, assign, update status, resolve |
| Reports | Usage, billing, payment reconciliation, ticket metrics |
| Health | Readiness/liveness endpoints appropriate to deployment |

API conventions:

- Use appropriate HTTP methods and status codes.
- Validate request payloads with serializers.
- Return predictable error structures.
- Paginate collection endpoints.
- Filter returned records by the authenticated user's permissions.
- Version the API and document request/response examples.
- Never expose password hashes, tokens, secrets, or unnecessary provider payloads.
- Apply throttling to authentication and other abuse-prone endpoints.
- Use a separate device identity/authentication mechanism for simulated meters rather than reusing customer credentials.

## 12. Testing and Quality Assurance

### Test levels

1. **Unit tests:** Tariff calculations, validation rules, state transitions, and idempotency helpers.
2. **Integration tests:** Database transactions, ledger posting, payment callbacks, and Celery integration.
3. **API tests:** Authentication, permissions, validation, pagination, status codes, and error responses.
4. **Security tests:** Cross-customer access, privilege escalation, input validation, and rate-limit behavior.
5. **Concurrency tests:** Multiple simultaneous callbacks or reading submissions.
6. **End-to-end tests:** Register/login, view a meter, submit a simulated payment, and raise a support ticket.
7. **Performance tests:** Reading ingestion and important list/report endpoints under a documented workload.
8. **Regression tests:** Preserve a test for every confirmed defect.

### Minimum critical test cases

- Invalid login is rejected.
- A customer cannot access another customer's meter, bill, or payment.
- An inactive meter cannot submit a normal reading.
- Duplicate reading events do not create duplicate consumption records.
- Repeated payment callbacks credit the ledger only once.
- Two simultaneous callbacks cannot double-credit an account.
- Failed payment processing does not leave a partially posted financial transaction.
- Posted ledger entries cannot be silently edited or deleted through normal application APIs.
- Invalid tariff or amount values are rejected.
- Ticket status transitions follow the documented workflow.
- CI fails when a critical test fails.

Use realistic test data, isolated test databases, and factories/fixtures where useful. Never run destructive tests against production data.

## 13. Security Requirements

- Use Django's password hashing and password validation facilities.
- Store secrets in environment variables or a secrets manager, never in source control.
- Require HTTPS in deployed environments.
- Configure allowed hosts, CORS, CSRF, cookie, and token behavior intentionally.
- Apply authentication and least-privilege authorization to protected endpoints.
- Validate all input on the server.
- Use ORM operations and parameterized queries; avoid unsafe raw SQL.
- Rate-limit sensitive endpoints and protect against brute-force attempts.
- Verify payment-provider callbacks according to the provider's official integration rules.
- Use unique constraints and atomic database operations for financial consistency.
- Redact credentials, access tokens, and sensitive personal information from logs.
- Keep dependencies updated and scan them for known vulnerabilities.
- Maintain audit logs for privileged and financial operations.
- Define backup, restore, data retention, and incident-response procedures before production use.

## 14. DevOps and Deployment

### Local development

- Docker Compose services for Django, PostgreSQL, Redis, Celery worker, and optionally the React frontend.
- Persistent database volume for development.
- Environment-based configuration and an example environment file with placeholders only.
- Health checks and service dependencies configured intentionally.
- Database migrations and test commands documented.

### Continuous integration

A GitHub Actions pipeline should:

1. Install pinned dependencies.
2. Run formatting/lint checks.
3. Run unit, integration, and API tests.
4. Build the frontend.
5. Build container images where appropriate.
6. Fail clearly when required checks fail.

### Deployment checklist

- Configure secrets and environment-specific settings.
- Use a production-grade WSGI/ASGI deployment configuration.
- Run migrations as a controlled release step.
- Collect static assets and serve them appropriately.
- Configure HTTPS, trusted hosts, CORS, and secure cookies/tokens.
- Set up logging, health checks, database backups, and restore testing.
- Verify monitoring and alerts.
- Document rollback and incident-recovery procedures.

## 15. Eight-Week Roadmap

| Week | Focus | Deliverable |
|---|---|---|
| 1 | Requirements and data design | User stories, ER diagram, Django project, PostgreSQL connection |
| 2 | Authentication and permissions | Registration/login, roles, protected endpoints, authorization tests |
| 3 | Meter management | Meter CRUD, reading ingestion, validation, pagination |
| 4 | Billing and payments | Tariffs, bills, payment simulation, idempotency, ledger |
| 5 | Customer support | Ticket creation, assignment, workflow, notifications |
| 6 | Quality assurance | Unit/API/security/concurrency tests and regression suite |
| 7 | Frontend and delivery | React dashboard, Docker Compose, CI pipeline |
| 8 | Production readiness | Deployment, API docs, load testing, security review, demo |

The schedule is a guide. Spend additional time on a week if its acceptance criteria are not met.

## 16. Initial Acceptance Criteria

The first milestone is complete when all of the following are demonstrated:

- [ ] A customer can register and authenticate.
- [ ] An administrator can create a meter and assign it to a customer.
- [ ] The customer can retrieve their own meter but cannot access another customer's meter.
- [ ] An authorized simulated device can submit a valid reading.
- [ ] Invalid and duplicate readings are handled according to documented rules.
- [ ] Automated tests cover the successful and rejected workflows.
- [ ] Setup instructions allow another developer to run the project locally.

The payment milestone is complete when:

- [ ] A simulated payment can be recorded.
- [ ] A verified/simulated callback updates payment state safely.
- [ ] Repeated and concurrent callbacks cannot create duplicate ledger credits.
- [ ] A failed transaction does not leave inconsistent financial records.
- [ ] Reconciliation can identify payments that remain pending or need review.

## 17. Suggested Repository Structure

```text
smart-utility-platform/
├── backend/
│   ├── config/                 # Django settings, URLs, ASGI/WSGI
│   ├── apps/
│   │   ├── accounts/           # User model, authentication, permissions
│   │   ├── meters/             # Meters and readings
│   │   ├── billing/            # Tariffs and bills
│   │   ├── payments/           # Payment callbacks and ledger
│   │   ├── support/            # Tickets and workflow
│   │   └── audit/              # Audit events
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt        # Or a pinned pyproject.toml workflow
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── api.md
│   └── test-plan.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── .gitignore
├── compose.yaml
└── README.md
```

Adjust the layout as the project grows. Avoid creating unnecessary abstraction layers before there is a real need.

## 18. Getting Started

### Prerequisites

- Python version supported by the selected Django release.
- Git.
- PostgreSQL, or Docker with Docker Compose.
- Node.js and npm for the React frontend.
- A code editor such as VS Code.

### Initial backend setup

The following commands are a starting point for a local setup; database configuration and dependencies still need to be added.

```bash
# Create and enter the project folder
mkdir smart-utility-platform
cd smart-utility-platform

# Create the backend environment
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux alternative:
# source .venv/bin/activate

mkdir backend
cd backend

pip install django djangorestframework psycopg[binary] djangorestframework-simplejwt drf-spectacular
django-admin startproject config .
python manage.py startapp accounts
python manage.py startapp meters
python manage.py startapp billing
python manage.py startapp payments
python manage.py startapp support
python manage.py startapp audit
```

Before creating the first migrations:

1. Configure the custom user model, if using one.
2. Configure PostgreSQL and environment variables.
3. Add the apps and REST framework settings.
4. Define the initial models and constraints.
5. Review settings so secrets and development-only configuration are not committed.

Then create and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

These commands do not complete the application by themselves; API views, serializers, permissions, business services, tests, and frontend pages must be implemented.

### Environment variables

Create a local `.env` file based on `.env.example`. Use placeholder values in the committed example, such as:

```dotenv
DJANGO_SECRET_KEY=replace-for-local-development
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://app_user:local_password@localhost:5432/smart_utility
REDIS_URL=redis://localhost:6379/0
```

Do not commit `.env`, real credentials, private keys, or production payment-provider secrets.

## 19. Definition of Done

A feature is considered done when:

- Requirements and acceptance criteria are documented.
- Implementation follows the project's code and architecture conventions.
- Validation and authorization are enforced server-side.
- Automated tests cover normal, invalid, and relevant failure paths.
- Critical database operations preserve integrity under retries and concurrency.
- API documentation is updated.
- Logging is useful but does not expose secrets or sensitive data.
- CI checks pass.
- Relevant setup, deployment, and recovery instructions are updated.

## 20. Future Enhancements

Once the core application is reliable, consider:

- Real payment-provider sandbox integration.
- MQTT-based smart-meter ingestion.
- Device certificates or per-device credentials.
- Anomaly detection for unusual consumption patterns.
- Email/SMS notifications through a provider sandbox.
- More advanced usage analytics and forecasting.
- Role-specific React dashboards.
- Infrastructure-as-code and more advanced observability.
- Load testing at a defined target scale.
- Accessibility and usability testing.

---

## Portfolio Deliverables

By the end of the project, aim to publish:

- A clear GitHub repository with this README and setup instructions.
- An architecture diagram and data model.
- A documented API with example requests and responses.
- A meaningful automated test suite and visible CI status.
- A deployed demo using synthetic data.
- Screenshots or a short walkthrough of the main workflows.
- A short engineering write-up explaining idempotent payment processing, authorization, concurrency handling, and testing decisions.

**Success is not measured by the number of features alone.** It is measured by whether the system handles realistic failures safely, is testable by another developer, and can be deployed and maintained reliably.

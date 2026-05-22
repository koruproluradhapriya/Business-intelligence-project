# InsightIQ Features Documentation

InsightIQ is an AI-powered universal business intelligence platform built to transform uploaded operational data into analytics, dashboards, forecasts, chat-ready explanations, and persistent workspace intelligence.

This document explains the system in product, engineering, and architecture terms.

## 1. Platform Summary

InsightIQ combines:

- data ingestion
- schema inference
- analytics generation
- dashboard rendering
- AI-style Q&A
- forecasting
- persistence in MongoDB Atlas
- JWT-secured user access

The result is a business intelligence workflow that works on top of flexible datasets instead of requiring a rigid warehouse schema from day one.

## 2. Product Features

### 2.1 Authentication

Users can:

- create accounts
- log in
- refresh tokens
- fetch current profile
- update name and business name

Authentication is JWT-based and user state is persisted in MongoDB.

Primary storage:

- `users`
- `user_sessions`
- `activity_logs`
- `settings`
- `notifications`

### 2.2 Universal Dataset Uploads

Users can upload:

- CSV
- XLSX
- XLS
- JSON
- TSV
- Parquet

The upload pipeline stores raw metadata, processed schema output, and downstream analytics references.

Primary storage:

- `uploads`
- `datasets`

### 2.3 Dynamic Dashboard Generation

Dashboards are not fixed templates. The backend computes analytics based on inferred dataset meaning and stores a dashboard snapshot that the frontend can render directly.

Dashboard components include:

- KPIs
- trend charts
- dimensional breakdowns
- data quality summaries
- schema mapping
- recommendations
- forecast summaries

Primary storage:

- `dashboards`
- `analytics`
- `settings`

### 2.4 AI Chat With Data

Users can ask questions about the latest uploaded dataset. Responses are produced from the persisted analytics context and saved for later use.

Examples:

- revenue interpretation
- performance comparison
- anomaly explanation
- forecast interpretation
- schema understanding

Primary storage:

- `chat_history`
- `insights`
- `activity_logs`

### 2.5 Forecasting

InsightIQ evaluates time-series suitability and computes forward-looking predictions when enough historical data is present.

Forecast output includes:

- historical series
- predicted future periods
- confidence data
- model candidate summary
- explanatory narrative
- anomaly-awareness markers

Primary storage:

- `forecasts`
- `analytics`
- `reports`

### 2.6 Recommendations and Insights

The system generates actionable observations based on:

- data quality
- anomalies
- KPI behavior
- forecast readiness
- inventory behavior
- inferred business concepts

Primary storage:

- `insights`
- `analytics`
- `notifications`

### 2.7 Reports and Exports

The system persists report-ready summary objects and export metadata so downloadable reporting can be layered in cleanly.

Primary storage:

- `reports`
- `exports`

### 2.8 Connectors

The current architecture includes persisted connector metadata as the foundation for future recurring sync integrations.

Primary storage:

- `connectors`

## 3. AI Workflow

InsightIQ’s AI workflow is hybrid.

### Stage 1: deterministic data intelligence

The platform first computes structured analytics from uploaded data:

- schema detection
- column typing
- business meaning inference
- trends
- outliers
- KPI extraction
- forecast signals

### Stage 2: business framing

Services transform computed analytics into:

- executive summaries
- recommendations
- AI-style answers
- chart selections

### Stage 3: optional external AI

Anthropic and future OpenAI/LangChain flows can enrich outputs, but the core system is designed to remain functional without a hosted LLM.

## 4. Analytics Pipeline

The analytics pipeline is centered in backend services.

### 4.1 Input

- uploaded file path
- upload type
- normalized data frame
- column profile report
- inferred schema
- semantic groups
- file metadata

### 4.2 Processing

The backend computes:

- profile metrics
- dimensional summaries
- time-series aggregates
- anomaly candidates
- charts
- KPIs
- recommendations
- executive summaries
- chat suggestions
- forecast payloads

### 4.3 Output

The final analytics payload is stored in:

- `analytics`

Derived artifacts are also stored in:

- `dashboards`
- `forecasts`
- `insights`
- `reports`
- `exports`

## 5. Forecasting System

The forecasting engine evaluates uploaded historical data and chooses the strongest available predictive representation.

### Forecasting behavior

- validates time-series sufficiency
- normalizes historical sequence
- evaluates model candidates
- computes forecast rows
- calculates confidence summaries
- generates explanation text

### Forecast consumers

- dashboard page
- forecast page
- AI chat answers
- report summaries

## 6. Connector Architecture

The connector layer is currently metadata-first and API-ready.

Each connector record may store:

- connector name
- connector type
- config payload
- status
- timestamps

This supports future:

- scheduled imports
- webhook-driven updates
- credential vault indirection
- warehouse sync pipelines

## 7. Dashboard Generation Logic

Dashboard generation is driven by dataset semantics.

### Inputs

- inferred column roles
- dataset profile
- available numerical measures
- categorical dimensions
- date fields

### Dashboard outputs

- KPI cards
- profile blocks
- line, bar, pie, area, and scatter charts
- recommendations
- schema mapping panels
- chat prompts

The dashboard is persisted so the system can reload the latest state without recomputing everything on every page load.

## 8. Export System

The export layer currently stores export metadata and report artifacts, preparing the platform for binary generation such as:

- PDF board reports
- CSV extracts
- Excel packs
- JSON analytics exports

Suggested next step:

- connect the `exports` collection to a file generation worker and object storage path

## 9. Authentication Flow

### Register

1. user submits name, email, and password
2. password is hashed with bcrypt
3. user document is created
4. default settings are created
5. welcome notification is created
6. session and activity records are logged
7. access and refresh tokens are issued

### Login

1. email and password are verified
2. session record is created
3. access and refresh tokens are returned

### Authenticated requests

The frontend stores the JWT and sends it in the `Authorization` header through the shared Axios client.

## 10. MongoDB Collections

### `users`

- profile identity
- hashed password
- plan
- timestamps

### `user_sessions`

- login session token
- request metadata
- start and last-seen timestamps

### `settings`

- theme
- dashboard layout
- export defaults
- notification preferences

### `uploads`

- file metadata
- file path
- schema and profile context
- upload type

### `datasets`

- normalized dataset summary
- upload linkage
- semantic metadata

### `analytics`

- canonical analytics payload
- KPIs
- charts
- insights
- recommendations
- forecast block

### `dashboards`

- dashboard-specific persisted view state

### `forecasts`

- persisted forecast payloads

### `insights`

- analytics-derived and chat-derived insight artifacts

### `reports`

- executive report metadata
- summary block
- high-level highlights

### `exports`

- export artifacts and readiness metadata

### `connectors`

- connector definitions
- integration config
- sync status

### `notifications`

- welcome notifications
- system events
- dataset processed events

### `activity_logs`

- auditable record of user and system actions

### `chat_history`

- user questions
- answer payloads
- analytics snapshots

## 11. API Routes

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `PUT /api/auth/profile`

### Uploads

- `POST /api/upload/dataset`
- `POST /api/upload/csv`
- `GET /api/upload/history`
- `DELETE /api/upload/<upload_id>`

### Analytics

- `GET /api/analytics/dashboard`
- `GET /api/analytics/profile`
- `GET /api/analytics/products`
- `GET /api/analytics/trends`
- `GET /api/analytics/segments`
- `POST /api/analytics/chat`
- `GET /api/analytics/chat/history`

### Forecasts

- `GET /api/forecast/sales`

### Recommendations

- `GET /api/recommendations`

### Inventory

- `GET /api/inventory/status`

### Workspace

- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/reports`
- `GET /api/connectors`
- `POST /api/connectors`
- `GET /api/notifications`
- `POST /api/notifications/<notification_id>/read`

## 12. Frontend Pages

### Login page

- authenticates existing users

### Register page

- creates a new account

### Upload page

- submits supported files and starts analytics processing

### Dashboard page

- shows KPIs, schema insights, charts, recommendations, and chat

### Analytics page

- presents deeper analytics slices

### Forecast page

- presents historical vs predicted values and model confidence

### Inventory page

- shows inventory analysis and stock recommendations

### Recommendations page

- displays recommendation feed

### Settings page

- profile updates
- theme preferences
- persisted workspace settings

## 13. Backend Services

### `csv_processor.py`

- parses incoming files
- normalizes tabular data
- prepares preview and schema context

### `analytics_service.py`

- computes KPIs, charts, dimensional summaries, and executive content

### `forecast_service.py`

- produces forecast payloads and explanation blocks

### `ai_insight_service.py`

- produces insight-oriented natural language outputs

### `recommendation_service.py`

- shapes recommendation content from analytics state

### `data_intelligence_service.py`

- handles deeper schema and column intelligence tasks

### `persistence_service.py`

- centralizes durable writes for uploads, dashboards, forecasts, reports, chat, notifications, settings, and connectors

### `database/mongo.py`

- validates configuration
- initializes MongoDB Atlas
- creates indexes
- exposes shared collection helpers
- provides health checks

## 14. Production Notes

### Security

- do not commit `.env` files
- do not expose MongoDB credentials publicly
- rotate Atlas credentials before public deployment
- store secrets in deployment environment variables or secret managers

### Reliability

- configure Atlas IP allowlists correctly
- use managed process runners like Gunicorn
- keep upload directories mounted or externalized
- add background jobs for long-running report/export tasks

### Scalability

- offload file processing to queues
- move generated exports to object storage
- introduce worker pools for connector sync and report generation

## 15. Resume / Demo Value

InsightIQ demonstrates:

- full-stack SaaS architecture
- AI-assisted analytics product design
- MongoDB Atlas integration
- dynamic schema intelligence
- production-conscious persistence modeling
- JWT auth and session tracking
- analytics-to-dashboard workflow automation

It is suitable as:

- a portfolio centerpiece
- an investor demo foundation
- an internal analytics accelerator
- a startup MVP base

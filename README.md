# InsightIQ

**AI-Powered Universal Business Intelligence Platform**

[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Vite](https://img.shields.io/badge/Build-Vite-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

InsightIQ is a full-stack analytics SaaS platform that turns uploaded business data into adaptive dashboards, AI-assisted insights, time-series forecasts, and persistent workspace intelligence. It is designed for teams that want fast answers from messy CSVs, spreadsheets, JSON exports, operational reports, and connector-fed data without building a custom BI pipeline first.

## 🚀 Project Overview

InsightIQ combines universal dataset ingestion, schema inference, analytics generation, AI-style Q&A, and Atlas-backed persistence into one workflow:

- Upload almost any structured business dataset.
- Infer schema, business meaning, and semantic column mappings automatically.
- Generate dashboards, KPIs, charts, recommendations, and forecasts.
- Persist user sessions, settings, chat history, reports, connectors, analytics snapshots, and activity logs in MongoDB Atlas.
- Serve everything through a responsive React frontend and a Flask API backend.

The platform is built to feel like a startup-ready internal intelligence layer rather than a static reporting app.

## ✨ Features

- Universal dataset upload for `CSV`, `XLSX`, `XLS`, `JSON`, `TSV`, and `Parquet`
- AI chat with uploaded datasets
- Dynamic dashboards generated from inferred schema
- Auto column mapping for dates, revenue, categories, inventory, products, and operational signals
- Forecasting engine for time-series business data
- AI insights and recommendations
- Real-time analytics refresh after upload
- Persistent saved dashboards and workspace state
- JWT authentication with profile persistence
- Upload history and analytics caching
- Notifications, settings, connectors, reports, exports, and activity logs
- Responsive UI for desktop and laptop workflows

## 🤖 AI Features

InsightIQ includes multiple AI-adjacent intelligence layers:

- AI-style chat responses grounded in the latest uploaded analytics snapshot
- Executive summaries generated from computed profile and trend data
- Recommendation templates with optional external model extension
- Forecast narratives that explain confidence, anomalies, and signal quality
- Dataset semantic inference for business-aware question answering
- Offline-friendly architecture with rule-based fallbacks when external model APIs are unavailable

Current implementation includes Anthropic integration hooks and is structured for OpenAI, Anthropic, and LangChain-style orchestration.

## 🧠 Universal Dataset Intelligence

The ingestion pipeline is designed to work without a fixed schema:

- Detects file type automatically
- Normalizes column names
- Profiles nulls, duplicates, outliers, and cardinality
- Infers datetime, numeric, categorical, currency, and percentage fields
- Maps columns to business concepts like revenue, quantity, product, region, category, customer, and date
- Generates downstream analytics payloads tailored to the uploaded data

This makes InsightIQ suitable for sales, finance, operations, inventory, retail, and reporting use cases.

## 📊 Dynamic Dashboard System

Dashboards are generated from persisted analytics output rather than hardcoded report templates.

- KPI cards are selected from detected business signals
- Charts are chosen dynamically by data shape
- Profile blocks summarize quality and schema context
- Dashboard layout metadata is stored in MongoDB settings
- Saved dashboard snapshots are available per uploaded dataset

## 💬 AI Chat With Data

Users can ask natural-language questions such as:

- “Why did revenue drop?”
- “Which segment performed best?”
- “What does the forecast suggest next month?”
- “Are there anomalies in the uploaded dataset?”

Each chat exchange is persisted in `chat_history`, linked back to the relevant analytics context, and available for future workspace memory features.

## 📈 Forecasting Engine

InsightIQ includes a forecasting pipeline for historical time-series data:

- Detects whether sufficient date-based history exists
- Builds historical trend series from uploaded data
- Runs statistical forecasting models
- Produces forecast rows, confidence summaries, explanations, and anomaly-aware signals
- Persists forecast results in MongoDB for dashboard and API reuse

## 📤 Export System

The platform includes an export-oriented persistence layer for:

- analytics snapshots
- generated reports
- dataset-linked outputs
- future PDF/Excel exports

Collections and service structure are already in place to support downloadable reporting workflows.

## ⚡ Real-Time Analytics

Analytics refresh after every successful upload:

- upload record is stored
- dataset snapshot is stored
- analytics payload is computed
- dashboard snapshot is persisted
- forecast snapshot is persisted
- insights and report metadata are generated
- notification and activity records are created

This gives the app real-time behavior from the user’s perspective while keeping a durable backend history.

## 🔌 Data Connectors

InsightIQ includes a connector persistence layer for future integrations such as:

- Shopify
- Stripe
- HubSpot
- QuickBooks
- Google Sheets
- Internal warehouse exports

Connector metadata is stored in MongoDB and exposed through workspace APIs so the platform can grow toward recurring sync-based analytics.

## 🛠 Tech Stack

### Frontend

- React
- Vite
- Tailwind CSS
- Framer Motion
- Recharts
- Axios
- React Router

### Backend

- Flask
- Flask-JWT-Extended
- PyMongo
- Pandas
- NumPy
- Scikit-learn
- Statsmodels
- bcrypt

### Database

- MongoDB Atlas

### AI

- Anthropic integration hooks
- OpenAI-ready architecture
- LangChain-friendly service boundaries
- Rule-based AI fallbacks for offline mode

## 🧱 Frontend Architecture

The frontend is organized around route-level pages, API wrappers, and shared UI components:

- `src/pages/` contains route screens like dashboard, upload, forecast, inventory, settings, login, and register
- `src/api/` contains Axios clients for auth, uploads, analytics, forecast, recommendations, and inventory
- `src/components/` contains layout primitives, charts, notifications, and reusable UI pieces
- `src/context/` manages auth and app-level state

The frontend never connects directly to MongoDB. It communicates only through backend APIs.

## 🧩 Backend Architecture

The backend uses a modular Flask architecture:

- `app.py` creates the Flask application and registers blueprints
- `routes/` exposes HTTP endpoints
- `services/` contains analytics, forecasting, insight, persistence, and file-processing logic
- `database/mongo.py` centralizes Atlas connection management
- `ai_models/` stores model-specific recommendation and inventory logic
- `config.py` validates operational configuration

## 🗄 Database Architecture

MongoDB Atlas is the single source of truth for persistent application data.

### Core collections

- `users`
- `datasets`
- `uploads`
- `dashboards`
- `analytics`
- `forecasts`
- `insights`
- `reports`
- `connectors`
- `chat_history`
- `notifications`
- `settings`
- `activity_logs`
- `exports`
- `user_sessions`

### Persistence strategy

- Authentication records live in `users`
- File metadata lives in `uploads`
- Normalized dataset metadata lives in `datasets`
- Full analytics payloads live in `analytics`
- Dashboard-ready snapshots live in `dashboards`
- Forecast artifacts live in `forecasts`
- Q&A history lives in `chat_history`
- User workspace state lives in `settings`

## 🗂 Folder Structure

```text
insightiq-fullstack/
├── backend/
│   ├── ai_models/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── mongo.py
│   ├── routes/
│   ├── services/
│   ├── tests/
│   ├── uploads/
│   ├── .env.example
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js
├── data/
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── FEATURES_DOCUMENTATION.md
└── README.md
```

## 📦 Installation Guide

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- MongoDB Atlas account or a local MongoDB instance

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

If you prefer a virtual environment:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 🔐 Environment Variables

Create `backend/.env`:

```env
SECRET_KEY=replace-with-a-strong-secret
JWT_SECRET_KEY=replace-with-a-strong-jwt-secret
MONGO_URI=mongodb+srv://Insightadmin:adminxxxx@cluster0.gmzziw6.mongodb.net/?appName=Cluster0
DATABASE_NAME=InsightIQ
MONGO_CONNECT_RETRIES=3
MONGO_SERVER_SELECTION_TIMEOUT_MS=15000
MONGO_CONNECT_TIMEOUT_MS=15000
MONGO_SOCKET_TIMEOUT_MS=30000
MONGO_MAX_POOL_SIZE=30
MONGO_MIN_POOL_SIZE=1
ALLOW_DB_FALLBACK=False
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OFFLINE_MODE=False
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

For the frontend, set only API-facing variables:

```env
VITE_API_URL=http://localhost:5000/api
```

Never expose MongoDB credentials publicly in production.

## ☁️ MongoDB Atlas Setup

1. Create or access your Atlas cluster.
2. Add an IP access rule for your development machine or deployment environment.
3. Create a database user with least-privilege permissions.
4. Add the connection string to `backend/.env`:

```env
MONGO_URI=mongodb+srv://Insightadmin:admin12345@cluster0.gmzziw6.mongodb.net/?appName=Cluster0
DATABASE_NAME=InsightIQ
```

5. Start the backend and confirm the health route:

```bash
curl http://127.0.0.1:5000/api/health
```

Important:
Never expose credentials publicly in production. Move credentials to a secrets manager or deployment environment variables for real-world deployments.

## ▶️ Running Locally

### Backend

```bash
cd backend
./venv/bin/python app.py
```

If port `5000` is busy:

```bash
cd backend
PORT=5001 ./venv/bin/python app.py
```

### Frontend

```bash
cd frontend
npm run dev
```

If backend is running on `5001`:

```bash
cd frontend
BACKEND_URL=http://localhost:5001 npm run dev
```

### Local URLs

- Frontend: `http://localhost:5173`
- Backend: `http://127.0.0.1:5000`
- Health: `http://127.0.0.1:5000/api/health`

## 🐳 Docker Setup

Run the full stack with Docker Compose:

```bash
docker-compose up --build
```

Current containers:

- frontend served through Nginx on `http://localhost:3000`
- backend served on `http://localhost:5000`
- MongoDB container on `localhost:27017`

For a pure Atlas-based deployment, update Docker environment variables so the backend points to Atlas instead of the local Mongo container.

## 📚 API Documentation

### Auth

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

### Forecasting

- `GET /api/forecast/sales`

### Recommendations & Inventory

- `GET /api/recommendations`
- `GET /api/inventory/status`

### Workspace

- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/reports`
- `GET /api/connectors`
- `POST /api/connectors`
- `GET /api/notifications`
- `POST /api/notifications/<notification_id>/read`

## 🚢 Deployment Instructions

### Frontend

- Deploy to Vercel, Netlify, or an Nginx-backed container
- Set `VITE_API_URL` to your backend base URL

### Backend

- Deploy to Render, Railway, Fly.io, ECS, or Kubernetes
- Install dependencies from `backend/requirements.txt`
- Run with Gunicorn using the provided Dockerfile strategy
- Set all secrets through environment variables

### Production recommendations

- Rotate database credentials
- Store secrets in a managed secret store
- Disable Flask debug mode
- Put the API behind HTTPS
- Restrict Atlas network access
- Enable observability and structured logs

## 🖼 Screenshots

Add product screenshots or GIFs here:

- dashboard overview
- upload workflow
- AI chat panel
- forecasting page
- inventory intelligence page
- settings workspace

Example:

```md
![Dashboard](docs/screenshots/dashboard.png)
![Forecasting](docs/screenshots/forecast.png)
```

## 🔭 Future Improvements

- Scheduled connector sync jobs
- Streaming warehouse connectors
- Team workspaces and RBAC
- PDF and Excel binary export generation
- Natural language dashboard builder
- Alerting workflows and anomaly subscriptions
- LLM orchestration with LangChain agents
- Fine-grained audit trails and retention policies

## 🤝 Contributing Guide

1. Fork the repository
2. Create a feature branch
3. Keep secrets out of commits
4. Add tests for backend behavior changes
5. Run frontend build and backend tests before opening a PR
6. Submit a clear pull request with context and screenshots where useful

Recommended local validation:

```bash
cd backend
./venv/bin/python -m unittest discover -s tests

cd ../frontend
npm run build
```

## 📄 License

MIT License.

For a deeper product and technical walkthrough, see [FEATURES_DOCUMENTATION.md](FEATURES_DOCUMENTATION.md).
# insight-IQ

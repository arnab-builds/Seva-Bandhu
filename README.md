<div align="center">

# 🔧 Seva Bandhu

### Real-Time Smart Dispatch, On-Demand Local Services & Technician Orchestration Platform

<p>
  Connect home & commercial service complaints with certified local specialists in real time.
</p>

![Python](https://img.shields.io/badge/Python%203.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django%205.2-092E20?logo=django&logoColor=white)
![Django Channels](https://img.shields.io/badge/Django%20Channels%204.3-44B78B?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Supabase%20PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet%20%26%20OSRM-199900?logo=leaflet&logoColor=white)
![AI Powered](https://img.shields.io/badge/AI%20Chatbot-Groq%20%2B%20Gemini-8A2BE2?logo=sparkles&logoColor=white)
![Brevo](https://img.shields.io/badge/Transactional%20Email-Brevo%20API-0B99FF?logo=sendinblue&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cron%20Worker-Cloudflare-F38020?logo=cloudflare&logoColor=white)

**Match the right technician to every job, instantly.** ⚡

Seva Bandhu bridges local service requests with certified trade specialists through automated skill-based dispatching, live GPS turn-by-turn navigation, real-time WebSocket communication, dual-ledger digital wallets, machine-learning recommendations, and an automated administration portal.

### 🌐 [Explore Seva Bandhu Live](https://seva-bandhu-41dh.onrender.com) — Active Production Deployment

<br>

<img src="docs/Screenshot.png" alt="Seva Bandhu Platform" width="900"/>

</div>

---

## 📑 Table of Contents

- [🌐 Live Deployment](#-live-deployment)
- [✨ Key Capabilities](#-key-capabilities)
- [👥 User Roles & Workflows](#-user-roles--workflows)
  - [👤 Customer Portal](#-customer-portal)
  - [🛠️ Technician Portal](#️-technician-portal)
  - [👑 Super Admin Portal](#-super-admin-portal)
  - [🌐 Public & Authentication Workflows](#-public--authentication-workflows)
- [🧠 Machine Learning & AI Intelligence](#-machine-learning--ai-intelligence)
- [🗺️ Live GPS Tracking & Road Guidance](#️-live-gps-tracking--road-guidance)
- [💳 Financial Systems, Wallets & Incentives](#-financial-systems-wallets--incentives)
- [⚡ Real-Time Systems & WebSockets](#-real-time-systems--websockets)
- [🛠️ Tech Stack](#️-tech-stack)
- [🏗️ System Architecture](#️-system-architecture)
- [🗄️ Data Model & Schema Overview](#️-data-model--schema-overview)
- [🚀 Local Development Setup](#-local-development-setup)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Database & Static Files](#2-database--static-files)
  - [3. Running the Server](#3-running-the-server)
- [🔐 Environment Variables](#-environment-variables)
- [☁️ Production Infrastructure & Health Monitoring](#️-production-infrastructure--health-monitoring)
- [🧪 Testing & Verification](#-testing--verification)
- [👤 Author](#-author)

---

## 🌐 Live Deployment

| Service | Endpoint / Link | Description |
|---|---|---|
| **Live Web Application** | [seva-bandhu-41dh.onrender.com](https://seva-bandhu-41dh.onrender.com) | Production ASGI web deployment hosted on Render |
| **System Health Check** | [/health/](https://seva-bandhu-41dh.onrender.com/health/) | Lightweight HTTP status check (`status: 200 OK`) |
| **Database Health Check** | [/health/db/](https://seva-bandhu-41dh.onrender.com/health/db/) | Live database connectivity probe (`SELECT 1` on Supabase) |
| **Super Admin Portal** | [/super-admin/](https://seva-bandhu-41dh.onrender.com/super-admin/) | Executive management and business analytics suite |
| **Cloudflare Health Monitor** | `sevabandhu-health-monitor` | Cloudflare Cron worker pinging `/health/db/` every 10 min |

> **🚀 Infrastructure:** The core application runs on **Render** (Python 3.12 Daphne ASGI container), persistence is backed by **Supabase PostgreSQL**, media is served through **Cloudinary**, transactional emails run via **Brevo HTTPS REST API**, and uptime is monitored via a **Cloudflare Worker Cron trigger**.

---

## ✨ Key Capabilities

- ⚡ **Real-Time Smart Dispatch Engine** — Broadcasts incoming service bookings immediately across WebSockets to matching available technicians; prevents assignment collision via atomic database locks.
- 🛡️ **Self-Booking & Conflict Prevention** — Guarantees that a user holding dual Customer and Technician roles cannot book or assign themselves, while preventing schedule clashes across date and time slots.
- 🗺️ **Turn-by-Turn Road Guidance & Live Map** — Technician navigation with Leaflet, OpenStreetMap, OSRM routing, GPS jitter filtering, arrival proximity detection, and browser SpeechSynthesis voice guidance.
- 💬 **In-Journey WebSocket Chat** — Dedicated real-time communication channel established between customer and technician once the journey starts, automatically locked upon job completion.
- 💰 **Dual-Role Financial Wallets** — Customer wallet supporting online top-ups and one-click booking payments; technician earnings wallet with atomic job credits and milestone incentives.
- 🏆 **Technician Incentive Missions** — Configurable target missions (e.g., daily completed job quotas, 5-star rating milestones) with automated wallet rewards and administrative audit trails.
- 🤖 **Context-Aware AI Assistant** — Customer support chatbot with Groq primary acceleration and Google Gemini fallback, injecting live user context and active booking statuses.
- 🎯 **KNN Collaborative Filtering Recommender** — Custom machine-learning model trained with scikit-learn cosine similarity on customer interaction matrices to surface personalized service suggestions.
- 📈 **Bayesian Smoothed Service Ratings** — Mathematical ranking algorithm balancing completed bookings against validated complaints to compute fair service ratings.
- 🧾 **Automated PDF Invoices & Email Delivery** — Generates downloadable PDF receipts via ReportLab / xhtml2pdf and delivers them immediately via Brevo transactional emails.
- 📊 **Executive Analytics & Natural Language Querying** — Super Admin dashboard with financial accounting, cohort metrics, campaign analytics, and an integrated database query assistant.

---

## 👥 User Roles & Workflows

Seva Bandhu implements strict role separation with independent dashboards, permissions, and session handling.

### 👤 Customer Portal

Designed for seamless service discovery, flexible booking, transparent pricing, and live service coordination.

```
Service Discovery → Booking Creation → Real-Time Dispatch → Live GPS Tracking → In-Service Chat → Dual-Method Payment → Invoice & Rating
```

- **Identity & Authentication:**
  - Secure registration and email verification code flow (prevents phantom account creation).
  - Supabase OAuth integration supporting Google Sign-In with automated Indian mobile number validation (`/auth/complete-profile/`).
  - Account profile management with persistent addresses and referral code generation.
- **Service Discovery & Smart Booking:**
  - Dynamic service catalog with pricing and availability status.
  - Collaborative filtering recommendations (`get_recommendations`) powered by user booking history.
  - OpenStreetMap Nominatim geocoding fallback for manual address inputs.
  - Smart offer popups triggered by user browsing frequency and cooldown timers.
  - Coupon redemption engine with flat and percentage discount validations.
  - Self-booking guard: Prevents booking if the customer is the sole technician in that trade category.
- **Tracking & Communication:**
  - Real-time map displaying technician's live location, distance in meters, and arrival ETA.
  - WebSocket chat enabled during active journeys with server-side authorization.
- **Billing & Reviews:**
  - Payment checkout supporting Seva Bandhu Wallet balance deduction or simulated online checkout.
  - Instant PDF invoice generation and automated email delivery.
  - 5-star rating and review submission with Bayesian rating updates.
  - Support ticket and complaint filing with direct linking to specific bookings and technicians.

---

### 🛠️ Technician Portal

Built for field trade specialists to review dispatch broadcasts, manage active jobs, navigate routes, and track professional earnings.

```
Job Broadcast Alert → 1-Click Accept (Conflict-Checked) → Start Journey → Live GPS Guidance → Complete Service → Instant Wallet Credit
```

- **Professional Onboarding:**
  - Role-specific signup, credential authentication, and profile completion (trade category, experience years, service areas).
  - Online/offline availability status toggle.
- **Dispatch Queue & Job Lifecycle:**
  - Real-time WebSocket connection to `/ws/requests/` receiving broadcasted service cards.
  - Atomic acceptance (`accept_request`) with `select_for_update` row locking to prevent race conditions.
  - Validation against customer identity to prevent self-assignment.
  - Automated notification cleanup across all other connected technicians upon claim.
  - Status progression: `Pending` → `Assigned` → `In Progress` → `Completed`.
- **Navigation & Road Guidance:**
  - Full-screen Leaflet interactive map with OSRM optimal driving routes.
  - Geolocation tracking with GPS accuracy thresholds and stationary jitter suppression.
  - Browser Web Speech API (`SpeechSynthesisUtterance`) providing hands-free voice directions.
  - Automated arrival detection when within 100 meters of customer coordinates.
- **Wallet, Earnings & Missions:**
  - Dedicated technician wallet receiving 100% of job earnings upon completion.
  - Automated qualification engine for Daily Job Quotas and Five-Star Milestones.
  - Formal withdrawal request pipeline with reserved funds, administrative review, and rejection reversals.
- **Guided Support System:**
  - Interactive decision-tree chatbot (`SUPPORT_TREE`) for troubleshooting common field issues.
  - One-click ticket escalation to Super Admin with live WebSocket support chat (`/ws/support/technician/<ticket_id>/`).

---

### 👑 Super Admin Portal

A custom executive management suite accessible only to authenticated superusers at `/super-admin/`.

```
Executive Dashboard → Real-Time Analytics → Platform Oversight → Financial Settlements → AI Data Assistant
```

- **Executive Analytics & Accounting:**
  - Comprehensive Analytics (`/super-admin/analytics/comprehensive/`): Authoritative sales (paid bookings), technician payouts, net platform income, discounts absorbed, referral bonuses, and pending withdrawal obligations.
  - Date range filters: `Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `This Month`, `Last Month`, `This Year`, `All Time`.
  - Platform Analytics (`/super-admin/analytics/platform/`): ML recommendation performance (CTR, conversion rate, impressions), promotional campaign redemption rates, and Bayesian service quality metrics.
- **Platform Management:**
  - Customer & Technician Lifecycle: Profile inspection, service history, activity metrics, and 1-click account activation/deactivation.
  - Service Catalog Management: Create, edit, toggle availability, or safely disable services referenced in historical requests.
  - Service Request Oversight: Global log of all requests with status filters, address details, and manual technician assignments (excluding the customer's own technician profile).
- **Financial & Incentive Governance:**
  - Withdrawal Approval Pipeline: Review pending technician withdrawals, approve transfers, or reject requests with automatic fund reversal and ledger credit.
  - Incentive Mission Creator: Define new daily or milestone missions with thresholds, cash bonuses, and validity dates.
- **Support, Discipline & AI Assistant:**
  - Customer Support Ticket Resolution: Process complaints, issue discretionary wallet credits directly to customer accounts, and dispatch resolution emails.
  - Automated Warning Engine: Issue official disciplinary warnings with automatic 1-point penalties to technician public ratings.
  - Live Technician Support Console: Dual-pane WebSocket chat interface for resolving escalated field tickets.
  - **Admin Data Assistant:** Integrated natural-language query engine (`AdminDataAssistant`) allowing superadmins to query revenue, technician performance, and booking statistics in plain English.

---

### 🌐 Public & Authentication Workflows

- **Landing Experience (`home.html`):** Modern hero showcase with portal shortcuts, verified technician statistics, category highlights, and quick booking triggers.
- **Dual Authentication System:** Standard Django session authentication paired with Supabase OAuth for one-tap Google logins.
- **Centralized Identity Layer (`core.identity`):** Unifies display names across both profiles, prioritizing official user names over raw usernames, and centralizing email notifications through the core Django user.

---

## 🧠 Machine Learning & AI Intelligence

Seva Bandhu integrates predictive modeling and generative AI into production workflows:

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│     Scikit-Learn Recommender    │      │        Dual-Provider AI         │
│  - Interaction Matrix (joblib)  │      │  - Groq (openai/gpt-oss-20b)    │
│  - KNN Cosine Distance Model    │      │  - Gemini (gemini-3.6-flash)    │
│  - Dynamic Fallback Padding     │      │  - Customer Context Injection   │
└─────────────────────────────────┘      └─────────────────────────────────┘
```

1. **KNN Collaborative Filtering Recommender (`core.ml.recommender`):**
   - Implements a K-Nearest Neighbors model trained on user-service interaction matrices.
   - Evaluates cosine distance between customer usage vectors to suggest relevant services.
   - Falls back gracefully to popularity and category recency when historical data is sparse.
   - Cached in memory using thread-safe lazy loading (`threading.Lock`) for instant response times.
2. **Context-Aware AI Chatbot (`core.ai.chatbot`):**
   - **Primary Engine:** Groq API (`openai/gpt-oss-20b`) for sub-second conversational latency.
   - **Fallback Engine:** Google Gemini (`gemini-3.6-flash`) automatically activated if Groq limits are reached.
   - Dynamic prompt synthesis incorporating customer profile information, current wallet balance, and recent service request details.
3. **Bayesian Smoothed Service Ratings (`core.services.rating_engine`):**
   - Prevents small-sample distortion on service ratings using Bayesian prior smoothing:
     $$\text{Smoothed Rate} = \frac{\text{Complaints} + (\text{Prior Confidence} \times \text{Prior Rate})}{\text{Completed Bookings} + \text{Prior Confidence}}$$
   - Clamps ratings between 1.0 and 5.0 to produce statistically sound quality metrics.

---

## 🗺️ Live GPS Tracking & Road Guidance

The tracking system connects field specialists and customers through low-latency telemetry:

| Feature | Implementation | Details |
|---|---|---|
| **Map Rendering** | Leaflet + OpenStreetMap | Interactive tile rendering with customized SVG location markers. |
| **Route Calculation** | Leaflet Routing Machine + OSRM | Calculates optimal driving route, turn instructions, total meters, and ETA. |
| **GPS Acquisition** | `navigator.geolocation.watchPosition` | High-accuracy device GPS tracking with timeout and fallback handling. |
| **Noise Filtering** | Jitter & Accuracy Filter | Rejects readings with accuracy > 200m or stationary movements < 25m. |
| **Voice Navigation** | Web Speech API (`SpeechSynthesis`) | Announces turn-by-turn guidance prompts aloud in real time. |
| **Arrival Detection** | Haversine Proximity Check | Automatically marks arrival when distance to customer drops below 100m. |
| **Telemetry Relay** | WebSocket (`RequestConsumer`) | Persists latitude, longitude, ETA, and distance directly to PostgreSQL. |

---

## 💳 Financial Systems, Wallets & Incentives

Seva Bandhu manages two separate digital ledger systems:

```
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│           Customer Wallet            │     │          Technician Wallet           │
├──────────────────────────────────────┤     ├──────────────────────────────────────┤
│ • Balance top-ups (Simulated / Card) │     │ • 100% Job earnings on completion    │
│ • 1-Click booking checkout           │     │ • Daily job milestone incentives     │
│ • Administrative refund credits      │     │ • 5-Star rating milestone bonuses    │
│ • Referral bonuses (ReferralLog)     │     │ • Regulated withdrawal pipeline      │
└──────────────────────────────────────┘     └──────────────────────────────────────┘
```

- **Atomic Transactions:** All wallet mutations use `@transaction.atomic` and `select_for_update` row locking to prevent double-spending or race conditions.
- **Incentive Engine:** Automatically scans completed jobs and 5-star ratings against active administrative missions to issue bonus credits.
- **Settlement & Audit:** Every balance modification creates a permanent `WalletTransaction` or `TechnicianWalletTransaction` record with reference IDs.

---

## ⚡ Real-Time Systems & WebSockets

The real-time layer is built on **Django Channels** and served through **Daphne ASGI**:

```
Client Browser ──(WSS)──> Daphne ASGI Router ──> ProtocolTypeRouter ──> Channel Layer
                                                                            │
      ┌─────────────────────┬───────────────────────┬───────────────────────┤
      ▼                     ▼                       ▼                       ▼
ws/requests/       ws/tracking/<id>/         ws/chat/<id>/       ws/support/technician/<id>/
(Technician Queue)  (Live GPS Stream)        (In-Service Chat)     (Admin Support Chat)
```

- **`/ws/requests/` (`RequestConsumer`):** Group `technicians` — Broadcasts new job bookings and removes claimed requests in real time.
- **`/ws/tracking/<id>/` (`RequestConsumer`):** Group `tracking_<id>` — Authenticates customer and technician participants, streams GPS coordinates, route distances, and ETAs.
- **`/ws/chat/<id>/` (`ChatConsumer`):** Group `chat_<id>` — Enables bidirectional chat during active journeys; automatically locks when the service status is marked `Completed`.
- **`/ws/support/technician/<id>/` (`TechnicianSupportConsumer`):** Group `tech_support_<id>` — Dedicated support room connecting technicians with administrators.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.12, Django 5.2.7, Django Channels 4.3.2, Daphne 4.2.1, Asgiref |
| **Frontend Templates** | Django Templates, HTML5, CSS3, Vanilla JavaScript, FontAwesome, Google Fonts |
| **Real-Time & Networking** | WebSockets, InMemoryChannelLayer, Twisted, Autobahn |
| **Database & ORM** | PostgreSQL (Supabase), dj-database-url, psycopg2-binary, SQLite (Development) |
| **Mapping & Navigation** | Leaflet, Leaflet Routing Machine, OpenStreetMap Tiles, Nominatim API, Web Speech API |
| **AI & Machine Learning** | Google Gemini (`google-generativeai`), Groq SDK (`groq`), Scikit-learn, Pandas, NumPy, Joblib |
| **Document Generation** | ReportLab 4.0, xhtml2pdf 0.2.8 |
| **Transactional Email** | Brevo Python SDK (`brevo-python`), HTTPS REST API Port 443 |
| **Media & Static Storage** | Cloudinary, django-cloudinary-storage, WhiteNoise |
| **Deployment & Ops** | Render (Web Service), Cloudflare Worker (Cron Monitor), Supabase (PostgreSQL) |

---

## 🏗️ System Architecture

### Component Hierarchy

```
                                  ┌───────────────────────────────┐
                                  │      Cloudflare Worker        │
                                  │   (Cron Ping every 10 min)    │
                                  └───────────────┬───────────────┘
                                                  │ HTTP GET /health/db/
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Render ASGI Container                                 │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                              Daphne ASGI                                │   │
│   └────────────────────┬────────────────────────────────┬───────────────────┘   │
│                        │ HTTP Requests                  │ WebSockets            │
│                        ▼                                ▼                       │
│   ┌─────────────────────────────────────────┐  ┌────────────────────────────┐   │
│   │           Django 5.2 Application        │  │      Django Channels       │   │
│   │                                         │  │  (Tracking / Chat / Queue) │   │
│   │  • Views & Admin Views                  │  └─────────────┬──────────────┘   │
│   │  • Offer, Incentive & Rating Engines    │                │                  │
│   │  • Admin Assistant NL Query Engine      │                │                  │
│   │  • ML Recommender & AI Chatbot          │                │                  │
│   └────────────────────┬────────────────────┘                │                  │
│                        │                                     │                  │
└────────────────────────┼─────────────────────────────────────┼──────────────────┘
                         │                                     │
                         ▼                                     ▼
      ┌─────────────────────────────────────┐   ┌─────────────────────────────┐
      │         Supabase PostgreSQL         │   │      External Services      │
      │  (Relational Database + Auth OAuth) │   │ • Brevo (Transactional Mail)│
      └─────────────────────────────────────┘   │ • Cloudinary (Media CDN)    │
                                                │ • Groq / Gemini (AI Chat)   │
                                                │ • OSM Nominatim (Geocoding) │
                                                └─────────────────────────────┘
```

---

## 🗄️ Data Model & Schema Overview

Seva Bandhu manages 25 database models handling relationships across users, bookings, finances, and communications:

```mermaid
erDiagram
    User ||--o| customer_signup : "has profile"
    User ||--o| Technician_signup : "has profile"
    customer_signup ||--o{ ServiceRequest : "books"
    Technician_signup ||--o{ ServiceRequest : "assigned to"
    ServiceRequest ||--|| ServiceDetail : "describes"
    ServiceRequest ||--|| ServiceAddress : "located at"
    ServiceRequest ||--o| Offer : "applies promo"
    ServiceRequest ||--o| ChatConversation : "has chat"
    ChatConversation ||--o{ ChatMessage : "contains"
    ServiceRequest ||--o| TechnicianRating : "receives review"
    customer_signup ||--o{ WalletTransaction : "ledger entries"
    Technician_signup ||--|| TechnicianWallet : "owns wallet"
    TechnicianWallet ||--o{ TechnicianWalletTransaction : "ledger entries"
    Technician_signup ||--o{ WithdrawalRequest : "requests"
    Incentive ||--o{ TechnicianIncentiveAward : "qualifies"
    Technician_signup ||--o{ TechnicianIncentiveAward : "awarded to"
    customer_signup ||--o{ SupportTicket : "files"
    SupportTicket ||--o| TechnicianWarning : "penalizes"
    Technician_signup ||--o{ TechnicianSupportTicket : "escalates"
    TechnicianSupportTicket ||--o{ TechnicianSupportMessage : "messages"
```

---

## 🚀 Local Development Setup

### Prerequisites

Ensure the following tools are installed locally:
- **Python 3.12+**
- **Git**
- **PowerShell** (Windows) or **Bash** (macOS/Linux)
- **Node.js 20+** (Optional, for Cloudflare worker tests)

---

### 1. Backend Setup

Clone the repository and navigate to the project root:

```bash
git clone https://github.com/arnab-builds/Seva-Bandhu.git
cd Seva-Bandhu
```

Create and activate a virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

---

### 2. Database & Static Files

Configure your local environment by creating a `.env` file in the project root (see [Environment Variables](#-environment-variables)):

```powershell
Copy-Item .env.example .env
```

Apply database migrations:

```bash
python backend/manage.py migrate
```

Create a Super Admin user:

```bash
python backend/manage.py createsuperuser
```

---

### 3. Running the Server

Start the development server using Daphne (recommended for WebSockets):

```bash
daphne -b 127.0.0.1 -p 8001 seva_bandhu.asgi:application
```

*(Alternatively, use `python backend/manage.py runserver 8001` for standard HTTP development).*

| Interface | Local URL | Description |
|---|---|---|
| **Public Landing Page** | `http://127.0.0.1:8001/home/` | Customer & Technician portal entry |
| **Customer Portal** | `http://127.0.0.1:8001/customer/dashboard/` | Booking management & live tracking |
| **Technician Portal** | `http://127.0.0.1:8001/technician/dashboard_t/` | Dispatch queue & navigation |
| **Super Admin Portal** | `http://127.0.0.1:8001/super-admin/` | Custom operations & analytics dashboard |
| **Django Admin** | `http://127.0.0.1:8001/admin/` | Standard Django model administration |
| **Health Probe** | `http://127.0.0.1:8001/health/db/` | Database health endpoint |

---

## 🔐 Environment Variables

Create a `.env` file in the repository root. All production secrets and keys are read safely via `python-dotenv`:

```env
# ==========================================
# DJANGO CORE CONFIGURATION
# ==========================================
DJANGO_SECRET_KEY=your-secure-random-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,seva-bandhu-41dh.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://seva-bandhu-41dh.onrender.com
PUBLIC_BASE_URL=http://127.0.0.1:8001

# ==========================================
# DATABASE CONFIGURATION
# ==========================================
# Leave blank to use local SQLite (backend/db.sqlite3)
DATABASE_URL=postgres://user:password@host:5432/dbname

# ==========================================
# MEDIA STORAGE (CLOUDINARY)
# ==========================================
# Required in production for persistent technician & service photos
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# ==========================================
# TRANSACTIONAL EMAIL (BREVO API)
# ==========================================
BREVO_API_KEY=xkeysib-your-brevo-api-key
BREVO_FROM_EMAIL=your-verified-sender@example.com
BREVO_FROM_NAME=Seva Bandhu Support
DEFAULT_FROM_EMAIL=your-verified-sender@example.com

# ==========================================
# AUTHENTICATION & SUPABASE
# ==========================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...

# ==========================================
# AI & MACHINE LEARNING PROVIDERS
# ==========================================
# Primary high-speed chat provider
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

# Secondary backup chat provider
AI_API_KEY=your-gemini-api-key
AI_MODEL_NAME=gemini-3.6-flash
```

> ⚠️ **Security Notice:** Never commit actual `.env` files, production database URLs, or API keys to version control. The repository's `.gitignore` explicitly excludes all `.env` files.

---

## ☁️ Production Infrastructure & Health Monitoring

### Render ASGI Deployment
- **Runtime:** Python 3.12 (`runtime.txt: python-3.12.10`)
- **Build Command:** `pip install -r backend/requirements.txt && python backend/manage.py collectstatic --noinput && python backend/manage.py migrate`
- **Start Command:** `daphne -b 0.0.0.0 -p $PORT seva_bandhu.asgi:application`
- **Security:** Strict SSL headers, `WhiteNoise` static compression, and Cloudinary media persistence.

### Cloudflare Cron Health Monitor (`cloudflare/`)
Because Render free instances can sleep after periods of inactivity, a standalone Cloudflare Worker periodically exercises the database connection:
- **Worker Name:** `sevabandhu-health-monitor`
- **Schedule:** `*/10 * * * *` (Runs every 10 minutes via Cloudflare Cron Triggers)
- **Target Endpoint:** `https://seva-bandhu-41dh.onrender.com/health/db/`
- **Behavior:** Issues an awaited HTTP GET request with `User-Agent: SevaBandhu-HealthMonitor/1.0`. Django runs a live `SELECT 1` query and outputs structured runtime logs to Render `stdout`. Throws an error on non-200 responses to ensure failure visibility in Cloudflare metrics.

---

## 🧪 Testing & Verification

Seva Bandhu maintains automated test suites covering all critical business flows:

### Running Django Test Suites

Run the complete core test suite (75 tests):

```bash
python backend/manage.py test core
```

Run targeted functional suites:

```bash
# Test health endpoints & safe logging (10 tests)
python backend/manage.py test core.tests.test_health

# Test account flows, self-booking prevention & recommender (20 tests)
python backend/manage.py test core.tests.test_flows

# Test Brevo transactional email delivery & identity resolution (20 tests)
python backend/manage.py test core.tests.test_brevo_email

# Test Supabase OAuth & profile completion (15 tests)
python backend/manage.py test core.tests.test_supabase_auth

# Test promotional offer engines & cooldown timers (10 tests)
python backend/manage.py test core.tests.test_smart_offers
```

Run Django system configuration checks:

```bash
python backend/manage.py check
```

### Running Cloudflare Worker Tests

From the `cloudflare/` directory:

```bash
cd cloudflare
node test/test_monitor.js
```
*(Executes 7 isolated unit tests validating healthy responses, HTTP error codes, timeout abortions, and Cron trigger error throwing).*

---

## 👤 Author

**Arnab**  
GitHub: [@arnab-builds](https://github.com/arnab-builds)  
Project Repository: [Seva-Bandhu](https://github.com/arnab-builds/Seva-Bandhu)

---

<div align="center">

If you find Seva Bandhu helpful, consider starring the repository ⭐

</div>

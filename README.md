# 🩷 WebPulse — Self-Hostable Website Monitoring Tool

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-pink?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react" alt="React" />
  <img src="https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker" alt="Docker" />
</p>

**WebPulse** is a free, self-hostable website monitoring tool that tracks latency, page speed, uptime, and provides actionable performance improvement suggestions. Built with a modern stack featuring a beautiful Pink/Black/White themed UI with dark and light mode support.

---

## ✨ Features

### 🔍 Core Monitoring
- **Latency Tracking** — Real-time ping/latency measurements to your websites
- **Page Speed Analysis** — Full page load time, TTFB, and page size monitoring
- **Periodic Background Checks** — Automated monitoring via APScheduler (configurable interval)
- **Up to 10 Websites** — Monitor up to 10 websites simultaneously
- **Performance Suggestions** — Intelligent, per-check improvement recommendations

### 🔐 Auth & Security
- **JWT Authentication** — Secure token-based login
- **2FA (TOTP) Enforcement** — Mandatory two-factor authentication for all accounts
- **Multi-Admin Support** — Main Admin + Sub-admins with granular permissions
- **Checkbox Permissions** — Fine-grained access control (view, manage, run checks, etc.)
- **Secure Onboarding** — Default admin credentials generated on first run, forced password change

### 🎨 UI/UX
- **Theme** — Pink, Black, and White accent color scheme
- **Dark/Light Mode** — Toggle between dark and light themes
- **Welcome Back Popup** — Weekly roundup with performance stats and rotating tips
- **Responsive Design** — Mobile-friendly with collapsible sidebar
- **Glass Morphism Cards** — Modern, professional interface

### 🐳 DevOps
- **Docker & Docker Compose** — One-command deployment
- **SQLite Database** — Zero-configuration, file-based persistence
- **Health Checks** — Built-in container health monitoring

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.12) |
| Database | SQLite + SQLAlchemy |
| Auth | JWT (python-jose) + pyotp (TOTP) |
| Scheduler | APScheduler |
| HTTP Client | httpx |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Icons | Lucide React |
| Container | Docker + Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (v2.x+)
- OR Python 3.12+ and Node.js 20+

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/webpulse.git
cd webpulse

# Start all services
docker compose up -d --build

# Access the app
# Frontend: http://localhost
# Backend API: http://localhost:8000
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies API to :8000)
npm run dev
```

---

## 🔑 First-Time Setup

1. **Start WebPulse** using Docker Compose or manual setup
2. **Login** with default credentials:
   - **Username:** `admin`
   - **Password:** `WebPulse@2026!`
3. **Change Password** — You'll be forced to set a new password on first login
4. **Setup 2FA** — Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
5. **Start Monitoring** — Add your first website from the Websites page

> ⚠️ **Important:** Default credentials are temporary and must be changed on first login. The system enforces this flow for security.

---

## 📋 Permissions System

The Main Admin can create Sub-admins with granular, checkbox-based permissions:

| Permission | Description |
|-----------|-------------|
| `view_websites` | View websites and monitoring data |
| `manage_websites` | Add, edit, and delete websites |
| `run_checks` | Trigger manual website checks |
| `view_users` | View list of sub-admins |
| `manage_users" | Create and manage sub-admins |
| `view_settings" | View system settings |
| `manage_settings" | Change system settings |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Auto-generated | JWT signing key (set in production!) |
| `DATABASE_URL" | `sqlite:///./webpulse.db` | Database connection string |
| `CHECK_INTERVAL_SECONDS" | `300` | Interval between automated checks (5 min) |

### Docker Compose `.env` file

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key-change-this
CHECK_INTERVAL_SECONDS=300
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login (returns JWT) |
| POST | `/api/auth/change-password` | Change password |
| GET | `/api/auth/totp/setup` | Get TOTP setup QR code |
| POST | `/api/auth/totp/verify` | Verify and enable TOTP |
| GET | `/api/auth/me` | Get current user info |

### Websites
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/websites/dashboard" | Dashboard statistics |
| GET | `/api/websites/weekly-roundup" | Weekly performance roundup |
| GET | `/api/websites" | List all websites |
| POST | `/api/websites" | Add a website |
| DELETE | `/api/websites/{id}" | Delete a website |
| POST | `/api/websites/{id}/check" | Run manual check |
| GET | `/api/websites/{id}/history" | Get check history |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/permissions" | List available permissions |
| GET | `/api/admin/users" | List all users |
| POST | `/api/admin/users" | Create sub-admin |
| PUT | `/api/admin/users/{id}" | Update user permissions |
| DELETE | `/api/admin/users/{id}" | Delete user |

---

## 🔒 Security Notes

- All passwords are hashed with **bcrypt**
- JWT tokens expire after **60 minutes**
- **TOTP (2FA) is mandatory** for all accounts
- Sub-admins must change their password on first login
- Main Admin cannot be deleted or modified by sub-admins
- CORS is configured for development; restrict in production

---

## 📁 Project Structure

```
webpulse/
├── backend/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py             # Configuration
│   ├── database.py           # SQLAlchemy setup
│   ├── models.py             # Database models
│   ├── schemas.py            # Pydantic schemas
│   ├── auth.py               # Authentication logic
│   ├── monitor.py            # Website monitoring engine
│   ├── routes_auth.py        # Auth API routes
│   ├── routes_websites.py    # Website API routes
│   ├── routes_admin.py       # Admin API routes
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx        # App layout + sidebar
│   │   │   └── WelcomePopup.tsx  # Welcome back modal
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx    # Auth state management
│   │   │   └── ThemeContext.tsx   # Theme management
│   │   ├── pages/
│   │   │   ├── Login.tsx         # Login + onboarding flows
│   │   │   ├── Dashboard.tsx     # Main dashboard
│   │   │   ├── Websites.tsx      # Website management
│   │   │   └── Users.tsx         # User management
│   │   ├── utils/
│   │   │   └── api.ts            # Axios client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 📜 License

MIT License — Free to use, modify, and distribute.

---

<p align="center">
  Built with 🩷 by the WebPulse team
</p>

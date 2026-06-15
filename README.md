# 🏫 Dormitory Management System (DMS) - Backend API


A production-ready RESTful API for managing secondary school dormitories. Built with Django REST Framework, this system handles leave-out requests, maintenance tracking, duty rosters, room inspections, and audit logging with role-based access control.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Authentication](#authentication)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Functionality

| Module | Description | Status |
|----------|----------|----------|
| User Authentication | JWT-based login with role-based access | ✅ |
| Leave-Out Management | Submit, approve, track student leave requests | ✅ |
| Maintenance Requests | Report and track dormitory repairs | ✅ |
| Duty Roster | Schedule boarding officer shifts | ✅ |
| Room Inspections | Record and track inspection results | ✅ |
| Audit Logging | Automatic tracking of all user actions | ✅ |
| Parent Notifications | Email alerts for leave approvals | 🚧 |
| Reports Export | PDF/Excel reports for administrators | 🚧 |

### User Roles

- **Administrator** - Full system access, user management, reports
- **Boarding Officer** - Daily operations, leave submission, inspections
- **Parent/Guardian** - Read-only access to child's dormitory information

## 🛠️ Tech Stack

```yaml
Framework: Django 5.1.6
REST API: Django REST Framework 3.15.1
Authentication: JWT (SimpleJWT 5.3.1)
Database: PostgreSQL + psycopg2-binary 2.9.9
Task Queue: Celery 5.3.6 + Redis 5.0.1
API Documentation: drf-spectacular 0.27.2
CORS: django-cors-headers 4.3.1
Configuration: python-decouple 3.8
```

## 🚀 Quick Start

```bash
git clone https://github.com/yourusername/dms-backend.git
cd dms-backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**The API will be available at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/api/schema/swagger-ui/`

## 📦 Installation

### Prerequisites

| Requirement | Version |
|----------|----------|
| Python | 3.10+ |
| PostgreSQL | 14+ |
| Redis | 6.0+ |

### Configure Environment Variables

```env
SECRET_KEY=your-super-secret-key
DEBUG=True

DB_NAME=dms_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|----------|----------|----------|
| POST | `/api/token/` | Login |
| POST | `/api/token/refresh/` | Refresh Token |
| POST | `/api/token/verify/` | Verify Token |

### Users

| Method | Endpoint |
|----------|----------|
| GET | `/api/users/` |
| POST | `/api/users/` |
| GET | `/api/users/{id}/` |
| PUT | `/api/users/{id}/` |
| DELETE | `/api/users/{id}/` |

### Leave-Out Management

| Method | Endpoint |
|----------|----------|
| GET | `/api/leave-out/` |
| POST | `/api/leave-out/` |
| PUT | `/api/leave-out/{id}/approve/` |

### Maintenance

| Method | Endpoint |
|----------|----------|
| GET | `/api/maintenance/` |
| POST | `/api/maintenance/` |
| PUT | `/api/maintenance/{id}/` |

## 🗄️ Database Schema

```text
User
 ├── LeaveOut
 ├── Inspection
 └── AuditLog

Student
 └── Room

Room
 └── Inspection
```

## 🔐 Authentication

```bash
curl -X POST http://localhost:8000/api/token/ \
-H "Content-Type: application/json" \
-d '{"username":"admin","password":"password"}'
```

## 📁 Project Structure

```text
dms_backend/
├── apps/
│   ├── users/
│   ├── leave_out/
│   ├── maintenance/
│   ├── duty_roster/
│   ├── inspection/
│   └── audit_log/
├── requirements/
├── .env
├── manage.py
└── README.md
```

## 🧪 Testing

```bash
python manage.py test
```

## 🐛 Troubleshooting

| Issue | Solution |
|----------|----------|
| Port already in use | Use another port |
| JWT expired | Refresh token |
| Database not found | Create database |

## 🚢 Deployment

```bash
gunicorn dms_backend.wsgi:application \
--bind 0.0.0.0:8000 \
--workers 4
```

## 🤝 Contributing

1. Fork repository
2. Create branch
3. Commit changes
4. Push changes
5. Open Pull Request

## 📝 License

MIT License

## 👥 Authors

- Your Name

## 📧 Contact

- Email: your.email@example.com
- GitHub: https://github.com/yourusername
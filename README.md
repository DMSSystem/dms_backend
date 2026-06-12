\# Dormitory Management System - Backend API



RESTful API backend for the Dormitory Management System, built with Django REST Framework. Handles user authentication, leave-out management, maintenance requests, duty rosters, room inspections, and audit logging for secondary school dormitories.



\## 🎯 Core Features



\- \*\*JWT Authentication\*\* - Secure token-based authentication

\- \*\*Role-Based Access Control\*\* - Admin, Boarding Officer, Parent roles

\- \*\*Leave-Out Management\*\* - Submit, approve, reject, and track student leaves

\- \*\*Maintenance Requests\*\* - Report and track dormitory repairs

\- \*\*Duty Roster\*\* - Schedule and manage boarding officer assignments

\- \*\*Inspection Tracking\*\* - Record room inspection results

\- \*\*Audit Logging\*\* - Automatic tracking of all user actions

\- \*\*API Documentation\*\* - Auto-generated OpenAPI 3.0 docs



\## 🛠️ Technology Stack



| Component | Technology |

|-----------|------------|

| Framework | Django 5.1.6 |

| REST API | Django REST Framework 3.15.1 |

| Authentication | JWT (SimpleJWT 5.3.1) |

| Database | PostgreSQL with psycopg v3 |

| Task Queue | Celery 5.3.6 + Redis 5.0.1 |

| API Docs | drf-spectacular 0.27.2 |

| CORS | django-cors-headers 4.3.1 |

| Config | python-decouple 3.8 |



\## 📋 Prerequisites



\- Python 3.10+

\- PostgreSQL 14+

\- Redis (for Celery task queue)



\## 🚀 Installation



\### 1. Clone the repository



```bash

git clone https://github.com/yourusername/dms-backend.git

cd dms-backend



\# Windows

python -m venv venv

venv\\Scripts\\activate



\# Linux/Mac

python3 -m venv venv

source venv/bin/activate


# Academic Assignment Helper & Plagiarism Detector (RAG-Powered)

A comprehensive backend + n8n automation system for academic assignment analysis, plagiarism detection, and research source suggestions using RAG (Retrieval-Augmented Generation).

## 🚀 Features

- **JWT-based Authentication**: Secure student registration and login
- **File Upload & Processing**: Support for PDF and DOCX files
- **RAG-based Source Suggestions**: Vector similarity search for relevant academic sources
- **AI-powered Plagiarism Detection**: Advanced analysis using OpenAI models
- **Structured Analysis Storage**: PostgreSQL database with pgvector extension
- **n8n Workflow Automation**: Complete automation pipeline
- **Required Notifications (Student → Teacher)**: Student receives results first; teacher is notified only after student confirms
- **Docker Compose Setup**: Easy deployment with all services orchestrated

## 📋 Prerequisites

- Docker Desktop installed and running
- WSL 2 configured (Windows users)
- OpenAI API key

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Natiabay/Plagiarism-Detection-and-Assignment-Helper.git
cd Plagiarism-Detection-and-Assignment-Helper
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Load Sample Academic Sources

The sample academic sources data is available in `data/sample_academic_sources.json`. 
You can load it into the database using a custom script or directly via the API after starting the services.

### 5. Configure n8n Workflow

1. Open n8n: http://localhost:5678 (admin/admin123)
2. Import workflow (student email + analysis): `workflows/assignment_analysis_workflow.json`
3. Import workflow (teacher email after student approval): `workflows/teacher_notification_workflow.json`
3. Configure credentials:
   - OpenAI API (used by embeddings + analysis)
   - Postgres (same database settings)
   - SMTP (for student + teacher emails)
4. Activate BOTH workflows

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register student
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/token` - OAuth2-compatible token endpoint (for Swagger UI)
- `POST /api/v1/auth/reset-password` - Reset password (for forgotten passwords)
- `POST /api/v1/auth/change-password` - Change password (requires authentication)

### Assignment & Analysis
- `POST /api/v1/upload` - Upload assignment (protected)
- `GET /api/v1/analysis/{analysis_id}` - Get analysis results by analysis ID (protected)
- `GET /api/v1/assignments/{assignment_id}/analysis` - Get analysis results by assignment ID (protected, recommended)
- `POST /api/v1/assignments/{assignment_id}/send-to-teacher` - Student-confirmed step: notify teacher (protected)
- `GET /api/v1/sources` - Search academic sources via RAG (protected)

## 🔗 Access Services

- **FastAPI Backend**: http://localhost:8000/docs
- **n8n Workflow**: http://localhost:5678
- **pgAdmin**: http://localhost:5050 (admin@academic.local / admin)

## 🏗️ Project Structure

```
├── backend/              # FastAPI backend application
├── workflows/            # n8n workflow exports
├── data/                 # Sample academic sources
├── init_db/              # Database initialization
├── docker-compose.yml    # Service orchestration
└── README.md            # This file
```

## 🔐 Security

- JWT-based authentication for all protected endpoints
- Password hashing with bcrypt
- Secure environment variable management

## 📖 Documentation

- API Documentation: http://localhost:8000/docs (when services are running)
- n8n Workflows:
  - Student-first analysis workflow: `workflows/assignment_analysis_workflow.json`
  - Teacher notification workflow: `workflows/teacher_notification_workflow.json`

## ✅ Required Notification Flow (Student → Teacher)

1. Student uploads assignment (`POST /api/v1/upload`) with JWT.
2. Backend triggers n8n analysis webhook.
3. n8n stores analysis and **emails the student** (required).
4. After the student checks results, student calls:
   - `POST /api/v1/assignments/{assignment_id}/send-to-teacher` (JWT required)
5. Backend triggers the **teacher notification** webhook.
6. n8n emails the teacher (required).

## 🐛 Troubleshooting

### Docker Issues
```bash
# Check services
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs n8n
```

### Database Connection
- Ensure PostgreSQL is healthy: `docker-compose ps postgres`
- Use `postgres` as hostname in n8n (not `localhost`)

## 📝 License

This project is for academic/educational purposes.

## 👤 Author

Natnael Abayneh

## 🔗 Repository

https://github.com/Natiabay/Plagiarism-Detection-and-Assignment-Helper.git

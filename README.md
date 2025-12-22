# Academic Assignment Helper & Plagiarism Detector (RAG-Powered)

A comprehensive backend + n8n automation system for academic assignment analysis, plagiarism detection, and research source suggestions using RAG (Retrieval-Augmented Generation).

## 🚀 Features

- **JWT-based Authentication**: Secure student registration and login
- **File Upload & Processing**: Support for PDF and DOCX files
- **RAG-based Source Suggestions**: Vector similarity search for relevant academic sources
- **AI-powered Plagiarism Detection**: Advanced analysis using OpenAI models
- **Structured Analysis Storage**: PostgreSQL database with pgvector extension
- **n8n Workflow Automation**: Complete automation pipeline
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

```bash
docker exec -it academic_backend python /app/../data/load_sample_sources.py
```

### 5. Configure n8n Workflow

1. Open n8n: http://localhost:5678 (admin/admin123)
2. Import workflow: `workflows/assignment_analysis_workflow.json`
3. Configure credentials:
   - OpenAI Chat Model (your API key)
   - Embeddings OpenAI (same API key)
   - Postgres PGVector Store (host: `postgres`, db: `academic_helper`)
   - Postgres (same database settings)
4. Activate workflow

## 📚 API Endpoints

- `POST /api/v1/auth/register` - Register student
- `POST /api/v1/auth/login` - Login and get JWT
- `POST /api/v1/upload` - Upload assignment (protected)
- `GET /api/v1/analysis/{id}` - Get analysis results (protected)
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
- n8n Workflow: Import `workflows/assignment_analysis_workflow.json`

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

Natiabay

## 🔗 Repository

https://github.com/Natiabay/Plagiarism-Detection-and-Assignment-Helper.git

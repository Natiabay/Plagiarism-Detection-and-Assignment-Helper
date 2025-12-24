# Academic Assignment Helper & Plagiarism Detector

Backend system that analyzes student assignments using RAG (vector search) and AI to detect plagiarism and suggest academic sources. Built with FastAPI, PostgreSQL + pgvector, and n8n automation.

## What It Does

Students upload assignments (PDF/DOCX), the system extracts text, searches a vector database of academic papers for similar content, runs AI analysis to detect plagiarism, and stores results. All protected with JWT authentication.

## Setup

**Requirements:**
- Docker Desktop
- OpenAI API key

**Steps:**

1. Clone the repo:
```bash
git clone https://github.com/Natiabay/Plagiarism-Detection-and-Assignment-Helper.git
cd Plagiarism-Detection-and-Assignment-Helper
```

2. Create `.env` file (copy from `.env.example`):
```env
OPENAI_API_KEY=your_key_here
POSTGRES_PASSWORD=your_password
JWT_SECRET_KEY=your_secret_min_32_chars
```

3. Start everything:
```bash
docker-compose up -d
```

4. Load sample academic sources:
The data is in `data/sample_academic_sources.json`. You'll need to load it into the database (script or manual import).

5. Setup n8n workflow:
- Go to http://localhost:5678 (admin/admin123)
- Import `workflows/assignment_analysis_workflow.json`
- Configure credentials: OpenAI API, Postgres (host: `postgres`, db: `academic_helper`), SMTP if using emails
- Activate the workflow

## API Endpoints

**Auth:**
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/login` - Get JWT token
- `POST /api/v1/auth/reset-password` - Reset password
- `POST /api/v1/auth/change-password` - Change password (needs JWT)

**Assignments:**
- `POST /api/v1/upload` - Upload assignment (needs JWT)
- `GET /api/v1/assignments/{id}/analysis` - Get analysis results (needs JWT)
- `GET /api/v1/sources?query=...` - Search academic sources (needs JWT)

Full API docs: http://localhost:8000/docs

## Services

- Backend: http://localhost:8000
- n8n: http://localhost:5678
- pgAdmin: http://localhost:5050 (admin@academic.local / admin)

## How It Works

1. Student uploads file → Backend extracts text
2. Backend calls n8n webhook with assignment data
3. n8n generates embeddings → Vector search in PostgreSQL
4. n8n runs AI analysis (GPT-4o-mini) with retrieved sources
5. Results saved to database
6. Student can retrieve analysis via API

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, JWT auth
- **Database:** PostgreSQL with pgvector extension
- **Automation:** n8n workflows
- **AI:** OpenAI (embeddings + GPT-4o-mini)
- **Deployment:** Docker Compose

## Project Structure

```
├── backend/          # FastAPI app
├── workflows/        # n8n workflow JSON
├── data/             # Sample academic sources
├── init_db/          # DB init scripts
├── docker-compose.yml
└── README.md
```

## Notes

- All endpoints except auth require JWT token
- Passwords hashed with bcrypt
- Vector search uses pgvector cosine similarity
- n8n workflow handles the full analysis pipeline

## Troubleshooting

**Services not starting?**
```bash
docker-compose ps
docker-compose logs backend
```

**Database connection issues?**
- Make sure postgres container is healthy
- In n8n, use `postgres` as hostname (not localhost)

## Author

Natnael Abayneh
# CareerLift AI

> **Dream. Prepare. Shine.**
>
> An AI-powered interview preparation platform built with Python Flask, IBM watsonx.ai, and IBM Granite models — featuring RAG, mock interviews, resume analysis, and a modern chat interface.

---

## 📋 Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Local Setup](#local-setup)
5. [Configuration](#configuration)
6. [Running the App](#running-the-app)
7. [IBM Cloud Deployment](#ibm-cloud-deployment)
8. [Project Structure](#project-structure)
9. [Customising the Agent](#customising-the-agent)
10. [Knowledge Base](#knowledge-base)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 AI Interview Coach | Chat with IBM Granite via watsonx.ai for personalised coaching |
| 🎯 Question Generator | Generate technical, behavioral, HR & coding questions |
| 🎤 Mock Interviews | Interactive sessions with real-time AI scoring (5 criteria) |
| 📄 Resume Analyser | Upload PDF/DOCX for ATS scoring & keyword analysis |
| 🗺️ Prep Roadmaps | Personalised week-by-week study plans |
| 📊 Progress Dashboard | Track sessions, scores, and achievement badges |
| 🌙 Dark / Light Mode | Elegant theme toggle persisted in localStorage |
| 🔍 RAG Retrieval | Knowledge base with 100+ interview Q&As, tips, trends |
| 🏢 Company-Specific | Tailored for Google, Amazon, Microsoft, Apple, IBM, etc. |
| 📱 Responsive | Mobile-first Bootstrap 5 design |

---

## 🏗️ Architecture

```
User Browser
    │
    ▼
Flask App (routes.py)
    │
    ├── RAG Retrieval (rag_retrieval.py)
    │      └── Knowledge Base (JSON + TXT files)
    │
    ├── Prompt Builder (prompt_builder.py)
    │      └── Agent Instructions (agent_instructions.py)
    │
    ├── watsonx.ai Client (watsonx_client.py)
    │      └── IBM Granite Model
    │
    ├── Resume Parser (resume_parser.py)
    │      └── pdfminer + python-docx
    │
    └── Progress Tracker (progress_tracker.py)
           └── Flask Session
```

---

## 🔧 Prerequisites

- Python 3.9+
- pip
- IBM Cloud account with watsonx.ai access
- IBM Granite model (e.g., `ibm/granite-13b-chat-v2`)

---

## 🚀 Local Setup

### 1. Clone / download the project

```bash
cd careerlift
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

```bash
cp .env.example .env
# Now edit .env with your IBM Cloud credentials
```

### 5. Run the app

```bash
python run.py
```

Open **http://localhost:5000** in your browser.

---

## ⚙️ Configuration

Edit **`.env`** (copy from `.env.example`):

```env
# IBM watsonx.ai
WATSONX_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# IBM Granite Model
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2

# Flask
FLASK_SECRET_KEY=change_this_to_a_long_random_string
```

### Getting IBM watsonx.ai Credentials

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Create a **watsonx.ai** service instance
3. Go to **Manage → Access (IAM) → API Keys** → Create API key
4. In watsonx.ai, create a **project** and copy its Project ID
5. Set `WATSONX_URL` to your region endpoint (default: `us-south`)

**Demo Mode**: If credentials are not configured, the app runs in demo mode with pre-written responses.

---

## ▶️ Running the App

### Development

```bash
python run.py
```

### Production (Gunicorn)

```bash
gunicorn run:app --bind 0.0.0.0:8080 --workers 2 --timeout 120
```

---

## ☁️ IBM Cloud Deployment

### Option A — IBM Code Engine (Recommended)

```bash
# Install IBM Cloud CLI
# https://cloud.ibm.com/docs/cli

# Login
ibmcloud login --sso

# Target resource group
ibmcloud target -g default

# Create Code Engine project
ibmcloud ce project create --name careerlift

# Select project
ibmcloud ce project select --name careerlift

# Deploy from source
ibmcloud ce application create \
  --name careerlift-app \
  --build-source . \
  --build-dockerfile Dockerfile \
  --env WATSONX_API_KEY=your_key \
  --env WATSONX_PROJECT_ID=your_project_id \
  --env FLASK_SECRET_KEY=your_secret \
  --port 5000 \
  --min-scale 1
```

### Option B — IBM Cloud Foundry

```bash
# Login
ibmcloud login --sso
ibmcloud target --cf

# Create manifest.yml with memory and env config
# Deploy
ibmcloud cf push careerlift -b python_buildpack -m 512M
```

### Option C — Docker

```bash
# Build
docker build -t careerlift .

# Run
docker run -p 5000:5000 \
  -e WATSONX_API_KEY=your_key \
  -e WATSONX_PROJECT_ID=your_project_id \
  -e FLASK_SECRET_KEY=your_secret \
  careerlift
```

#### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

---

## 📁 Project Structure

```
careerlift/
├── __init__.py               # Flask app factory
├── routes.py                 # All Flask routes & API endpoints
├── run.py                    # Entry point
├── app.yaml                  # IBM Cloud App Engine config
├── Procfile                  # Heroku/Code Engine Procfile
├── requirements.txt          # Python dependencies
├── .env.example              # Credential template
├── .gitignore
│
├── modules/
│   ├── agent_instructions.py # ⭐ Edit to customise the AI agent
│   ├── watsonx_client.py     # IBM watsonx.ai / Granite integration
│   ├── rag_retrieval.py      # RAG chunking & TF-IDF retrieval
│   ├── resume_parser.py      # PDF/DOCX resume parsing
│   ├── prompt_builder.py     # Prompt engineering for each use case
│   └── progress_tracker.py   # Session-based progress tracking
│
├── knowledge_base/
│   ├── behavioral_questions.json
│   ├── technical_questions.json
│   ├── company_tips.json
│   ├── hr_questions.json
│   └── resume_guide.txt
│
├── templates/
│   ├── base.html             # Base template (navbar, footer, theme)
│   ├── index.html            # Landing page
│   ├── chat.html             # AI Coach chat interface
│   ├── generate.html         # Question generator
│   ├── mock.html             # Mock interview
│   ├── resume.html           # Resume analyser
│   └── dashboard.html        # Progress dashboard
│
├── static/
│   ├── css/styles.css        # Complete design system
│   └── js/app.js             # Modular JS (chat, generate, mock, resume)
│
└── uploads/                  # Uploaded resumes (auto-cleaned)
```

---

## 🎛️ Customising the Agent

Edit **`modules/agent_instructions.py`** to change:

```python
AGENT_INSTRUCTIONS = {
    "name": "CareerLift Coach",
    "welcome_message": "...",
    "personality": "Encouraging, professional, and insightful",
    "tone": "Warm but expert",
    "difficulty_levels": { "fresher": "...", "mid": "...", ... },
    "mock_interview": {
        "questions_per_session": 10,
        "scoring_rubric": { ... },
    },
    "safety_rules": [...],
    "system_prompt": "You are CareerLift Coach...",
    "rag": { "top_k_chunks": 5 },
}
```

**No other file needs changing** — all agent behaviour flows from this single config.

---

## 📚 Knowledge Base

Add more knowledge by dropping JSON files into `knowledge_base/`:

```json
[
  {
    "category": "technical",
    "role": "Data Engineer",
    "question": "Explain the difference between OLTP and OLAP.",
    "answer": "OLTP handles transactional workloads (INSERT/UPDATE/DELETE), optimised for high-concurrency writes. OLAP handles analytical queries (aggregations, reporting), optimised for large-scale reads.",
    "tip": "Mention real-world examples: MySQL/PostgreSQL for OLTP; Redshift/BigQuery for OLAP."
  }
]
```

The RAG engine automatically indexes all new files on startup.

---

## 🔒 Security Notes

- Never commit `.env` to version control
- Rotate `FLASK_SECRET_KEY` for production
- Uploaded resumes are stored locally — add cloud object storage for production
- The app uses Flask sessions (cookie-based) — add Redis for multi-worker deployments

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.0 |
| AI / LLM | IBM watsonx.ai, IBM Granite |
| RAG | Custom TF-IDF cosine similarity |
| Resume Parsing | pdfminer.six, python-docx |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Markdown | marked.js, highlight.js |
| Deployment | Gunicorn, IBM Code Engine / Cloud Foundry |

---

## 📄 License

MIT License — Free for personal and commercial use.

---

**CareerLift AI** — *Dream. Prepare. Shine.* ⚡

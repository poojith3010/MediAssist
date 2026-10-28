# MediAssist AI

MediAssist is a local-first educational healthcare information application. It is not a medical device and must not be used to diagnose conditions or prescribe treatment.

## Current status

The foundation includes a FastAPI API, secure password hashing, cookie authentication, per-user PDF access controls, PDF text extraction, retrieval-grounded Ollama chat, a React/Vite landing page, and Docker development services. See [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Windows quick start

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PYTHONPATH = "backend"
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env`. PostgreSQL is supported through `DATABASE_URL`; the default development database is SQLite so the core app runs without paid services. Install Ollama separately, then manually download a model such as `ollama pull llama3.2:3b`. Model size and performance depend on hardware; never download a model automatically.

Run tests with `pytest`. Create/update the database with `alembic upgrade head`. Train the experimental model with `$env:PYTHONPATH="backend"; python -m app.train_model`; it uses scikit-learn's documented breast-cancer teaching dataset and is not clinically validated. The optional local AI dependencies are installed with `pip install -e ".[ai]"`. Sentence Transformers downloads its selected model once unless it is already cached; inference remains local. OCR additionally requires the free Tesseract executable installed on Windows and available on `PATH`. No uploaded documents are sent to external AI providers.

The frontend runs from `frontend` with `npm install` and `npm run dev`. Set `VITE_API_URL` if the API is not at `http://localhost:8000`. Docker starts the backend and PostgreSQL with `docker compose up --build`; Ollama remains a separately installed local service so models are never downloaded during image builds.

## Safety and licensing

Use only synthetic or legally authorized documents. Review licenses for PyMuPDF, models, public-health source material, and any optional dependency before redistribution. Ollama and downloaded models have their own terms. This project makes no regulatory or clinical compliance claim.

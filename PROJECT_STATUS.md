# Project status

## Completed

- Local-first FastAPI/SQLAlchemy foundation with SQLite development default and PostgreSQL configuration.
- Registration, login, logout, Argon2 password hashing, expiring signed HttpOnly session cookie, and authorization checks.
- PDF type/size validation, safe filenames, text extraction, OCR-needed status, document listing/detail/deletion, and owner isolation.
- Retrieval-grounded local Ollama chat with source title/page references and explicit unavailable-service errors.
- Experimental scikit-learn training script and protected prediction endpoint with model-not-trained errors.
- React/Vite authentication/dashboard UI, Dockerfile, Compose PostgreSQL service, environment example, and initial test.
- Alembic initial migration, local Sentence Transformer/FAISS retrieval when optional AI dependencies are installed, OCR hook for scanned PDFs, summaries, persisted conversations, and SHAP explanations.

## Remaining production work

- Add a distributed job queue/rate limiter, retention automation, observability, secret management, and deployment hardening before real-world use.
- Expand the current smoke/integration tests into a full end-to-end regression suite.

## Verification

- Backend: `2 passed` with pytest.
- Frontend: Vite production build succeeded.
- Alembic: `0001_initial (head)`.
- Model training: succeeded with held-out accuracy 0.9561 and ROC-AUC 0.9939 on the bundled educational dataset. These metrics are not clinical evidence.

## Next commands

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PYTHONPATH = "backend"
alembic upgrade head
$env:PYTHONPATH = "backend"
pytest
Set-Location frontend
npm install
npm run build
uvicorn app.main:app --reload
```

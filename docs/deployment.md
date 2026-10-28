# Local deployment

For Windows development, create a virtual environment, install `.[dev]`, copy `.env.example` to `.env`, run `alembic upgrade head`, and start Uvicorn. Start the frontend separately with `npm install` and `npm run dev`.

Docker Compose starts PostgreSQL and the backend. Install Ollama on the host and manually run `ollama pull llama3.2:3b`; the model is never downloaded during Docker builds.

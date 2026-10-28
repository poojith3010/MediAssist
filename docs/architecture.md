# Architecture

The application is a local-first React/Vite client and FastAPI service. SQLAlchemy stores users, documents, chunks, conversations, messages, source references, and summaries in SQLite for zero-setup development or PostgreSQL for multi-process local deployments.

PDF text is extracted in the backend. Optional Tesseract handles image-only pages. Sentence Transformers creates local embeddings and FAISS performs in-process similarity search. Ollama receives only a bounded prompt assembled from the authenticated user's retrieved chunks.

The scikit-learn risk model is a separate experimental workflow. It is not used by chat and is not clinically validated.

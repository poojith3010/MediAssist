# Limitations

This is an educational prototype. OCR depends on a local Tesseract installation. Embedding model downloads require internet once, and inference requires sufficient local memory. In-process FAISS indexes and signed-cookie sessions are suitable for local development, not horizontal production deployments. Add a managed job queue, distributed rate limiting, secret management, observability, retention automation, formal threat modeling, and clinical/legal review before any real-world use.

# API

All endpoints are under `/api/v1`.

Authentication: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, and `GET /users/me`.

Documents: `POST /documents`, `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}`, and `POST /documents/{id}/summarize`.

Chat: `POST /chat`, `GET /conversations`, and `GET /conversations/{id}`.

Experimental ML: `POST /risk-assessment/predict` and `POST /risk-assessment/explain`. These endpoints require an authenticated session and explicitly return informational-only results.

Operational endpoints: `GET /health` and `GET /ready`.

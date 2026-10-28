# Security

- Passwords use Argon2 and are never logged or returned.
- Sessions are signed, HttpOnly cookies with configurable expiration.
- Every document and conversation query includes the authenticated owner.
- Uploads enforce PDF content type, size limits, basename normalization, and bounded extraction.
- Prompts are constructed with untrusted document text as context; document text cannot alter authorization.
- Local model failures return safe service errors rather than fabricated answers.

This project is educational and makes no HIPAA, GDPR, medical-device, or other regulatory compliance claim. Use synthetic data during development.

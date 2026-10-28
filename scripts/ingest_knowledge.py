"""Import an approved local text/PDF file into a user's document library.

This intentionally accepts local files only. Review reuse terms before importing
public-health material and do not use it for real patient records.
"""
import argparse
import os
from pathlib import Path

import fitz
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services import index_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    if not args.path.is_file():
        raise SystemExit(f"File not found: {args.path}")
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == args.email.lower()))
        if user is None:
            raise SystemExit("User does not exist; register through the application first")
        if args.path.suffix.lower() == ".pdf":
            pdf = fitz.open(args.path)
            pages = [(page.get_text("text") or "").strip() for page in pdf]
        else:
            pages = [args.path.read_text(encoding="utf-8")]
        document = Document(owner_id=user.id, filename=args.path.name, extracted_text="\n\n".join(pages), status="processed")
        document.chunks = [DocumentChunk(content=page, page_number=i + 1) for i, page in enumerate(pages) if page]
        index_chunks(document.chunks)
        db.add(document)
        db.commit()
        print(f"Imported {args.path.name} for {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", "backend")
    main()

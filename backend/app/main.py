from pathlib import Path

import fitz
from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import Base, engine, get_db
from .models import Conversation, Document, DocumentChunk, Message, SourceReference, Summary, User
from .ml import explain, predict
from .schemas import AuthInput, ChatInput, ChatOut, ConversationOut, DocumentOut, MessageOut, RiskInput, SourceOut, SummaryOut, UserOut
from .security import create_session, current_user, hash_password, verify_password
from .services import ask_ollama, index_chunks, retrieve, summarize_with_ollama

settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(engine)
app = FastAPI(title="MediAssist AI", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(User).limit(1))
    return {"status": "ready"}


@app.post("/api/v1/auth/register", response_model=UserOut, status_code=201)
def register(payload: AuthInput, response: Response, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    response.set_cookie("mediassist_session", create_session(user.id, settings.app_secret), httponly=True, samesite="lax")
    return user


@app.post("/api/v1/auth/login", response_model=UserOut)
def login(payload: AuthInput, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    response.set_cookie("mediassist_session", create_session(user.id, settings.app_secret), httponly=True, samesite="lax")
    return user


@app.post("/api/v1/auth/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie("mediassist_session")


@app.get("/api/v1/users/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@app.post("/api/v1/documents", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)) -> Document:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are supported")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds configured size limit")
    try:
        pdf = fitz.open(stream=content, filetype="pdf")
        pages = [(page.get_text("text") or "").strip() for page in pdf]
        if not any(pages):
            try:
                import pytesseract
                from PIL import Image

                pages = [pytesseract.image_to_string(Image.frombytes("RGB", [pix.width, pix.height], pix.samples)).strip() for page in pdf for pix in [page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))]]
            except ImportError:
                pages = []
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to extract PDF text") from exc
    text = "\n\n".join(pages).strip()
    document = Document(owner_id=user.id, filename=Path(file.filename or "document.pdf").name, extracted_text=text, status="processed" if text else "needs_ocr")
    document.chunks = [DocumentChunk(content=page, page_number=index + 1) for index, page in enumerate(pages) if page]
    index_chunks(document.chunks)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@app.get("/api/v1/documents", response_model=list[DocumentOut])
def documents(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc())))


@app.get("/api/v1/documents/{document_id}", response_model=DocumentOut)
def document(document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Document:
    item = db.scalar(select(Document).where(Document.id == document_id, Document.owner_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return item


@app.delete("/api/v1/documents/{document_id}", status_code=204)
def delete_document(document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    item = db.scalar(select(Document).where(Document.id == document_id, Document.owner_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(item)
    db.commit()


@app.post("/api/v1/chat", response_model=ChatOut)
async def chat(payload: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ChatOut:
    documents = list(db.scalars(select(Document).where(Document.owner_id == user.id)))
    chunks = retrieve(payload.question, documents)
    try:
        answer = await ask_ollama(payload.question, chunks)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Local Ollama service is unavailable or returned an invalid response") from exc
    conversation = Conversation(owner_id=user.id, title=payload.question[:200])
    user_message = Message(role="user", content=payload.question)
    assistant_message = Message(role="assistant", content=answer)
    conversation.messages = [user_message, assistant_message]
    db.add(conversation)
    db.flush()
    sources = [SourceOut(document_id=c.document.id, title=c.document.filename, page_number=c.page_number) for c in chunks]
    assistant_message.sources = [SourceReference(document_id=source.document_id, page_number=source.page_number) for source in sources]
    db.commit()
    return ChatOut(answer=answer, sources=sources)


@app.get("/api/v1/conversations", response_model=list[ConversationOut])
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Conversation]:
    return list(db.scalars(select(Conversation).where(Conversation.owner_id == user.id).order_by(Conversation.created_at.desc())))


@app.get("/api/v1/conversations/{conversation_id}", response_model=list[MessageOut])
def conversation_messages(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Message]:
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.owner_id == user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [
        MessageOut(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            sources=[
                SourceOut(document_id=source.document_id, title=f"Document {source.document_id}", page_number=source.page_number)
                for source in message.sources
            ],
        )
        for message in conversation.messages
    ]


@app.post("/api/v1/documents/{document_id}/summarize", response_model=SummaryOut)
async def summarize(document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Summary:
    item = db.scalar(select(Document).where(Document.id == document_id, Document.owner_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        content = await summarize_with_ollama(item)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Local Ollama service is unavailable or returned an invalid summary") from exc
    summary = Summary(document_id=item.id, content=content)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


@app.post("/api/v1/risk-assessment/predict")
def risk_assessment(payload: RiskInput, user: User = Depends(current_user)) -> dict:
    try:
        return predict(payload.features)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/risk-assessment/explain")
def risk_explanation(payload: RiskInput, user: User = Depends(current_user)) -> dict:
    try:
        return explain(payload.features)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

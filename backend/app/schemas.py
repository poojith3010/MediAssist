from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    status: str
    extracted_text: str
    created_at: datetime


class ChatInput(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class SourceOut(BaseModel):
    document_id: int
    title: str
    page_number: int | None


class ChatOut(BaseModel):
    answer: str
    sources: list[SourceOut]


class RiskInput(BaseModel):
    features: dict[str, float] = Field(min_length=1)


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    sources: list[SourceOut] = []


class SummaryOut(BaseModel):
    id: int
    document_id: int
    content: str
    created_at: datetime

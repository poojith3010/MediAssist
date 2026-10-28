"""Initial MediAssist schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(512), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("filename", sa.String(255), nullable=False), sa.Column("extracted_text", sa.Text(), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_table("document_chunks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("page_number", sa.Integer()), sa.Column("embedding", sa.Text()))
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_table("conversations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_conversations_owner_id", "conversations", ["owner_id"])
    op.create_table("messages", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table("source_references", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False), sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("page_number", sa.Integer()))
    op.create_index("ix_source_references_message_id", "source_references", ["message_id"])
    op.create_table("summaries", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_summaries_document_id", "summaries", ["document_id"])


def downgrade():
    op.drop_table("summaries")
    op.drop_table("source_references")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("users")

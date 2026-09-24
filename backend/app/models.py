from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    repository_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    application_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    health_endpoint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    environment: Mapped[str] = mapped_column(
        String(100),
        default="development",
    )

    incident_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    current_version: Mapped[str] = mapped_column(
        String(100),
        default="1.0.0",
    )

    previous_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    deployment_status: Mapped[str] = mapped_column(
        String(100),
        default="healthy",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        index=True,
    )

    tool: Mapped[str] = mapped_column(String(255))

    arguments: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
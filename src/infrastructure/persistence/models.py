from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    dicks: Mapped[list["DickModel"]] = relationship(back_populates="user")


class DickModel(Base):
    __tablename__ = "dicks"
    __table_args__ = (UniqueConstraint("user_id", "chat_id", name="uq_dicks_user_chat"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    size_cm: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_grow_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[UserModel] = relationship(back_populates="dicks")

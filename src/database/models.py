from datetime import datetime

from sqlalchemy import String, Column, Integer, Text, Sequence, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class ShortURL(Base):
    __tablename__ = "short_urls"

    # id = Column(Integer, Sequence('short_urls_id_seq'), primary_key=True)
    # slug = Column(String(100), unique=True, nullable=False, index=True)
    # long_url = Column(String(2048), nullable=False, index=True)
    # expiration_date = Column(DateTime, index=True)
    # user_id = Column(Integer, nullable=False)
    # hop_counts = Column(Integer, default=0, nullable=False)
    # password = Column(String(2048), default=None)
    # is_private = Column(Boolean, nullable=False, default=False)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    long_url: Mapped[str] = mapped_column(nullable=False)
    expiration_date: Mapped[datetime] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False)
    hop_counts: Mapped[int] = mapped_column(default=0, nullable=False)
    password: Mapped[str] = mapped_column(default=None)
    is_private: Mapped[bool] = mapped_column(nullable=False, default=False)


class UserModel(Base):
    __tablename__ = "users"

    # id = Column(Integer, Sequence('users_id_seq'), primary_key=True)
    # login = Column(String(100), unique=True, nullable=False, index=True)
    # password = Column(String(2048), nullable=False)
    # email_is_valid = Column(Boolean, nullable=False, default=False)

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    email_is_valid: Mapped[bool] = mapped_column(nullable=False, default=False)


class RedirectsHistory(Base):
    __tablename__ = "redirects_history"

    # id = Column(Integer, Sequence('redirects_history_id_seq'), primary_key=True)
    # created_by = Column(String(), nullable=False, index=True)
    # slug = Column(String(2048), nullable=False, index=True)
    # long_url = Column(String(2048), nullable=False, index=True)
    # location_city = Column(String(2048), nullable=False, index=True)
    # location_country = Column(String(2048), nullable=False, index=True)
    # time = Column(String(2048), nullable=False, index=True)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False, index=True)
    long_url: Mapped[str] = mapped_column(nullable=False, index=True)
    location_city: Mapped[str] = mapped_column(nullable=False)
    location_country: Mapped[str] = mapped_column(nullable=False)
    time: Mapped[str] = mapped_column(nullable=False)


class PasswordReset(Base):
    __tablename__ = "password_reset"
    #
    # id = Column(Integer, Sequence('password_reset_id_seq'), primary_key=True)
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # token_hash = Column(String(2048), nullable=False, index=True)
    # email = Column(String(2048), nullable=False, index=True)
    # created_at = Column(DateTime, nullable=False, index=True)
    # expires_at = Column(DateTime, nullable=False, index=True)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(nullable=False, index=True)
    email: Mapped[str] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    users = relationship("UserModel")


class EmailValidation(Base):
    __tablename__ = "email_validations"

    # id = Column(Integer, Sequence('email_validations_id_seq'), primary_key=True)
    # token_hash = Column(String(2048), nullable=False, index=True)
    # email = Column(String(2048), nullable=False, index=True)
    # created_at = Column(DateTime, nullable=False, index=True)
    # expires_at = Column(DateTime, nullable=False, index=True)

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(nullable=False, index=True)
    email: Mapped[str] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class ServiceNews(Base):
    __tablename__ = "service_news"
    
    # id = Column(Integer, Sequence('service_news_id_seq'), primary_key=True)
    # created_at = Column(DateTime, nullable=False, index=True)
    # content = Column(Text, nullable=False, index=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False, index=True)

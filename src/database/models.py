from sqlalchemy import String, Column, Integer, Sequence, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class ShortURL(Base):
    __tablename__ = "short_urls"

    # slug: Mapped[str] = mapped_column(primary_key=True)
    # long_url: Mapped[str]

    id = Column(Integer, Sequence('short_urls_id_seq'), primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    long_url = Column(String(2048), nullable=False, index=True)
    expiration_date = Column(DateTime, index=True)
    user_id = Column(Integer, nullable=False)
    hop_counts = Column(Integer, default=0, nullable=False)
    password = Column(String(2048), default=None)
    is_private = Column(Boolean, nullable=False, default=False)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence('users_id_seq'), primary_key=True)
    login = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(2048), nullable=False)
    email_is_valid = Column(Boolean, nullable=False, default=False)


class RedirectsHistory(Base):
    __tablename__ = "redirects_history"

    id = Column(Integer, Sequence('redirects_history_id_seq'), primary_key=True)
    created_by = Column(String(), nullable=False, index=True)
    slug = Column(String(2048), nullable=False, index=True)
    long_url = Column(String(2048), nullable=False, index=True)
    location_city = Column(String(2048), nullable=False, index=True)
    location_country = Column(String(2048), nullable=False, index=True)
    time = Column(String(2048), nullable=False, index=True)


class PasswordReset(Base):
    __tablename__ = "password_reset"

    id = Column(Integer, Sequence('password_reset_id_seq'), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(2048), nullable=False, index=True)
    email = Column(String(2048), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    user = relationship("UserModel")


class EmailValidation(Base):
    __tablename__ = "email_validations"

    id = Column(Integer, Sequence('email_validations_id_seq'), primary_key=True)
    token_hash = Column(String(2048), nullable=False, index=True)
    email = Column(String(2048), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)



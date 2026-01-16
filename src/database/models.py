from sqlalchemy import String, Column, Integer, Sequence
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class ShortURL(Base):
    __tablename__ = "short_urls"

    # slug: Mapped[str] = mapped_column(primary_key=True)
    # long_url: Mapped[str]

    id = Column(Integer, Sequence('short_urls_id_seq'), primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    long_url = Column(String(2048), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    hop_counts = Column(Integer, default=0, nullable=False)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence('users_id_seq'), primary_key=True)
    login = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(2048), nullable=False)


class RedirectsHistory(Base):
    __tablename__ = "redirects_history"

    id = Column(Integer, Sequence('redirects_history_id_seq'), primary_key=True)
    created_by = Column(String(), nullable=False, index=True)
    slug = Column(String(2048), nullable=False, index=True)
    long_url = Column(String(2048), nullable=False, index=True)
    location_city = Column(String(2048), nullable=False, index=True)
    location_country = Column(String(2048), nullable=False, index=True)
    time = Column(String(2048), nullable=False, index=True)




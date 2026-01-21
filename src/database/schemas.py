from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional

from src.database.models import UserModel


class UserSchema(BaseModel):
    id: int
    login: EmailStr
    password: str


class AddSlug(BaseModel):
    slug: str
    long_url: HttpUrl
    expiration_time: datetime | None
    user_id: int
    hop_count: int


class UserAddSchema(BaseModel):
    login: EmailStr
    password: str


class SetExpirationTimeForSlug(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int


class UserUpdateSchema(BaseModel):
    login: Optional[EmailStr] = Field(default=UserModel.login)
    password: Optional[str] = Field(default=UserModel.password)



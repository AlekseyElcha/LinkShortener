from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional

from src.database.models import UserModel


class UserSchema(BaseModel):
    id: int
    login: EmailStr
    password: str

# not used
class AddSlug(BaseModel):
    long_url: HttpUrl


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



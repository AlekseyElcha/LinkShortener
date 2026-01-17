from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from src.database.models import UserModel

class UserSchema(BaseModel):
    id: int
    login: EmailStr
    password: str


class UserAddSchema(BaseModel):
    login: EmailStr
    password: str


class UserUpdateSchema(BaseModel):
    login: Optional[EmailStr] = Field(default=UserModel.login)
    password: Optional[str] = Field(default=UserModel.password)




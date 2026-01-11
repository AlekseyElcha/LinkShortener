from pydantic import BaseModel, Field
from typing import Optional

from src.database.models import UserModel

class UserSchema(BaseModel):
    id: int
    login: str
    password: str


class UserAddSchema(BaseModel):
    login: str
    password: str


class UserUpdateSchema(BaseModel):
    login: Optional[str] = Field(default=UserModel.login)
    password: Optional[str] = Field(default=UserModel.password)

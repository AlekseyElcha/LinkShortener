import bcrypt
from fastapi import Depends, HTTPException, Response, APIRouter, Body, Request, status
from authx import AuthXConfig, AuthX
from sqlalchemy import select
from typing import Annotated
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from src.get_session import get_session
from src.database.models import UserModel
from src.database.schemas import UserAddSchema

router = APIRouter(prefix="/auth")

load_dotenv(".env")
config = AuthXConfig()
config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_ALGORITHM = "HS256"
config.JWT_ACCESS_COOKIE_NAME = "auth_cookies"
config.JWT_COOKIE_CSRF_PROTECT = False
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
config.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
security = AuthX(config=config)

def hash_data(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

@router.post("/login")
async def login(
        session: Annotated[AsyncSession, Depends(get_session)],
        login: Annotated[str, Body(embed=True)],
        password: Annotated[str, Body(embed=True)],
        response: Response = None,
):
    query = select(UserModel).where(UserModel.login == login)
    result = await session.execute(query)
    data = result.scalar_one_or_none()
    if data:
        if not verify_password(password, data.password):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Неверный логин или пароль.")
        token = security.create_access_token(uid=login)
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        security.set_access_cookies(token, response)
        if data.email_is_valid:
            return {
                "access_token": token,
                "user": {
                    "login": data.login,
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Почта не была подтверждена! Подтвердите почту.")
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")


@router.post("/create_account")
async def create_account(user: UserAddSchema,
                         session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        new_user = UserModel(
            login=user.login,
            password=hash_data(user.password),
            email_is_valid=False,
        )
        session.add(new_user)
        try:
            await session.commit()
            await session.refresh(new_user)
        except:
            raise HTTPException(status.HTTP_306_RESERVED, detail="Аккаунт с такой почтой уже сущеcтвует")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании аккаунта")
    return {
        "new_user": {
            "login": new_user.login,
            "password": hash_data(new_user.password),
        },
        "message": "Аккаунт успешно создан!"
    }


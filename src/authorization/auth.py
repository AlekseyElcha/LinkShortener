from fastapi import Depends, HTTPException, Response, APIRouter, Body, Request, status
from authx import AuthXConfig, AuthX
from sqlalchemy import select
from typing import Annotated
from dotenv import load_dotenv
import jwt
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.get_session import get_session
from src.database.models import UserModel
from src.database.schemas import UserAddSchema, UserUpdateSchema
from src.exeptions import CriticalDatabaseError

router = APIRouter(prefix="/auth")

load_dotenv(".env")
config = AuthXConfig()
config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_ALGORITHM = "HS256"
config.JWT_ACCESS_COOKIE_NAME = "auth_cookies"
config.JWT_COOKIE_CSRF_PROTECT = False
security = AuthX(config=config)

@router.post("/login")
async def login(
        session: Annotated[AsyncSession, Depends(get_session)],
        login: Annotated[str, Body(embed=True)],
        password: Annotated[str, Body(embed=True)],
        response: Response = None,
):
    query = select(UserModel).where(login == UserModel.login).where(password == UserModel.password)
    result = await session.execute(query)
    data = result.scalar_one_or_none()
    if data:
        token = security.create_access_token(uid=login)
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        security.set_access_cookies(token, response)

        return {
            "access_token": token,
            "user": {
                "login": data.login,
                "password": data.password,
            }
        }
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")


@router.post("/create_account")
async def create_account(user: UserAddSchema,
                         session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        new_user = UserModel(
            login=user.login,
            password=user.password,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании аккаунта")
    return {
        "new_user": {
            "login": new_user.login,
            "password": new_user.password,
        },
        "message": "Аккаунт успешно создан!"
    }

# async def admin_required(user = Depends(security.access_token_required)):
#     try:
#         is_admin = user.get("is_admin")
#     except AttributeError:
#         is_admin = getattr(user, 'is_admin', False)
#     if not is_admin:
#         raise HTTPException(status_code=403, detail="Требуются права администратора")
#     return user

def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        print(f"Token payload: {payload}")
        return payload
    except Exception as e:
        print(f"Token decode error: {e}")
        return {}

async def check_auth(request: Request, session: AsyncSession):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    if token:
        login = decode_token(token).get("sub")
        return await get_user_id_by_login(login, session)
    return False

async def check_auth_account(request: Request, session: AsyncSession):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    if token:
        login = decode_token(token).get("sub")
        return await get_user_id_by_login(login, session)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Авторизация неверна.")

async def get_user_id_by_login(login: str, session: AsyncSession):
    query = select(UserModel.id).where(login == UserModel.login)
    res = await session.execute(query)
    return res.scalar_one_or_none()

import base64

from fastapi import Depends, HTTPException, Response, APIRouter, Body, Request, status
from authx import AuthXConfig, AuthX
from sqlalchemy import select, update, delete
from typing import Annotated
from dotenv import load_dotenv
import jwt
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.sql.functions import user

from src.get_session import get_session
from src.database.models import UserModel, PasswordReset
from src.database.schemas import UserAddSchema, UserUpdateSchema
from src.services.email_sender import send_reset_password_email, send_reset_password_email_notification
from src.exeptions import SendEmailError, CreateResetPasswordLinkError

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


def decode_token_urlsafe(token: str) -> bytes:
    """
    Декодирует URL-safe Base64 токен обратно в байты
    """
    # 1. Заменяем обратно URL-safe символы
    token = token.replace('-', '+').replace('_', '/')

    # 2. Добавляем padding ('=') если нужно
    padding = 4 - (len(token) % 4)
    if padding != 4:
        token += '=' * padding

    # 3. Декодируем Base64
    return base64.urlsafe_b64decode(token)


async def create_link_with_token(login: str, session: AsyncSession):
    reset_token = secrets.token_urlsafe(32)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=1)
    # reset_url = f"http://localhost:8000/reset_password?token={reset_token}"
    reset_url = f"http://localhost:8000/?token={reset_token}"
    print(reset_url)
    user_id = await get_user_id_by_login(login, session)
    reset_request = PasswordReset(
        user_id=user_id,
        token_hash=reset_token,
        email=login,
        created_at=created_at,
        expires_at=expires_at,
        is_used=False
    )

    session.add(reset_request)
    try:
        await session.commit()
    except:
        raise CreateResetPasswordLinkError

    return reset_url


async def send_reset_password_email_with_instructions(email: str, reset_url: str):
    try:
        await send_reset_password_email(email, reset_url)
    except SendEmailError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при отправке письма.")


async def check_token_and_reset_password(token: str, new_password: str, session: AsyncSession):
    query = select(PasswordReset.expires_at).where(PasswordReset.token_hash == token)
    try:
        res = await session.execute(query)
        expires_at = res.scalar_one_or_none()
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Возникла ошибка при проверке токена")
    exp = datetime.fromisoformat(str(expires_at))
    now = datetime.fromisoformat(str(datetime.utcnow()))
    if exp < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Время дейстаия ссылки истекло")

    query = select(PasswordReset.email).where(PasswordReset.token_hash == token)
    try:
        res = await session.execute(query)
        login = res.scalar_one_or_none()
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Возникла ошибка при плучении логина")

    query = update(UserModel).where(UserModel.login == login).values(password=new_password)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось обновить пароль")

    query = delete(PasswordReset).where(PasswordReset.email == login)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить PasswordReset запрос из базы данных"
        )
    await send_reset_password_email_notification(user_email=login)



def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except Exception as e:
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

async def check_auth_get_login(request: Request):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    if token:
        login = decode_token(token).get("sub")
        return login
    return "Пользователь"

async def get_user_id_by_login(login: str, session: AsyncSession):
    query = select(UserModel.id).where(login == UserModel.login)
    res = await session.execute(query)
    return res.scalar_one_or_none()

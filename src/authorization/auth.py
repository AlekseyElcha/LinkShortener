import base64

import bcrypt
from fastapi import Depends, HTTPException, Response, APIRouter, Body, Request, status
from authx import AuthXConfig, AuthX
from sqlalchemy import select, update, delete
from typing import Annotated
from dotenv import load_dotenv
from passlib.context import CryptContext
import jwt
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.orm import session
from sqlalchemy.sql.functions import user
from src.get_session import get_session
from src.database.models import UserModel, PasswordReset, EmailValidation
from src.database.schemas import UserAddSchema, UserUpdateSchema
from src.services.email_sender import send_reset_password_email, send_reset_password_email_notification, \
    send_email_validation
from src.exeptions import SendEmailError, CreateResetPasswordLinkError, CreateEmailValidationLinkError, \
    UserIdByLoginNotFoundError, UserNotFoundError

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


async def validate_user_email(email: str, session: AsyncSession):
    query = select(UserModel.email_is_valid).where(UserModel.login == email)
    try:
        res = await session.execute(query)
        is_valid = res.scalar_one_or_none()
        if is_valid:
            return True
        return False
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сервера при проверке авторизации.")



async def create_link_with_token(login: str, session: AsyncSession):
    reset_token = secrets.token_urlsafe(32)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=1)
    # reset_url = f"http://localhost:8000/reset_password?token={reset_token}"
    # reset_url = f"http://localhost:8080/api/?token={reset_token}"   для работы с nginx
    reset_url = f"http://localhost:8000/?token={reset_token}"
    print(reset_url)
    user_id = await get_user_id_by_login(login, session)
    if user_id is None:
        raise UserIdByLoginNotFoundError
    reset_request = PasswordReset(
        user_id=user_id,
        token_hash=reset_token,
        email=login,
        created_at=created_at,
        expires_at=expires_at,
    )

    session.add(reset_request)
    try:
        await session.commit()
        await session.close()
    except:
        raise CreateResetPasswordLinkError

    return reset_url


async def create_validation_link(login: str, session: AsyncSession):
    validate_token = secrets.token_urlsafe(32)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=1)
    # validate_email_url = f"http://localhost:8080/api/?validate_token={validate_token}" для работы с nginx
    validate_email_url = f"http://localhost:8080/?validate_token={validate_token}"
    print(validate_email_url)
    validate_email_request = EmailValidation(
        token_hash=validate_token,
        email=login,
        created_at=created_at,
        expires_at=expires_at
    )
    session.add(validate_email_request)
    try:
        await session.commit()
        await session.close()
    except:
        raise CreateEmailValidationLinkError

    return validate_email_url



async def check_token_and_validate_user_email(token: str, session: AsyncSession):
    query = select(EmailValidation.expires_at).where(EmailValidation.token_hash == token)
    try:
        res = await session.execute(query)
        expires_at = res.scalar_one_or_none()
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Возникла ошибка при проверке токена")
    exp = datetime.fromisoformat(str(expires_at))
    now = datetime.fromisoformat(str(datetime.utcnow()))
    if exp < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Время действия ссылки истекло")

    query = select(EmailValidation.email).where(EmailValidation.token_hash == token)
    try:
        res = await session.execute(query)
        login = res.scalar_one_or_none()
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Возникла ошибка при получении логина")

    query = update(UserModel).where(UserModel.login == login).values(email_is_valid=True)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось обновить статус почты")

    query = delete(EmailValidation).where(EmailValidation.email == login)
    try:
        await session.execute(query)
        await session.commit()
        await session.close()
    except:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить EmailValidation запрос из базы данных"
        )
    return {"message": "Почта успешно подтверждена."}


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
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Возникла ошибка при получении логина")

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
        await session.close()
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


async def check_user_auth(request: Request, session: AsyncSession, id_to_check: int):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    if token:
        login = decode_token(token).get("sub")
        user_id_required = await get_user_id_by_login(login, session)
        if user_id_required == id_to_check:
            return True
        return False
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
    await session.close()
    if res:
        return res.scalar_one_or_none()
    raise UserNotFoundError
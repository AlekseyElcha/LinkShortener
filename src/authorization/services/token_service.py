import base64
import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from src.authorization.auth import config
import jwt

from src.authorization.services.auth_service import get_user_id_by_login
from src.database.models import PasswordReset
from src.exeptions import UserIdByLoginNotFoundError, CreateResetPasswordLinkError, SendEmailError
from src.services.email_service import send_reset_password_email


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


def decode_token_urlsafe(token: str) -> bytes:
    token = token.replace('-', '+').replace('_', '/')
    padding = 4 - (len(token) % 4)
    if padding != 4:
        token += '=' * padding
    return base64.urlsafe_b64decode(token)


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


async def send_reset_password_email_with_instructions(email: str, reset_url: str):
    try:
        await send_reset_password_email(email, reset_url)
    except SendEmailError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при отправке письма.")

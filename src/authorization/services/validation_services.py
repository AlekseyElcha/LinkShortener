from fastapi import status, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import secrets

from src.database.models import EmailValidation, UserModel
from src.exeptions import CreateEmailValidationLinkError


async def create_validation_link(login: str, session: AsyncSession):
    validate_token = secrets.token_urlsafe(32)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=1)
    # validate_email_url = f"http://localhost:8080/api/?validate_token={validate_token}" для работы с nginx
    validate_email_url = f"http://localhost:8000/?validate_token={validate_token}"
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
    exp = datetime.fromisoformat(expires_at)
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
from fastapi import status, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.database.models import UserModel, PasswordReset
from src.exeptions import UserNotFoundError
from src.services.email_service import send_reset_password_email_notification


async def get_user_id_by_login(login: str, session: AsyncSession):
    query = select(UserModel.id).where(login == UserModel.login)
    res = await session.execute(query)
    await session.close()
    if res:
        return res.scalar_one_or_none()
    raise UserNotFoundError


async def check_token_and_reset_password(token: str, new_password: str, session: AsyncSession):
    query = select(PasswordReset.expires_at).where(PasswordReset.token_hash == token)
    try:
        res = await session.execute(query)
        exp_at_str = str(res.scalar_one_or_none())
        exp_at_iso_formatted = exp_at_str.replace(' ', 'T', 1)
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Возникла ошибка при проверке токена")
    exp = datetime.fromisoformat(exp_at_iso_formatted)
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
            detail="Не удалось удалить PasswordReset-запрос из базы данных"
        )
    await send_reset_password_email_notification(user_email=login)
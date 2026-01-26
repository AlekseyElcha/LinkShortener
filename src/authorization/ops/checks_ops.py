from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime

from src.authorization.auth import config, hash_data
from src.authorization.services.auth_service import get_user_id_by_login
from src.authorization.services.token_service import decode_token
from src.database.models import ShortURL, PasswordReset, UserModel
from src.services.email_service import send_reset_password_email_notification


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


async def check_password_for_protected_slug(slug: str, password_for_slug: str, session: AsyncSession):
    password = hash_data(password_for_slug)
    query = select(ShortURL.id).where(slug == ShortURL.slug)
    try:
        res = await session.execute(query)
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Возникла ошибка.")
    if res:
        return True
    return False


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
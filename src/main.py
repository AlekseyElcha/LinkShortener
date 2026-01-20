import os

import pytz
from fastapi import FastAPI, Depends, Body, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Annotated
from tzlocal import get_localzone
import uvicorn
import logging
import sys

from src.database.schemas import SetExpirationTimeForSlug
from src.get_session import get_session
from src.authorization.auth import router as auth_router, create_link_with_token, \
    send_reset_password_email_with_instructions, check_token_and_reset_password, check_token_and_validate_user_email, \
    create_validation_link, hash_data
from src.authorization.auth import check_auth, check_auth_get_login
from src.services.email_sender import send_email_validation
from src.services.location import router as location_router
from src.services.location import get_location
from src.services.personal_client import router as personal_router
from src.database.models import Base
from src.database.database import engine, new_session
from src.exeptions import LongUrlNotFoundError, AddRedirectHistoryToDatabaseError, RedirectsHistoryNull, NoLocationData, \
    ShortURLToDeleteNotFound, CreateResetPasswordLinkError, CreateEmailValidationLinkError, UserIdByLoginNotFoundError, \
    SetSlugExpirationDateError, ShortLinkExpired, RemoveSlugExpirationDateError
from src.services.ops import generate_short_url, get_long_url_by_slug_from_database, add_redirect_to_history, \
    get_redirect_history_by_slug, delete_slug_from_database, set_expiration_date_for_slug, \
    remove_expiration_date_from_database
from src.services.time_service import convert_local_str_to_utc

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router=auth_router)
app.include_router(router=personal_router)
app.include_router(router=location_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/create_slug")
async def create_slug(
        long_url: Annotated[str, Body(embed=True)],
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request
):
    check_res = await check_auth(request, session)
    if check_res:
        user_id = check_res
    else:
        user_id = 0
    result = await generate_short_url(long_url=long_url, user_id=user_id, session=session)
    logger.debug(f"Успешно создан slug: {result}")
    return result


@app.get("/{slug}")
async def get_url_by_slug(
        slug: str,
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request
):
    user_login = await check_auth_get_login(request)
    logger.debug("Обращение к ручке get_url_by_slug (src.main.py)")
    try:
        long_url = await get_long_url_by_slug_from_database(slug, session)
        logger.debug(f"Длинная ссылка возвращена из БД: {long_url}.")
    except LongUrlNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мы не смогли найти запрашиваемую ссылку в нашей базе! Возможно, она была удалена её создателем."
        )
    except ShortLinkExpired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Ссылка недоступна, т.к. у неё истек срок действия. "
                   "Если Вы являетесь создателем этой ссылки - продлите её действие в личном кабинете нашего сервиса."
        )
    try:
        location_data = await get_location(request)
        location_city = location_data.get("city")
        location_country = location_data.get("country")
    except NoLocationData:
        location_city = "н/д"
        location_country = "н/д"
    if location_city is None:
        location_city = "н/д"
    if location_country is None:
        location_country = "н/д"
    if user_login:
        redirected_at = str(datetime.now(timezone.utc))[:19]
        try:
            await add_redirect_to_history(slug=slug,
                                          long_url=long_url,
                                          created_by=user_login,
                                          time=redirected_at,
                                          location_city=location_city,
                                          location_country=location_country,
                                          session=session)
            logger.info(f"Добавлен редирект в БД: slug={slug},"
                          f" long_url={long_url}, created_by={user_login}, time={redirected_at}")
        except AddRedirectHistoryToDatabaseError:
            logger.warn(
                f"Ошибка при записи перехода в историю: slug: {slug}, "
                f"long_url: {long_url}, created_by: {user_login}, time: {redirected_at} "
                f"location_country: {location_country}, location_city: {location_city}"
            )
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)


@app.get("/slug_redirect_history/{slug}")
async def get_slug_redirect_history(slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        user_timezone = str(get_localzone())
    except:
        user_timezone = "UTC"
    logger.debug(f"Получен часовой пояс пользователя: {user_timezone}.")
    try:
        data = await get_redirect_history_by_slug(slug=slug, user_timezone=user_timezone, session=session)
        logger.debug(f"Успешное получение истории редиректов по slug: {slug}.")
    except RedirectsHistoryNull:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="История переходов пуста.")
    return data


@app.put("/set_expiration_date/{slug}")
async def set_expiration_date(slug: str,
                              user_tz: Annotated[str, Query()],
                              exp_time: SetExpirationTimeForSlug,
                              session: Annotated[AsyncSession, Depends(get_session)]):
    expire_time = datetime(
        year=exp_time.year, month=exp_time.month, day=exp_time.day, hour=exp_time.hour, minute=exp_time.minute
    )
    us_tz = pytz.timezone(user_tz)
    new_expiration_time_aware = expire_time.astimezone(us_tz)
    expire_time_naive = new_expiration_time_aware.astimezone(pytz.UTC).replace(tzinfo=None)
    datetime_now = datetime.now(us_tz)
    if new_expiration_time_aware < datetime_now:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Время истечения ссылки не может быть в прошлом.",
        )
    try:
        res = await set_expiration_date_for_slug(slug=slug, exp_time=expire_time_naive, session=session)
        return res
    except SetSlugExpirationDateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при установке даты истечения ссылки."
        )


@app.put("/remove_expiration_date/{slug}")
async def remove_expiration_date(slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        res = await remove_expiration_date_from_database(slug=slug, session=session)
        return res
    except RemoveSlugExpirationDateError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить срок истечения ссылки."
        )


@app.delete("/delete_slug/{slug}")
async def delete_slug(slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        res = await delete_slug_from_database(slug=slug, session=session)
        logger.debug(f"Slug: {slug} и история редиректов по нему удалены.")
    except ShortURLToDeleteNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ссылка для удаления не найдена.")
    return res


@app.post("/reset_password")
async def create_reset_password_link(login: Annotated[str, Body(embed=True)], session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        reset_url = await create_link_with_token(login=login, session=session)
    except UserIdByLoginNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail = "Не удалось найти аккаунт с данным email."
        )
    except CreateResetPasswordLinkError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Ошибка при создании ссылки с токеном и добавлении в базу."
        )
    try:
        await send_reset_password_email_with_instructions(email=login, reset_url=reset_url)
    except:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить письмо."
        )
    return {"result": "success"}


@app.put("/reset_password/{token}")
async def reset_password(
        token: str,
        new_password: str,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        await check_token_and_reset_password(token=token, new_password=hash_data(new_password), session=session)
    except:
        raise
    return {"message": "Пароль успешно обновлён!"}


@app.post("/validate_email")
async def create_validate_email_link(login: Annotated[str, Body(embed=True)],
                                     session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        validate_url = await create_validation_link(login=login, session=session)
    except CreateEmailValidationLinkError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Ошибка при создании ссылки с токеном и добавления в базу"
        )
    try:
        await send_email_validation(user_email=login, validate_url=validate_url)
    except:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить письмо"
        )
    return validate_url


@app.put("/validate_email/{token}")
async def validate_email(
        token: str,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        await check_token_and_validate_user_email(token, session)
    except:
        raise
    return {"message": "Пароль успешно обновлён!"}


app.mount("/", StaticFiles(directory="./public", html=True), name="public")

if __name__ == "__main__":
    logger.info("Сервер uvicorn запущен")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
from fastapi import FastAPI, Depends, Body, HTTPException, status, Request
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

from src.get_session import get_session
from src.authorization.auth import router as auth_router
from src.authorization.auth import check_auth, check_auth_get_login
from src.services.location import router as location_router
from src.services.location import get_location
from src.services.personal_client import router as personal_router
from src.database.models import Base
from src.database.database import engine, new_session
from src.exeptions import LongUrlNotFoundError, AddRedirectHistoryToDatabaseError, RedirectsHistoryNull, NoLocationData, \
    ShortURLToDeleteNotFound
from src.services.ops import generate_short_url, get_long_url_by_slug_from_database, add_redirect_to_history, \
    get_redirect_history_by_slug, delete_slug_from_database


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
    return result

@app.get("/{slug}")
async def get_url_by_slug(
        slug: str,
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request
):
    user_login = await check_auth_get_login(request)
    logging.debug("Обращение к ручке get_url_by_slug (src.main.py)")
    try:
        long_url = await get_long_url_by_slug_from_database(slug, session)
        logging.debug(f"Длинная ссылка возвращена из БД: {long_url}")
    except LongUrlNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мы не смогли найти запрашиваемую ссылку в нашей базе! Возможно, она была удалена её создателем."
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
            logging.debug(f"Добавлен редирект в БД: slug={slug},"
                          f" long_url={long_url}, created_by={user_login}, time={redirected_at}")
        except AddRedirectHistoryToDatabaseError:
            logging.warn(
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
    try:
        data = await get_redirect_history_by_slug(slug=slug, user_timezone=user_timezone, session=session)
    except RedirectsHistoryNull:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="История переходов пуста")
    return data


@app.delete("/delete_slug/{slug}")
async def delete_slug(slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        await delete_slug_from_database(slug=slug, session=session)
    except ShortURLToDeleteNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ссылка для удаления не найдена.")



app.mount("/", StaticFiles(directory="./public", html=True), name="public")

if __name__ == "__main__":
    logging.info("Сервер uvicorn запущен")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
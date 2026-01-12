import uvicorn
from fastapi import FastAPI, Depends, Body, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.get_session import get_session
from src.authorization.auth import router as auth_router
from src.authorization.auth import check_auth
from src.services.personal_client import router as personal_router
from src.database.models import Base
from src.database.database import engine, new_session
from src.exeptions import LongUrlNotFoundError
from src.services.ops import generate_short_url, get_long_url_by_slug_from_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router=auth_router)
app.include_router(router=personal_router)

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
    slug = await generate_short_url(long_url=long_url, user_id=user_id, session=session)
    return {"slug": slug}


@app.get("/{slug}")
async def get_url_by_slug(
        slug: str,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        long_url = await get_long_url_by_slug_from_database(slug, session)
    except LongUrlNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не существует")
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)

app.mount("/", StaticFiles(directory="./public", html=True), name="public")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
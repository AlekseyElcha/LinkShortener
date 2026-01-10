from fastapi import FastAPI, Depends, Body, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated


from src.database.models import Base
from src.database.database import engine, new_session
from src.exeptions import LongUrlNotFoundError
from src.services.ops import generate_short_url, get_long_url_by_slug_from_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


async def get_session():
    async with new_session() as session:
        yield session


app = FastAPI(lifespan=lifespan)

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
        session: Annotated[AsyncSession, Depends(get_session)]
):
    slug = await generate_short_url(long_url=long_url, session=session)
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

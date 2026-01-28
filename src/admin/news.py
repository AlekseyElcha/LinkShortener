from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Body
from fastapi.responses import HTMLResponse
from typing import Annotated
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.services.time_service import convert_utc_string_to_local
from src.get_session import get_session
from src.database.models import ServiceNews


router = APIRouter(prefix="/admin/news")


@router.post("/create_news")
async def create_html_page(
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
        content: str = Body(
        ...,
                media_type="text/html",
                example="""<head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>...</title>
</head>"
                """
    ),
):

        news = ServiceNews(
                created_at=datetime.utcnow(),
                content=content
        )
        
        session.add(news)
        try:
                await session.commit()
        except:
                await session.rollback()
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка добавления новости.")

        return HTMLResponse(content)


@router.get("/get_all_news")
async def get_all_news(session: Annotated[AsyncSession, Depends(get_session)], user_tz: Annotated[str, Query()]):
        query = select(ServiceNews)
        try:
                res = await session.execute(query)
                await session.close()
        except:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка получения новостей.")
        news = res.scalars().all()
        if not news:
                return {
                        "message": "Новостей пока нет."
                }
        
        for i in range(len(news)):
                news[i].created_at = convert_utc_string_to_local(str(news[i].created_at), user_tz)
        
        
        return news


@router.patch("/patch_news_by_id")
async def patch_news_by_id(
                           request: Request,
                           session: Annotated[AsyncSession, Depends(get_session)],
                           id: int,
                           new_content: str = Body(
        ...,
                media_type="text/html")
):
        query = update(ServiceNews).where(ServiceNews.id == id).values(content=new_content)
        
        try:
                await session.execute(query)
                await session.commit()
        except:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось изменить новость.")
        
        return {
                "success": True
        }


@router.delete("/delete_news/{id}")
async def gelete_news_by_id(id: int, session: Annotated[AsyncSession, Depends(get_session)]):
        query = delete(ServiceNews).where(ServiceNews.id == id)
        try:
                await session.execute(query)
                await session.commit()
        except:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось удалить новость.")
        
        return {
                "success": True
        }
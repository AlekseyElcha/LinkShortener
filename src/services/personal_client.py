import json

from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.get_session import get_session
from src.authorization.auth import check_auth_account, check_auth
from src.database.models import ShortURL
from src.services.time_service import convert_utc_string_to_local

router = APIRouter(prefix="/account")

@router.get("/get_created_urls/{user_id}")
async def get_short_urls(request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    user_id = await check_auth_account(request=request, session=session)
    query = select(ShortURL).where(user_id == ShortURL.user_id)
    res = await session.execute(query)
    data = res.scalars().all()
    return data


@router.get("/get_created_urls")
async def get_short_urls(request: Request, user_tz: Annotated[str, Query()], session: Annotated[AsyncSession, Depends(get_session)]):
    user_id = await check_auth_account(request=request, session=session)
    query = select(ShortURL).where(user_id == ShortURL.user_id)
    try:
        res = await session.execute(query)
        await session.close()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось получить историю созданных ссылок.")
    data = res.scalars().all()
    for i in range(len(data)):
        if data[i].expiration_date:
            data[i].expiration_date = convert_utc_string_to_local(str(data[i].expiration_date), user_tz)
    return data
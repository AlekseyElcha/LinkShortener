from fastapi import APIRouter, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.get_session import get_session
from src.authorization.auth import check_auth_account, check_auth
from src.database.models import ShortURL

router = APIRouter(prefix="/account")

@router.get("/get_created_urls/{user_id}")
async def get_short_urls(request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    user_id = await check_auth_account(request=request, session=session)
    query = select(ShortURL).where(user_id == ShortURL.user_id)
    res = await session.execute(query)
    data = res.scalars().all()
    return data

@router.get("/get_created_urls")
async def get_short_urls(request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    user_id = await check_auth_account(request=request, session=session)
    print(user_id)
    query = select(ShortURL).where(user_id == ShortURL.user_id)
    res = await session.execute(query)
    data = res.scalars().all()
    return data
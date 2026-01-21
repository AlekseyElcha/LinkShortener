import json

from fastapi import APIRouter, Request, Depends, HTTPException, status, Query, Body
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.get_session import get_session
from src.authorization.auth import check_auth_account, check_auth, security, check_user_auth
from src.database.models import ShortURL
from src.services.time_service import convert_utc_string_to_local

router = APIRouter(prefix="/account")

@router.get("/get_created_urls/{user_id}", dependencies=[Depends(security.access_token_required)])
async def get_short_urls(request: Request, session: Annotated[AsyncSession, Depends(get_session)]):
    user_id = await check_auth_account(request=request, session=session)
    query = select(ShortURL).where(user_id == ShortURL.user_id)
    res = await session.execute(query)
    data = res.scalars().all()
    return data


@router.get("/get_created_urls", dependencies=[Depends(security.access_token_required)])
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


@router.put("/customize_slug/{slug}", dependencies=[Depends(security.access_token_required)])
async def customize_slug(slug: str,
                         new_slug: Annotated[str, Body(embed=True)],
                         session: Annotated[AsyncSession, Depends(get_session)],
                         request: Request
    ):
    query = select(ShortURL).where(slug == ShortURL.slug)
    try:
        res = await session.execute(query)
        old_slug_data = res.scalars().one_or_none()
        if old_slug_data:
            new_slug = ShortURL(
                id=old_slug_data.id,
                slug=old_slug_data.slug,
                long_url=old_slug_data.long_url,
                expiration_date=old_slug_data.expiration_date,
                user_id=old_slug_data.user_id,
                hop_counts=old_slug_data.hop_counts,
            )
        check_user = check_user_auth(request=request, session=session, id_to_check=new_slug.user_id)
        if not check_user:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Нет доступа.")
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось обновить ссылку.")

    query = update(ShortURL).where(ShortURL.slug == slug).values(slug=new_slug)
    try:
        await session.execute(query)
        await session.commit()
        await session.close()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Не удалось установить кастомную короткую ссылку.")
    return {"success": True}


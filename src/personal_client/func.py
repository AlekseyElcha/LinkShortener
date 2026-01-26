from fastapi import APIRouter, Request, Depends, HTTPException, status, Query, Body
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.authorization.auth import security, hash_data
from src.authorization.ops.checks_ops import check_auth_account, check_user_auth
from src.get_session import get_session
from src.database.models import ShortURL
from src.ops.auxiliary.auxiliary_ops import get_user_id_by_slug
from src.services.time_service import convert_utc_string_to_local
from src.services.url_slug_basic_validation_service import validate_custom_slug

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
    custom_slug_is_valid = validate_custom_slug(new_slug)
    user_id_required = await get_user_id_by_slug(slug=slug, session=session)
    if user_id_required is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Не удается найти пользователя по ссылке.")
    user_is_valid = await check_user_auth(request=request, session=session, id_to_check=user_id_required)
    if not user_is_valid:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Нет доступа.")
    if not custom_slug_is_valid:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Ссылка не должна содержать иных симоволов, кроме русских, латинских букв, цифр, символов  «-» и «_»"
        )
    query = select(ShortURL).where(slug == ShortURL.slug)
    try:
        res = await session.execute(query)
        old_slug_data = res.scalars().one_or_none()
        if old_slug_data is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Соответствие не найдено."
            )
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при поиске соответствия в базе данных.")
    if old_slug_data:
        new_custom_slug = ShortURL(
            slug=new_slug,
            long_url=old_slug_data.long_url,
            expiration_date=old_slug_data.expiration_date,
            user_id=old_slug_data.user_id,
            hop_counts=old_slug_data.hop_counts,
            is_private=True,
        )
        try:
            session.add(new_custom_slug)
            await session.commit()
            await session.close()
        except:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Непредвиденная ошибка.")

    return {"success": True}

@router.put("/set_password_for_slug/{slug}", dependencies=[Depends(security.access_token_required)])
async def set_password_on_link(slug: str,
                               password_for_slug: Annotated[str, Body(embed=True)],
                               session: Annotated[AsyncSession, Depends(get_session)],
                               request: Request
    ):
    user_id_required = await get_user_id_by_slug(slug=slug, session=session)
    if user_id_required is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Не удается найти пользователя по ссылке.")
    user_is_valid = await check_user_auth(request=request, session=session, id_to_check=user_id_required)
    if not user_is_valid:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Нет доступа.")

    query = update(ShortURL).where(ShortURL.slug == slug).values(password=hash_data(password_for_slug), is_private=True)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось установить пароль на ссылку.")
    return {"success": True}


@router.put("/remove_password_for_slug/{slug}", dependencies=[Depends(security.access_token_required)])
async def remove_password_for_slug(slug: str,
                                   session: Annotated[AsyncSession, Depends(get_session)],
                                   request: Request):
    user_id_required = await get_user_id_by_slug(slug=slug, session=session)
    if user_id_required is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Не удается найти пользователя по ссылке.")
    user_is_valid = await check_user_auth(request=request, session=session, id_to_check=user_id_required)
    if not user_is_valid:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Нет доступа.")

    query = update(ShortURL).where(ShortURL.slug == slug).values(password=None)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось установить пароль на ссылку.")
    return {"success": True}


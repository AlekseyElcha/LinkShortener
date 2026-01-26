from fastapi import status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.database.models import ShortURL
from src.exeptions import SlugAlreadyExistsError, ShortLinkExpired, ShortLinkIsProtected, LongUrlNotFoundError, \
    UserIdBySlugNotFoundError


async def add_slug_to_database(slug: str, long_url: str, user_id: int, session: AsyncSession):
    if user_id > 0:
        is_private = True
    else:
        is_private = False
    new_slug = ShortURL(
        slug=slug,
        long_url=long_url,
        user_id=user_id,
        is_private=is_private
    )
    session.add(new_slug)
    try:
        await session.commit()
    except:
        raise SlugAlreadyExistsError


async def get_long_url_by_slug_from_database_check(slug: str, session: AsyncSession):
    query = select(ShortURL).where(slug == ShortURL.slug)
    res = await session.execute(query)
    result = res.scalar_one_or_none()
    if result:
        exp = result.expiration_date
        now = datetime.utcnow()

        if exp is not None and now > exp:
            raise ShortLinkExpired
        if result.password is not None:
            raise ShortLinkIsProtected
        result.hop_counts += 1
        await session.commit()
        return result.long_url
    else:
        raise LongUrlNotFoundError


async def get_long_url_by_slug_from_database(slug: str, session: AsyncSession):
    query = select(ShortURL).where(slug == ShortURL.slug)
    res = await session.execute(query)
    result = res.scalar_one_or_none()
    if result:
        result.hop_counts += 1
        await session.commit()
        return result.long_url
    else:
        raise LongUrlNotFoundError


async def get_slug_password_from_db(slug: str, session: AsyncSession):
    query = select(ShortURL).where(ShortURL.slug == slug)
    try:
        res = await session.execute(query)
        await session.commit()
        result = res.scalar_one_or_none()
        return result.password
    except:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Произошла ошибка.")


async def check_slug_already_exists(long_url: str, user_id: int, session: AsyncSession):
    if user_id == 0:
        query = select(ShortURL).where(ShortURL.long_url == long_url).where(ShortURL.is_private != True)
        res = await session.execute(query)
        result = res.first()
        if result:
            return result[0].slug
        return None
    else:
        return None


async def get_user_id_by_slug(slug: str, session: AsyncSession):
    query = select(ShortURL).where(ShortURL.slug == slug)
    try:
        res = await session.execute(query)
        await session.commit()
        data = res.scalar_one_or_none()
        if not data:
            return None
        return data.user_id
    except:
        raise UserIdBySlugNotFoundError
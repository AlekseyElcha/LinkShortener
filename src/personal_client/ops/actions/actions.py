from datetime import datetime
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ShortURL, RedirectsHistory
from src.exeptions import SetSlugExpirationDateError, RemoveSlugExpirationDateError, \
    ShortURLToDeleteNotFoundHistoryClear, ShortURLToDeleteNotFound


async def set_expiration_date_for_slug(slug: str, exp_time: datetime, session: AsyncSession):
    query = update(ShortURL).where(ShortURL.slug == slug).values(expiration_date=exp_time, is_private=True)
    try:
        await session.execute(query)
        await session.commit()
        await session.close()
    except:
        raise SetSlugExpirationDateError
    return {"success": True}

async def remove_expiration_date_from_database(slug: str, session: AsyncSession):
    query = update(ShortURL).where(ShortURL.slug == slug).values(expiration_date=None)
    try:
        await session.execute(query)
        await session.commit()
        await session.close()
    except:
        raise RemoveSlugExpirationDateError
    return {"success": True}

async def delete_slug_from_database(slug: str, session: AsyncSession):
    query = delete(ShortURL).where(ShortURL.slug == slug)
    try:
        await session.execute(query)
        await session.commit()
        await session.close()
        try:
            await delete_slug_history(slug, session)
        except ShortURLToDeleteNotFoundHistoryClear:
            raise ShortURLToDeleteNotFound
    except:
        raise ShortURLToDeleteNotFound
    return {"success": True}


async def delete_slug_history(slug: str, session: AsyncSession):
    query = delete(RedirectsHistory).where(RedirectsHistory.slug == slug)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise ShortURLToDeleteNotFoundHistoryClear

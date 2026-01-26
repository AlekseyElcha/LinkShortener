from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RedirectsHistory
from src.exeptions import RedirectsHistoryNull
from src.services.time_service import convert_utc_string_to_local


async def get_redirect_history_for_slug(slug: str, session: AsyncSession):
    query = select(RedirectsHistory).where(slug == RedirectsHistory.slug)
    res = await session.execute(query)
    data = res.scalars().all()
    if not data:
        raise RedirectsHistoryNull
    return data

async def get_redirect_history_by_slug(slug: str, user_timezone: str, session: AsyncSession):
    query = select(RedirectsHistory).where(slug == RedirectsHistory.slug)
    res = await session.execute(query)
    data = res.scalars().all()
    if not data:
        raise RedirectsHistoryNull
    for item in data:
        item.time = item.time = convert_utc_string_to_local(str(item.time), user_timezone)
    return data

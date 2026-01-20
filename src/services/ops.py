from datetime import datetime

from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database.models import ShortURL, RedirectsHistory
from src.exeptions import SlugAlreadyExistsError, LongUrlNotFoundError, RedirectsHistoryNull, \
    AddRedirectHistoryToDatabaseError, ShortURLToDeleteNotFound, ShortURLToDeleteNotFoundHistoryClear, \
    SetSlugExpirationDateError, ShortLinkExpired, RemoveSlugExpirationDateError
from src.services.slug_service import generate_random_short_url
from src.services.time_service import convert_utc_string_to_local


async def add_slug_to_database(slug: str, long_url: str, user_id: int, session: AsyncSession):
    new_slug = ShortURL(
        slug=slug,
        long_url=long_url,
        user_id=user_id,
    )
    session.add(new_slug)
    try:
        await session.commit()
    except IntegrityError:
        raise SlugAlreadyExistsError


async def get_long_url_by_slug_from_database(slug: str, session: AsyncSession):
    query = select(ShortURL).where(slug == ShortURL.slug)
    res = await session.execute(query)
    result = res.scalar_one_or_none()
    if result:
        exp = result.expiration_date
        now = datetime.utcnow()
        
        # Проверяем истечение только если дата установлена
        if exp is not None and now > exp:
            raise ShortLinkExpired
            
        # Если ссылка не истекла, увеличиваем счетчик и возвращаем URL
        result.hop_counts += 1
        await session.commit()
        return result.long_url
    else:
        raise LongUrlNotFoundError



async def check_slug_already_exists(long_url: str, session: AsyncSession):
    query = select(ShortURL).where(ShortURL.long_url == long_url)
    res = await session.execute(query)
    result = res.first()
    if result:
        return result[0].slug
    return None


async def generate_short_url(
        long_url: str,
        user_id: int,
        session: AsyncSession
):
    async def _generate_new_slug_and_add_to_db():
        slug = generate_random_short_url()
        existing_slug = await check_slug_already_exists(long_url, session=session)
        if existing_slug:
            return {
                "slug": existing_slug,
                "created_before": True
            }

        await add_slug_to_database(
            user_id=user_id, slug=slug, long_url=long_url, session=session,
        )

        return {
            "slug": slug,
            "created_before": False
        }

    for attempt in range(5):
        try:
            result = await _generate_new_slug_and_add_to_db()
            return result
        except SlugAlreadyExistsError as ex:
            if attempt == 4:
                raise SlugAlreadyExistsError from ex

    raise Exception("Не удалось создать короткую ссылку")


async def get_url_by_slug(slug: str, session: AsyncSession):
    long_url = await get_long_url_by_slug_from_database(slug, session)
    if not long_url:
        raise LongUrlNotFoundError
    return long_url


async def get_redirect_history_for_slug(slug: str, session: AsyncSession):
    query = select(RedirectsHistory).where(slug == RedirectsHistory.slug)
    res = await session.execute(query)
    data = res.scalars().all()
    if not data:
        raise RedirectsHistoryNull
    return data


async def add_redirect_to_history(slug: str,
                                  created_by: str,
                                  long_url: str,
                                  time: str,
                                  location_city: str,
                                  location_country: str,
                                  session: AsyncSession):
    new_redirect = RedirectsHistory(
        slug=slug,
        created_by=created_by,
        long_url=long_url,
        location_country=location_country,
        location_city=location_city,
        time=time,
    )
    session.add(new_redirect)
    try:
        await session.commit()
    except IntegrityError:
        raise AddRedirectHistoryToDatabaseError


async def get_redirect_history_by_slug(slug: str, user_timezone: str, session: AsyncSession):
    query = select(RedirectsHistory).where(slug == RedirectsHistory.slug)
    res = await session.execute(query)
    data = res.scalars().all()
    if not data:
        raise RedirectsHistoryNull
    for item in data:
        item.time = item.time = convert_utc_string_to_local(str(item.time), user_timezone)
    return data


async def delete_slug_history(slug: str, session: AsyncSession):
    query = delete(RedirectsHistory).where(RedirectsHistory.slug == slug)
    try:
        await session.execute(query)
        await session.commit()
    except:
        raise ShortURLToDeleteNotFoundHistoryClear


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


async def set_expiration_date_for_slug(slug: str, exp_time: datetime, session: AsyncSession):
    query = update(ShortURL).where(ShortURL.slug == slug).values(expiration_date=exp_time)
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


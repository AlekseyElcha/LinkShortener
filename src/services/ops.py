from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ShortURL
from src.exeptions import SlugAlreadyExistsError, LongUrlNotFoundError
from src.services.slug_service import generate_random_short_url


async def add_slug_to_database(slug: str, long_url: str, session: AsyncSession):
    new_slug = ShortURL(
        slug=slug,
        long_url=long_url
    )
    session.add(new_slug)
    try:
        await session.commit()
    except IntegrityError:
        raise SlugAlreadyExistsError

async def get_long_url_by_slug_from_database(slug: str, session: AsyncSession):
    query = select(ShortURL).where(ShortURL.slug == slug)
    res = await session.execute(query)
    result = res.scalar_one_or_none()
    if result:
        return result.long_url
    else:
        raise LongUrlNotFoundError

async def generate_short_url(
        long_url: str,
        session: AsyncSession
):
    async def _generate_new_slug_and_add_to_db():
        slug = generate_random_short_url()
        await add_slug_to_database(
            slug=slug, long_url=long_url, session=session,
        )
        return slug

    for attemts in range(5):
        try:
            slug = await _generate_new_slug_and_add_to_db()
            return slug
        except SlugAlreadyExistsError as ex:
            if attemts == 4:
                raise SlugAlreadyExistsError from ex
    return slug

async def get_url_by_slug(slug: str, session: AsyncSession):
    long_url = await get_long_url_by_slug_from_database(slug, session)
    if not long_url:
        raise LongUrlNotFoundError
    return long_url

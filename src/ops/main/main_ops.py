from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import RedirectsHistory
from src.exeptions import SlugAlreadyExistsError, LongUrlNotFoundError, AddRedirectHistoryToDatabaseError
from src.ops.auxiliary.auxiliary_ops import check_slug_already_exists, add_slug_to_database, \
    get_long_url_by_slug_from_database
from src.services.random_slug_service import generate_random_short_url


async def generate_short_url(
        long_url: str,
        user_id: int,
        session: AsyncSession
):
    async def _generate_new_slug_and_add_to_db():
        slug = generate_random_short_url()
        existing_slug = await check_slug_already_exists(long_url=long_url, user_id=user_id, session=session)
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
    except:
        raise AddRedirectHistoryToDatabaseError


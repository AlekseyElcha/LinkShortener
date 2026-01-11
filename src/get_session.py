from src.database.database import new_session


async def get_session():
    async with new_session() as session:
        yield session
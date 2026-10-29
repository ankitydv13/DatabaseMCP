import asyncpg

from databasemcp.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


async def get_db_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )

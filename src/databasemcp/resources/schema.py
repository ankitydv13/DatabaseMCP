import logging

from fastmcp import FastMCP

from databasemcp.database import get_db_connection

logger = logging.getLogger(__name__)


def register_schema_resource(mcp: FastMCP) -> None:
    @mcp.resource("postgres://schema")
    async def get_database_schema() -> str:
        """Return the table and column names and data types in the public schema."""
        logger.info("get_database_schema called")
        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """

        conn = await get_db_connection()
        try:
            rows = await conn.fetch(query)
            logger.info("Schema rows => %s", rows)
            schema_text = "Database Schema:\n"
            current_table = ""
            for row in rows:
                if row["table_name"] != current_table:
                    current_table = row["table_name"]
                    schema_text += f"\nTable: {current_table}\n"
                schema_text += f" - {row['column_name']} ({row['data_type']})\n"

            logger.info("%s", schema_text)
            return schema_text
        finally:
            await conn.close()

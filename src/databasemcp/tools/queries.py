import logging
from datetime import date, datetime, time

from fastmcp import Context, FastMCP
from mcp.types import (
    ElicitRequest,
    ElicitRequestFormParams,
    InputRequiredResult,
)

from databasemcp.database import get_db_connection

logger = logging.getLogger(__name__)


def normalize_sql_parameter(value):
    """Convert ISO date/time strings into objects asyncpg can bind to temporal columns."""
    if not isinstance(value, str):
        return value

    raw_value = value.strip()
    if not raw_value:
        return value

    for parser in (date.fromisoformat, datetime.fromisoformat, time.fromisoformat):
        try:
            return parser(raw_value)
        except ValueError:
            continue

    return value


def ask_user(query: str, message: str) -> InputRequiredResult:
    params = ElicitRequestFormParams(
        message=f"{message} \n\n{query} ",
        requested_schema={
            "type": "object",
            "properties": {
                "confirmed": {
                    "type": "boolean",
                    "title": "Confirm execution",
                }
            },
            "required": ["confirmed"],
        },
    )

    elicitation = ElicitRequest(
        method="elicitation/create",
        params=params,
    )

    return InputRequiredResult(
        result_type="input_required",
        input_requests={"confirm_query": elicitation},
    )


def register_query_tools(mcp: FastMCP) -> None:
    @mcp.tool
    async def select_query(query: str, params: list, ctx: Context):
        """
        Executes a read-only PostgreSQL SELECT query. Use $1, $2, etc. as
        placeholders for values, and provide matching values in params in
        the same order. Never interpolate values into SQL.

        Args:
            query: Parameterized read-only PostgreSQL SELECT query.
            params: Ordered values matching the query placeholders.
            ctx: FastMCP Context object injected by the framework.
        """
        logger.info("select_query called")
        responses = ctx.input_responses

        if responses is None or "confirm_query" not in responses:
            return ask_user(query, "Do you want to execute this sql ?")

        response = responses["confirm_query"]
        if response.action != "accept":
            return "Query is Cancel by User"

        content = response.content or {}
        if content.get("confirmed", False) is not True:
            logger.info("User Does not confirmed query")
            return "Query Cancel the query"

        conn = None
        try:
            conn = await get_db_connection()
            normalized_params = [normalize_sql_parameter(param) for param in params]
            async with conn.transaction(readonly=True):
                rows = await conn.fetch(query, *normalized_params)
                logger.info("Rows in the tables => %s", rows)
                if not rows:
                    return "No rows found "
                result = [dict(row) for row in rows]
                return str(result)
        except Exception as e:
            return f"There is problem with database {e}"
        finally:
            if conn is not None:
                await conn.close()

    @mcp.tool
    async def insert_query(query: str, params: list, ctx: Context):
        """
        Executes a PostgreSQL INSERT query. Use $1, $2, etc. as placeholders
        for values, and provide the matching values in params in the same
        order. For date/time values in params, use ISO 8601 strings (for
        example, "2021-03-15" or "2021-03-15T10:30:00"). Do not interpolate
        external or user-provided values into the SQL query.

        Args:
            query: Parameterized PostgreSQL INSERT query.
            params: Ordered values matching the query placeholders.
            ctx: FastMCP Context object injected by the framework.
        """
        logger.info(f"query {query} params {params}")
        responses = ctx.input_responses
        if responses is None or "confirm_query" not in responses:
            return ask_user(query, "Do you want to execute this sql ?")

        response = responses["confirm_query"]
        if response.action != "accept":
            return "Query Delined By User"

        content = response.content or {}
        if content.get("confirmed", False) is not True:
            return "Query execution deny by User"

        conn = None
        try:
            conn = await get_db_connection()
            normalized_params = [normalize_sql_parameter(param) for param in params]
            rows = await conn.execute(query, *normalized_params)
            logger.info("Rows in the tables => %s", rows)
            if not rows:
                return "No rows added"
            row = rows.split(" ")[-1]
            return f"No of rows Inserted :{row}"
        except Exception as e:
            return f"There is problem with database {e}"
        finally:
            if conn is not None:
                await conn.close()

    @mcp.tool
    async def update_query(query:str,params:list,ctx:Context):
        """
        Executes a PostgreSQL UPDATE query after user confirmation. Use $1,
        $2, etc. as placeholders for values, and provide the matching values
        in params in the same order. Include an appropriate WHERE clause to
        limit which rows are updated. For date/time values in params, use
        ISO 8601 strings (for example, "2021-03-15" or
        "2021-03-15T10:30:00"). Never interpolate external or user-provided
        values into the SQL query.

        Args:
            query: Parameterized PostgreSQL UPDATE query.
            params: Ordered values matching the query placeholders.
            ctx: FastMCP Context object injected by the framework.
        """

        logger.info("update_query called")
        responses = ctx.input_responses

        if responses is None or "confirm_query" not in responses:
            return ask_user(query, "Do you want to execute this update query?")

        response = responses["confirm_query"]
        if response.action != "accept":
            return "Query execution deny by User"

        content = response.content or {}
        if content.get("confirmed", False) is not True:
            return "Query execution deny by User"

        conn = None
        try:
            conn = await get_db_connection()
            normalized_params = [normalize_sql_parameter(param) for param in params]
            result = await conn.execute(query, *normalized_params)
            logger.info("Update result => %s", result)
            if not result:
                return "No rows updated"
            row_count = result.split(" ")[-1]
            return f"No of rows Updated :{row_count}"
        except Exception as e:
            return f"There is problem with database {e}"
        finally:
            if conn is not None:
                await conn.close()

    @mcp.tool
    async def delete_query(query: str, params: list, ctx: Context):
        """
        Executes a PostgreSQL DELETE query after user confirmation. Use $1,
        $2, etc. as placeholders for values, and provide the matching values
        in params in the same order. Include an appropriate WHERE clause to
        limit which rows are deleted; without one, every row in the table
        may be deleted. For date/time values in params, use ISO 8601 strings
        (for example, "2021-03-15" or "2021-03-15T10:30:00"). Never
        interpolate external or user-provided values into the SQL query.

        Args:
            query: Parameterized PostgreSQL DELETE query.
            params: Ordered values matching the query placeholders.
            ctx: FastMCP Context object injected by the framework.
        """
        logger.info("delete_query called")
        responses = ctx.input_responses

        if responses is None or "confirm_query" not in responses:
            return ask_user(query, "Do you want to execute this delete query?")

        response = responses["confirm_query"]
        if response.action != "accept":
            return "Query execution deny by User"

        content = response.content or {}
        if content.get("confirmed", False) is not True:
            return "Query execution deny by User"

        conn = None
        try:
            conn = await get_db_connection()
            normalized_params = [normalize_sql_parameter(param) for param in params]
            result = await conn.execute(query, *normalized_params)
            logger.info("Delete result => %s", result)
            if not result:
                return "No rows deleted"
            row_count = result.split(" ")[-1]
            return f"No of rows Deleted :{row_count}"
        except Exception as e:
            return f"There is problem with database {e}"
        finally:
            if conn is not None:
                await conn.close()




    

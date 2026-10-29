import logging

from fastmcp import FastMCP

from databasemcp.resources.schema import register_schema_resource
from databasemcp.tools.queries import register_query_tools
from fastmcp.server.auth.providers.jwt import JWTVerifier
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


auth = JWTVerifier(
    jwks_uri="https://your-auth-system.com/.well-known/jwks.json",
    issuer="https://your-auth-system.com", 
    audience="database_mcp"
)

mcp = FastMCP("database_mcp")
register_query_tools(mcp)
register_schema_resource(mcp)


def main() -> None:
    logger.info("Starting database MCP server")
    mcp.run(transport="http", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

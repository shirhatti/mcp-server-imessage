from mcp.server.fastmcp import FastMCP

from .iMessage import Message, iMessageServer

# Create an MCP server
server = iMessageServer()
mcp = FastMCP(server.serverName)


@mcp.tool()
def read_iMessage(n: int) -> list[Message]:
    """Read last n iMessage messages"""
    return server.read_messages(n)

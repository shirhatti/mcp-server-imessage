import asyncio
import platform
from contextlib import suppress

from mcp import stdio_server
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel import Server
from mcp.types import TextContent, Tool

from .AddressBook import AddressBook
from .iMessage import iMessageServer

address_book = None
if platform.system() == "Darwin":
    with suppress(Exception):
        address_book = AddressBook()

server = iMessageServer(address_book=address_book)
mcp = FastMCP(server.serverName)

app = Server("iMessage")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="inbox",
            description="Lists the messages in the inbox",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of messages to return", "default": 100}
                },
            },
        ),
        Tool(
            name="sent",
            description="Lists the messages in the sent folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of messages to return", "default": 100}
                },
            },
        ),
    ]


@app.call_tool()
async def fetch_tool(name: str, arguments: dict) -> list[TextContent]:
    messages = []
    if name == "inbox":
        limit = arguments.get("limit", 100)
        messages = server.get_received_messages(limit=limit)
    elif name == "sent":
        limit = arguments.get("limit", 100)
        messages = server.get_sent_messages(limit=limit)
    return [TextContent(type="text", text=msg.__str__()) for msg in messages]


async def main() -> None:
    # Start server
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

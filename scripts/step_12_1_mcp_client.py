import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


'''
StdioServerParameters
        ↓
describes how to start server

stdio_client(...)
        ↓
starts server process
        ↓
creates communication streams

ClientSession(...)
        ↓
creates MCP session

session.initialize()
        ↓
MCP handshake

session.list_tools()
        ↓
server returns exposed tools
'''


SERVER_SCRIPT = "scripts/step_11_1_mcp_server.py"

async def run():

    server_params = StdioServerParameters(
        command="/Users/abhishekkumarmandal/Documents/python/local-rag-agent/venv/bin/python",
        args=[SERVER_SCRIPT]
    )

    async with stdio_client(
        server_params
    ) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            # MCP handshake
            await session.initialize()

            print("\nConnected to MCP server.")

            # Ask server which tools it exposes
            tools_response = await session.list_tools()

            print("\nAvailable tools:")

            for tool in tools_response.tools:
                print(
                    f"- {tool.name}"
                )


if __name__ == "__main__":
    asyncio.run(run())
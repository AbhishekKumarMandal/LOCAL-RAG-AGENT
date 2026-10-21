import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types


PYTHON_PATH = (
    "/Users/abhishekkumarmandal/Documents/python/"
    "local-rag-agent/venv/bin/python"
)

SERVER_SCRIPT = "scripts/step_11_1_mcp_server.py"


async def run():

    server_params = StdioServerParameters(
        command=PYTHON_PATH,
        args=[SERVER_SCRIPT]
    )

    async with stdio_client(
        server_params
    ) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            print("\nConnected to MCP server.")

            result = await session.call_tool(
                "search_documents_tool",
                arguments={
                    "question": (
                        "How do Kafka consumer groups work?"
                    )
                }
            )

            print("\nRaw MCP tool result:")
            print(result)

            print("\nTool content:")

            for content in result.content:

                if isinstance(
                    content,
                    types.TextContent
                ):
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(run())
import asyncio
import subprocess
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPHostManager:
    def __init__(self, server_script_path):
        self.server_script_path = server_script_path
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        # Configure the server process
        server_params = StdioServerParameters(
            command="node",
            args=[self.server_script_path]
        )
        
        # Start the client session
        transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(transport[0], transport[1]))
        
        # Initialize the MCP connection
        await self.session.initialize()
        print("Connected to MCP server.")

    async def list_tools(self):
        if not self.session:
            raise Exception("Not connected to MCP server.")
        return await self.session.list_tools()

    async def call_tool(self, name, arguments):
        if not self.session:
            raise Exception("Not connected to MCP server.")
        return await self.session.call_tool(name, arguments)

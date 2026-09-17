import asyncio
from contextlib import AsyncExitStack
from typing import List, Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPHostManager:
    """Manages connection and tool execution with an MCP (Model Context Protocol) server."""

    def __init__(self, server_script_path: Optional[str] = None, command: str = "node", args: Optional[List[str]] = None):
        self.server_script_path = server_script_path
        self.command = command
        if args is not None:
            if server_script_path:
                self.args = [server_script_path] + list(args)
            else:
                self.args = list(args)
        else:
            self.args = [server_script_path] if server_script_path else []
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    @property
    def is_connected(self) -> bool:
        return self.session is not None

    async def connect(self):
        """Starts the MCP server process and initializes the client session."""
        if self.is_connected:
            return

        server_params = StdioServerParameters(
            command=self.command,
            args=self.args
        )

        try:
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self.exit_stack.enter_async_context(ClientSession(transport[0], transport[1]))
            await self.session.initialize()
        except Exception:
            await self.disconnect()
            raise

    async def disconnect(self):
        """Disconnects the client session and closes all transport contexts."""
        self.session = None
        await self.exit_stack.aclose()
        self.exit_stack = AsyncExitStack()

    async def list_tools(self) -> Any:
        """Lists available tools exposed by the connected MCP server."""
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected to MCP server.")
        return await self.session.list_tools()

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Calls an MCP tool by name with arguments."""
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected to MCP server.")
        return await self.session.call_tool(name, arguments)

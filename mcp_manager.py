import asyncio
import os
from contextlib import AsyncExitStack
from typing import List, Optional, Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPHostManager:
    """Manages connection and tool execution with an MCP (Model Context Protocol) server."""

    def __init__(
        self,
        server_script_path: Optional[str] = None,
        command: str = "node",
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ):
        self.server_script_path = server_script_path
        self.command = command
        if args is not None:
            if server_script_path:
                self.args = [server_script_path] + list(args)
            else:
                self.args = list(args)
        else:
            self.args = [server_script_path] if server_script_path else []
        self.env = env
        self.cwd = cwd
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
            args=self.args,
            env=self.env,
            cwd=self.cwd,
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

    @classmethod
    def create_desktop_commander(
        cls,
        project_dir: Optional[str] = None,
        custom_path: Optional[str] = None,
        command: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        use_npx: bool = True,
    ) -> "MCPHostManager":
        """
        Creates an MCPHostManager configured to launch DesktopCommander.
        Checks for local build/dist paths, environment variable overrides,
        or falls back to npx package runner.
        """
        base_env: Dict[str, str] = {
            "MCP_DXT": "true",
            "NODE_ENV": "production",
        }
        if env:
            base_env.update(env)

        # 1. Custom path override or environment variable override
        path_override = custom_path or os.environ.get("DESKTOP_COMMANDER_PATH")
        if path_override and os.path.exists(path_override):
            cmd = command or "node"
            args = [path_override, "--no-onboarding"] + (extra_args or [])
            return cls(command=cmd, args=args, env=base_env, cwd=cwd)

        # 2. Search local candidate locations
        search_dirs = []
        if project_dir:
            search_dirs.append(project_dir)
        search_dirs.extend([".", os.path.dirname(os.path.abspath(__file__))])

        for s_dir in search_dirs:
            candidates = [
                os.path.join(s_dir, "desktop-commander", "dist", "index.js"),
                os.path.join(s_dir, "desktop-commander-ext", "dist", "index.js"),
                os.path.join(s_dir, "dist", "index.js"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    cmd = command or "node"
                    args = [os.path.abspath(candidate), "--no-onboarding"] + (extra_args or [])
                    return cls(command=cmd, args=args, env=base_env, cwd=cwd)

        # 3. Fallback to npx or configured command
        if use_npx:
            cmd = command or os.environ.get("DESKTOP_COMMANDER_CMD", "npx")
            args = ["-y", "@wonderwhy-er/desktop-commander@latest", "--no-onboarding"] + (extra_args or [])
            return cls(command=cmd, args=args, env=base_env, cwd=cwd)

        # 4. If npx fallback is disabled and no local script was found, raise FileNotFoundError
        raise FileNotFoundError(
            "DesktopCommander server script not found and npx fallback is disabled. "
            "Please install or build DesktopCommander or specify DESKTOP_COMMANDER_PATH."
        )

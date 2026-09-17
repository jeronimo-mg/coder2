import concurrent.futures
import asyncio
import os
import re
import json
from contextlib import AsyncExitStack
from typing import List, Optional, Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.table import Table

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


def format_mcp_tools_context(tools: Optional[List[Any]]) -> str:
    """
    Formats the list of MCP tools into a Markdown section suitable for
    injecting into the agent's context prompt with clear operational guidelines.
    """
    if not tools:
        return ""

    lines = [
        "## Local MCP Tools (DesktopCommander)",
        "DesktopCommander is an active Model Context Protocol (MCP) server running on the user's host machine (outside your sandbox container).",
        "The Coderagy CLI harness automatically intercepts `<mcp_call>` tags from your response, executes the requested tool on the user's machine, and feeds the output back to you in `<mcp_result>`.",
        "",
        "### Operational Instructions (Zero-Hesitation Execution):",
        "1. **Direct Invocation:** When the user asks to create, modify, inspect files on their machine or run host commands with DesktopCommander, IMMEDIATELY emit the `<mcp_call>` tag. Do NOT search for DesktopCommander inside your sandbox container, do NOT test if the tag is supported, and do NOT inspect DesktopCommander source code.",
        "2. **DOCX Document Generation:** To create or edit Word documents (`.docx`), call `write_file` with `\"mode\": \"rewrite\"`. DesktopCommander automatically converts standard Markdown text (`# Heading 1`, `## Heading 2`, `- bullet list`, formatted paragraphs) into native styled DOCX XML. You do NOT need to write Python scripts or install docx packages.",
        "3. **Excel & PDF Support:**",
        "   - For Excel (`.xlsx`, `.xls`), use `write_file` with JSON 2D array content.",
        "   - For PDF (`.pdf`), use `write_pdf`.",
        "4. **Invocation Format:**",
        '<mcp_call name="tool_name">{"arg_name": "arg_value"}</mcp_call>',
        "",
        "Available Tools:"
    ]

    for tool in tools:
        name = getattr(tool, 'name', None) or (tool.get('name') if isinstance(tool, dict) else str(tool))
        desc = getattr(tool, 'description', '') or (tool.get('description', '') if isinstance(tool, dict) else '')
        schema = getattr(tool, 'inputSchema', {}) or (tool.get('inputSchema', {}) if isinstance(tool, dict) else {})

        props = schema.get('properties', {}) if isinstance(schema, dict) else {}
        param_list = list(props.keys()) if props else []
        params_str = f" (Parameters: {', '.join(param_list)})" if param_list else ""

        desc_str = f": {desc}" if desc else ""
        lines.append(f"- `{name}`{params_str}{desc_str}")

    return "\n".join(lines)


def get_mcp_tools_table(tools: Optional[List[Any]]) -> Table:
    """
    Builds a Rich Table displaying discovered MCP tools.
    """
    table = Table(title="DesktopCommander MCP Tools", border_style="cyan")
    table.add_column("Tool Name", style="bold cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Parameters", style="dim green")

    if not tools:
        table.add_row("(none)", "No tools discovered", "")
        return table

    for tool in tools:
        name = getattr(tool, 'name', None) or (tool.get('name') if isinstance(tool, dict) else str(tool))
        desc = getattr(tool, 'description', '') or (tool.get('description', '') if isinstance(tool, dict) else '')
        schema = getattr(tool, 'inputSchema', {}) or (tool.get('inputSchema', {}) if isinstance(tool, dict) else {})
        props = schema.get('properties', {}) if isinstance(schema, dict) else {}
        param_list = list(props.keys()) if props else []
        params_str = ", ".join(param_list) if param_list else "(none)"
        table.add_row(name, desc or "(no description)", params_str)

    return table


def parse_mcp_tool_calls(text: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parses <mcp_call name="...">...</mcp_call> blocks from agent output.
    Returns list of dicts with keys: name, arguments, raw, and optionally error.
    """
    if not text:
        return []

    pattern = re.compile(r'<mcp_call\s+(?:name|tool)=["\']([^"\']+)["\']\s*>(.*?)</mcp_call>', re.DOTALL | re.IGNORECASE)
    tool_calls = []

    for match in pattern.finditer(text):
        name = match.group(1).strip()
        body = match.group(2).strip()
        raw = match.group(0)

        args = {}
        error = None
        if body:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    args = parsed
                else:
                    args = {"input": parsed}
            except Exception as e:
                error = f"Invalid JSON payload: {e}"

        call_info: Dict[str, Any] = {
            "name": name,
            "arguments": args,
            "raw": raw,
        }
        if error:
            call_info["error"] = error
        tool_calls.append(call_info)

    return tool_calls


def format_mcp_tool_result(name: str, result: Any, error: Optional[str] = None) -> str:
    """
    Formats the tool output into <mcp_result> XML tags for agent feedback.
    """
    if error:
        return f'<mcp_result name="{name}" status="error">\n{error}\n</mcp_result>'

    if isinstance(result, (dict, list)):
        formatted_content = json.dumps(result, indent=2)
    else:
        formatted_content = str(result)

    return f'<mcp_result name="{name}" status="success">\n{formatted_content}\n</mcp_result>'


async def execute_mcp_tool_calls(manager: MCPHostManager, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Asynchronously executes a list of parsed tool calls using an MCPHostManager instance.
    """
    results = []
    for call in tool_calls:
        name = call.get("name", "")
        args = call.get("arguments", {})
        if "error" in call:
            results.append({
                "name": name,
                "result": None,
                "error": call["error"],
            })
            continue

        try:
            res = await manager.call_tool(name, args)
            results.append({
                "name": name,
                "result": res,
                "error": None,
            })
        except Exception as e:
            results.append({
                "name": name,
                "result": None,
                "error": str(e),
            })

    return results


def strip_mcp_tags(text: Optional[str]) -> str:
    """
    Strips <mcp_call> tags from text to prepare clean user-facing response.
    """
    if not text:
        return ""
    pattern = re.compile(r'<mcp_call\s+.*?/mcp_call>', re.DOTALL | re.IGNORECASE)
    return pattern.sub('', text).strip()


def run_sync(coro, loop: Optional[asyncio.AbstractEventLoop] = None) -> Any:
    """
    Safely executes an async coroutine from a synchronous context,
    even if an asyncio event loop is already active in the current thread.
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop and running_loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    elif loop and not loop.is_closed():
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)

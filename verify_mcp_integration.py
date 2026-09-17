#!/usr/bin/env python3
"""
End-to-End Verification Script: MCP Host Integration (DesktopCommander)
Verifies that Coderagy can natively launch, discover, and execute DesktopCommander MCP tools.
"""

import os
import sys
import asyncio
import tempfile
from unittest.mock import MagicMock
from rich.console import Console

from mcp_manager import (
    MCPHostManager,
    format_mcp_tools_context,
    get_mcp_tools_table,
    parse_mcp_tool_calls,
    format_mcp_tool_result,
    strip_mcp_tags,
)
from prototype_tui import handle_chat_mcp_execution

console = Console()

def create_mock_desktop_commander_server(server_path: str):
    server_script = """
import sys
from mcp.server.mcpserver import MCPServer

server = MCPServer("DesktopCommander")

@server.tool(name="read_file", description="Read contents of a file on the host machine")
def read_file(path: str) -> str:
    return f"[MOCK_DESKTOP_COMMANDER] Contents of {path}: Coderagy native MCP integration active!"

@server.tool(name="list_directory", description="List files and directories")
def list_directory(path: str) -> str:
    return "README.md\\npackage.json\\nsrc/\\n"

@server.tool(name="start_process", description="Start a local terminal process")
def start_process(command: str) -> str:
    return f"Process '{command}' started successfully (PID: 12345)"

if __name__ == "__main__":
    server.run(transport="stdio")
"""
    with open(server_path, "w") as f:
        f.write(server_script)

async def verify_mcp_host():
    console.print("[bold blue]====================================================[/bold blue]")
    console.print("[bold blue]Starting MCP Host Integration Verification (Phase 3)[/bold blue]")
    console.print("[bold blue]====================================================[/bold blue]\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        server_path = os.path.join(tmp_dir, "desktop_commander_server.py")
        create_mock_desktop_commander_server(server_path)

        # 1. Verify Launch & Connect
        console.print("[bold cyan]1. Launching and connecting to DesktopCommander process...[/bold cyan]")
        mgr = MCPHostManager(command=sys.executable, args=[server_path])
        await mgr.connect()
        assert mgr.is_connected, "Manager failed to connect!"
        console.print("[green]✔ Successfully connected over stdio transport![/green]\n")

        # 2. Verify Tool Discovery
        console.print("[bold cyan]2. Testing Tool Discovery...[/bold cyan]")
        tools_resp = await mgr.list_tools()
        tools_list = tools_resp.tools
        tool_names = [t.name for t in tools_list]
        console.print(f"Discovered {len(tools_list)} tools: {tool_names}")
        assert "read_file" in tool_names, "Missing read_file tool!"
        assert "list_directory" in tool_names, "Missing list_directory tool!"
        assert "start_process" in tool_names, "Missing start_process tool!"

        # Render Table & Prompt Context
        table = get_mcp_tools_table(tools_list)
        console.print(table)

        prompt_context = format_mcp_tools_context(tools_list)
        assert "## Local MCP Tools (DesktopCommander)" in prompt_context
        assert "read_file" in prompt_context
        console.print("[green]✔ Tool Discovery and Prompt Context Generation Verified![/green]\n")

        # 3. Verify Direct Tool Execution
        console.print("[bold cyan]3. Testing Direct Tool Execution...[/bold cyan]")
        res = await mgr.call_tool("read_file", {"path": "/workspace/sample.txt"})
        console.print(f"Direct tool result: {res}")
        res_str = str(res)
        assert "Coderagy native MCP integration active!" in res_str
        console.print("[green]✔ Direct Tool Execution Verified![/green]\n")

        # 4. Verify Chat-based Execution Loop (REPL Interception)
        console.print("[bold cyan]4. Testing Chat-based Execution Loop (REPL Interception)...[/bold cyan]")
        raw_agent_output = (
            "I will check the file using the local MCP tool:\n"
            '<mcp_call name="read_file">{"path": "/test/demo.txt"}</mcp_call>'
        )

        mock_client = MagicMock()
        mock_followup = MagicMock()
        mock_followup.id = "followup_interaction_456"
        mock_client.send_follow_up.return_value = mock_followup
        mock_client.monitor_interaction.return_value = "The file was successfully read and contains the requested data."

        final_raw, final_id, clean_resp = await handle_chat_mcp_execution(
            raw_output=raw_agent_output,
            mcp_mgr=mgr,
            client=mock_client,
            active_interaction_id="initial_interaction_123",
            active_environment_id="env_abc",
            handle_thought=lambda t, i: None,
            handle_step=lambda a, d, i: None,
            show_thoughts=False,
        )

        assert final_id == "followup_interaction_456"
        assert "successfully read" in clean_resp
        assert "<mcp_call" not in clean_resp
        console.print(f"Final Clean Response: '{clean_resp}'")
        console.print("[green]✔ Chat-based Tool Execution and Feedback Loop Verified![/green]\n")

        # Clean disconnect
        await mgr.disconnect()
        assert not mgr.is_connected
        console.print("[green]✔ Cleanly disconnected from MCP process.[/green]\n")

    console.print("[bold green]========================================================[/bold green]")
    console.print("[bold green]ALL PHASE 3 VERIFICATION CHECKS PASSED SUCCESSFULLY!  [/bold green]")
    console.print("[bold green]========================================================[/bold green]")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_mcp_host())
    sys.exit(0 if success else 1)

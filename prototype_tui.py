from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from agent_client import AntigravityClient
import os
import time
import json
import threading
import asyncio
from mcp_manager import MCPHostManager

console = Console()
client = AntigravityClient()
# Assume DesktopCommander is in a relative path
mcp_manager = MCPHostManager(os.path.join("desktop-commander-ext", "dist", "index.js"))

async def initialize_mcp():
    await mcp_manager.connect()
    tools = await mcp_manager.list_tools()
    console.print(f"[bold cyan]Connected to DesktopCommander.[/bold cyan] Available tools: {[t.name for t in tools.tools]}")
    return tools

def run_tui(initial_environment_id=None):
    # Setup event loop for MCP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tools = loop.run_until_complete(initialize_mcp())
    
    session = PromptSession()
    active_interaction_id = None
    active_environment_id = initial_environment_id
    
    console.print(Panel("[bold green]Coderagy CLI Interactive Mode[/bold green]\nType 'exit' to quit. Use '/download' to save.\nUse '/tools' to list MCP tools, '/call <tool> <json_args>' to execute.", title="Welcome"))
    
    if active_environment_id:
        console.print(f"[bold green]Resuming session with environment: {active_environment_id}[/bold green]")

    while True:
        try:
            user_input = session.prompt(HTML("<style bg='green' fg='white'> coderagy </style> > "))
            
            if user_input.strip().lower() == 'exit':
                # ... (exit logic)
                break
            
            # ... (Slash Commands)
            if user_input.strip().lower().startswith('/download'):
                dest = input("Enter destination path for download: ").strip('"').strip("'")
                if not active_environment_id:
                    console.print("[red]No active sandbox found. Cannot download.[/red]")
                    continue
                try:
                    client.download_snapshot(active_environment_id, dest)
                    console.print(Panel(f"[bold green]Snapshot successfully downloaded to: {dest}[/bold green]", title="Download Complete"))
                except Exception as e:
                    console.print(Panel(f"[bold red]Download failed: {e}[/bold red]", title="Error"))
                continue
            
            if user_input.strip().lower().startswith('/tools'):
                tools = loop.run_until_complete(mcp_manager.list_tools())
                console.print(f"Available tools: {[t.name for t in tools.tools]}")
                continue
                
            if user_input.strip().lower().startswith('/call'):
                parts = user_input.split(" ", 2)
                if len(parts) < 2:
                    console.print("[red]Usage: /call <tool_name> <json_args>[/red]")
                    continue
                tool_name = parts[1]
                args = json.loads(parts[2]) if len(parts) > 2 else {}
                
                result = loop.run_until_complete(mcp_manager.call_tool(tool_name, args))
                console.print(Panel(str(result), title=f"Tool Output: {tool_name}"))
                continue
            
            # Default agent interaction logic
            with console.status("[bold green]Thinking...[/bold green]"):
                if active_interaction_id:
                    interaction = client.send_follow_up(active_interaction_id, active_environment_id, user_input)
                    # Important: Update to the NEW interaction ID for the next follow-up
                    active_interaction_id = interaction.id
                else:
                    interaction = client.create_interaction(user_input, active_environment_id)
                    active_interaction_id = interaction.id
                    active_environment_id = interaction.environment_id

                # Simple polling
                while True:
                    interaction = client.client.interactions.get(active_interaction_id)
                    if interaction.status == "completed":
                        console.print(Panel(interaction.output_text, title="Agent Response"))
                        break
                    elif interaction.status == "failed":
                        console.print(Panel(str(interaction.error), title="Agent Error", style="red"))
                        break
                    time.sleep(2)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    run_tui()

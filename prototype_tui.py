from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from agent_client import AntigravityClient
from conductor_manager import ConductorManager
import os
import time
import json
import threading
import asyncio
from mcp_manager import MCPHostManager

console = Console()
conductor = ConductorManager()

def get_mcp_manager():
    mcp_path = os.path.join("desktop-commander-ext", "dist", "index.js")
    if os.path.exists(mcp_path):
        return MCPHostManager(mcp_path)
    return None

async def initialize_mcp(mcp_mgr):
    if not mcp_mgr:
        return None
    try:
        await mcp_mgr.connect()
        tools = await mcp_mgr.list_tools()
        console.print(f"[bold cyan]Connected to DesktopCommander.[/bold cyan] Available tools: {[t.name for t in tools.tools]}")
        return tools
    except Exception as e:
        console.print(f"[yellow]DesktopCommander MCP initialization skipped: {e}[/yellow]")
        return None

def run_tui(initial_environment_id=None):
    client = AntigravityClient()
    mcp_mgr = get_mcp_manager()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tools = loop.run_until_complete(initialize_mcp(mcp_mgr)) if mcp_mgr else None
    
    session = PromptSession()
    active_interaction_id = None
    active_environment_id = initial_environment_id
    
    welcome_msg = (
        "[bold green]Coderagy CLI Interactive Mode[/bold green]\n"
        "Commands:\n"
        "  - '/conductor:status' or '/status': View Conductor project tracks and progress\n"
        "  - '/conductor:tracks' or '/tracks': List all registered tracks\n"
        "  - '/conductor:new-track <name>': Create a new Spec-Driven Development track\n"
        "  - '/conductor:context': View current SDD context injected into the agent\n"
        "  - '/download': Download sandbox snapshot\n"
        "  - '/tools': List available MCP tools\n"
        "  - '/call <tool> <json_args>': Execute MCP tool\n"
        "  - 'exit': Quit"
    )
    console.print(Panel(welcome_msg, title="Welcome to Coderagy"))
    
    if active_environment_id:
        console.print(f"[bold green]Resuming session with environment: {active_environment_id}[/bold green]")

    while True:
        try:
            user_input = session.prompt(HTML("<style bg='green' fg='white'> coderagy </style> > "))
            cleaned = user_input.strip()

            if cleaned.lower() == 'exit':
                break

            if not cleaned:
                continue
            
            # --- Slash Commands ---
            # 1. Conductor Status
            if cleaned.lower() in ['/status', '/conductor', '/conductor:status', '/conductor status']:
                console.print(conductor.format_status_report())
                continue

            # 2. Conductor Tracks
            if cleaned.lower() in ['/tracks', '/conductor:tracks', '/conductor tracks']:
                tracks = conductor.list_tracks()
                if not tracks:
                    console.print("[yellow]No tracks registered in conductor/tracks.md.[/yellow]")
                else:
                    console.print("[bold cyan]Conductor Tracks:[/bold cyan]")
                    for t in tracks:
                        badge = "[green][x][/green]" if t["status"] == "completed" else ("[yellow][~][/yellow]" if t["status"] == "in_progress" else "[dim][ ][/dim]")
                        console.print(f"  {badge} {t['name']} [dim]({t['status']})[/dim]")
                continue

            # 3. Conductor New Track
            if (cleaned.lower().startswith('/conductor:new-track') or 
                cleaned.lower().startswith('/conductor new-track') or 
                cleaned.lower().startswith('/new-track')):
                parts = cleaned.split(" ", 1)
                track_name = parts[1].strip() if len(parts) > 1 else ""
                if not track_name:
                    track_name = input("Enter track name: ").strip()
                if track_name:
                    t = conductor.create_track(track_name)
                    console.print(Panel(f"[green]Track created![/green]\nID: {t['track_id']}\nPath: {t['path']}", title="Conductor Track Created"))
                else:
                    console.print("[red]Track name cannot be empty.[/red]")
                continue

            # 4. Conductor Context
            if cleaned.lower() in ['/context', '/conductor:context', '/conductor context']:
                ctx = conductor.get_agent_context()
                if ctx:
                    console.print(Panel(ctx, title="Conductor SDD Context"))
                else:
                    console.print("[yellow]No Conductor context found or Conductor not initialized.[/yellow]")
                continue

            # 5. Download Snapshot
            if cleaned.lower().startswith('/download'):
                dest = input("Enter destination path for download: ").strip('\"').strip("'")
                if not active_environment_id:
                    console.print("[red]No active sandbox found. Cannot download.[/red]")
                    continue
                try:
                    client.download_snapshot(active_environment_id, dest)
                    console.print(Panel(f"[bold green]Snapshot successfully downloaded to: {dest}[/bold green]", title="Download Complete"))
                except Exception as e:
                    console.print(Panel(f"[bold red]Download failed: {e}[/bold red]", title="Error"))
                continue
            
            # 6. MCP Tools
            if cleaned.lower().startswith('/tools'):
                if mcp_mgr:
                    tools_result = loop.run_until_complete(mcp_mgr.list_tools())
                    console.print(f"Available tools: {[t.name for t in tools_result.tools]}")
                else:
                    console.print("[yellow]MCP host is not connected.[/yellow]")
                continue
                
            if cleaned.lower().startswith('/call'):
                if not mcp_mgr:
                    console.print("[yellow]MCP host is not connected.[/yellow]")
                    continue
                parts = cleaned.split(" ", 2)
                if len(parts) < 2:
                    console.print("[red]Usage: /call <tool_name> <json_args>[/red]")
                    continue
                tool_name = parts[1]
                args = json.loads(parts[2]) if len(parts) > 2 else {}
                
                result = loop.run_until_complete(mcp_mgr.call_tool(tool_name, args))
                console.print(Panel(str(result), title=f"Tool Output: {tool_name}"))
                continue
            
            # --- Default Agent Interaction Loop ---
            with console.status("[bold green]Thinking...[/bold green]"):
                if active_interaction_id:
                    interaction = client.send_follow_up(active_interaction_id, active_environment_id, cleaned)
                    active_interaction_id = interaction.id
                else:
                    # Inject Conductor context on initial prompt if available
                    agent_prompt = cleaned
                    if conductor.is_initialized():
                        sdd_context = conductor.get_agent_context(max_chars=2500)
                        if sdd_context:
                            agent_prompt = f"{sdd_context}\n\n---\nUser Request:\n{cleaned}"
                            console.print("[dim]Enriched prompt with Conductor Spec-Driven Development context.[/dim]")

                    interaction = client.create_interaction(agent_prompt, active_environment_id)
                    active_interaction_id = interaction.id
                    active_environment_id = interaction.environment_id

                # Polling
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

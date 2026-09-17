from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from agent_client import AntigravityClient, extract_output_text
from conductor_manager import ConductorManager
import os
import time
import json
import threading
import asyncio
import re
from mcp_manager import MCPHostManager

console = Console()
conductor = ConductorManager()

def parse_embedded_thoughts(text):
    """
    Extracts embedded <thought>...</thought> or <thinking>...</thinking> tags from text.
    Returns (list_of_thoughts, cleaned_text).
    """
    if not text:
        return [], ""
    pattern = re.compile(r'<(thought|thinking)>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
    thoughts = []
    for match in pattern.finditer(text):
        thoughts.append(match.group(2).strip())
    cleaned_text = pattern.sub('', text).strip()
    return thoughts, cleaned_text

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

def run_tui(initial_environment_id=None, default_show_thoughts=True):
    client = AntigravityClient()
    mcp_mgr = get_mcp_manager()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tools = loop.run_until_complete(initialize_mcp(mcp_mgr)) if mcp_mgr else None

    session = PromptSession()
    active_interaction_id = None
    active_environment_id = initial_environment_id
    show_thoughts = default_show_thoughts

    plugin_info = conductor.get_plugin_info()
    plugin_status_str = f"Conductor Plugin: Active (v{plugin_info['version']})" if plugin_info["installed"] else "Conductor Plugin: Available"

    welcome_msg = (
        f"[bold green]Coderagy CLI Interactive Mode[/bold green]\n"
        f"[dim]{plugin_status_str} - Conversational Spec-Driven Development[/dim]\n\n"
        "Commands:\n"
        "  - '/thoughts [on|off]': Visualizar pensamento do agente em tempo real (Padrão: ativado)\n"
        "  - '/conductor:status' or '/status': View Conductor project tracks and progress\n"
        "  - '/conductor:tracks' or '/tracks': List all registered tracks\n"
        "  - '/conductor:new-track <name>': Create a new Spec-Driven Development track\n"
        "  - '/conductor:context': View current SDD context injected into the agent\n"
        "  - '/conductor:plugin' or '/plugin': View Conductor Plugin details & skills\n"
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
            # 0. Thoughts Toggle
            if cleaned.lower().startswith('/thoughts') or cleaned.lower().startswith('/thought'):
                parts = cleaned.split()
                if len(parts) > 1:
                    arg = parts[1].lower()
                    if arg in ['on', 'true', '1', 'ativar', 'sim', 'enable']:
                        show_thoughts = True
                    elif arg in ['off', 'false', '0', 'desativar', 'nao', 'não', 'disable']:
                        show_thoughts = False
                    else:
                        console.print("[yellow]Uso: /thoughts [on|off][/yellow]")
                        continue
                else:
                    show_thoughts = not show_thoughts

                status_label = "[bold green]ATIVADA[/bold green]" if show_thoughts else "[bold red]DESATIVADA[/bold red]"
                console.print(f"Visualização do pensamento do agente: {status_label}")
                continue

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

            # 5. Conductor Plugin Info & Skills
            if cleaned.lower() in ['/plugin', '/plugins', '/conductor:plugin', '/conductor plugin', '/skills', '/conductor:skills']:
                info = conductor.get_plugin_info()
                if info["installed"]:
                    skills_desc = "\n".join([f"  • [bold]{s['name']}[/bold]: {s['description']}" for s in info["skills"]])
                    console.print(Panel(
                        f"[bold green]Conductor Plugin (v{info['version']})[/bold green]\n"
                        f"{info['description']}\n\n"
                        f"[bold cyan]Bundled Skills:[/bold cyan]\n{skills_desc}",
                        title="Conductor Plugin"
                    ))
                else:
                    console.print("[yellow]Conductor Plugin not found.[/yellow]")
                continue

            # 6. Download Snapshot
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

            # 7. MCP Tools
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

            # --- Default Agent Interaction Loop with Real-Time Thinking & Resilience ---
            def handle_thought(thought_text, idx):
                if show_thoughts and thought_text and thought_text.strip():
                    console.print(Panel(
                        thought_text.strip(),
                        title=f"[bold magenta]🤔 Pensamento do Agente (Etapa #{idx+1})[/bold magenta]",
                        border_style="magenta"
                    ))

            def handle_step(action_type, details, idx):
                if show_thoughts and details:
                    if action_type == "code_execution":
                        console.print(Panel(
                            f"[cyan]{details.strip()}[/cyan]",
                            title=f"[bold cyan]⚡ Executando Sandbox #{idx+1}[/bold cyan]",
                            border_style="cyan"
                        ))
                    elif action_type == "code_result":
                        res_str = details.strip()
                        if len(res_str) > 300:
                            res_str = res_str[:300] + "... [dim](truncado)[/dim]"
                        console.print(f"[dim green]↳ Saída: {res_str}[/dim green]")
                    elif action_type == "mcp_tool":
                        console.print(f"[bold yellow]🔧 Ferramenta MCP:[/bold yellow] [dim]{details}[/dim]")
                    elif action_type == "google_search":
                        console.print(f"[bold blue]🔍 Busca Google:[/bold blue] [dim]{details}[/dim]")
                    elif action_type == "url_fetch":
                        console.print(f"[bold blue]🌐 Leitura URL:[/bold blue] [dim]{details}[/dim]")

            with console.status("[bold green]O agente está trabalhando...[/bold green]"):
                interaction = None
                if active_interaction_id:
                    try:
                        interaction = client.send_follow_up(active_interaction_id, active_environment_id, cleaned)
                        active_interaction_id = interaction.id
                        new_env = getattr(interaction, 'environment_id', None)
                        if new_env and isinstance(new_env, str):
                            active_environment_id = new_env
                    except Exception as follow_up_err:
                        err_str = str(follow_up_err).lower()
                        # Fallback for HTTP 400 / Precondition check failed / invalid_request
                        if "400" in str(follow_up_err) or "precondition" in err_str or "invalid_request" in err_str:
                            console.print("[dim yellow]⚠️ Continuação da interação anterior indisponível (pré-condição falhou). Iniciando nova interação com contexto preservado...[/dim yellow]")
                            active_interaction_id = None
                            interaction = None
                        else:
                            active_interaction_id = None
                            raise follow_up_err

                if not interaction:
                    # Inject Conductor Plugin context on prompt if available
                    agent_prompt = cleaned
                    if conductor.is_initialized():
                        sdd_context = conductor.get_agent_context(max_chars=2500)
                        if sdd_context:
                            agent_prompt = f"{sdd_context}\n\n---\nUser Request:\n{cleaned}"
                            console.print("[dim]Enriched prompt with Conductor Plugin context.[/dim]")

                    try:
                        interaction = client.create_interaction(agent_prompt, active_environment_id)
                        active_interaction_id = interaction.id
                        new_env = getattr(interaction, 'environment_id', None)
                        if new_env and isinstance(new_env, str):
                            active_environment_id = new_env
                    except Exception as create_err:
                        err_str = str(create_err).lower()
                        # Fallback if active_environment_id is stale / not found / rejected
                        if active_environment_id and ("400" in str(create_err) or "precondition" in err_str or "not found" in err_str or "404" in str(create_err)):
                            console.print("[dim yellow]⚠️ Sandbox anterior inacessível ou expirado. Provisionando novo sandbox remoto...[/dim yellow]")
                            active_environment_id = None
                            interaction = client.create_interaction(agent_prompt, None)
                            active_interaction_id = interaction.id
                            new_env = getattr(interaction, 'environment_id', None)
                            if new_env and isinstance(new_env, str):
                                active_environment_id = new_env
                        else:
                            active_interaction_id = None
                            raise create_err

                try:
                    raw_output = client.monitor_interaction(
                        active_interaction_id,
                        on_thought=handle_thought,
                        on_step=handle_step
                    )
                    # Item B: Update active_environment_id upon successful completion
                    if getattr(client, 'last_environment_id', None):
                        active_environment_id = client.last_environment_id
                    elif active_interaction_id:
                        try:
                            direct_int = client.client.interactions.get(active_interaction_id)
                            comp_env = getattr(direct_int, 'environment_id', None)
                            if comp_env and isinstance(comp_env, str):
                                active_environment_id = comp_env
                                client.last_environment_id = comp_env
                        except Exception:
                            pass
                except Exception as mon_err:
                    # Item A: Invalidate interaction ID so next turn won't attempt to continue a failed interaction
                    active_interaction_id = None
                    raise mon_err

            # Fallback if raw_output was empty: retrieve interaction directly
            if not raw_output or not raw_output.strip():
                try:
                    direct_int = client.client.interactions.get(active_interaction_id)
                    raw_output = getattr(direct_int, 'output_text', None) or extract_output_text(direct_int) or ""
                except Exception:
                    pass

            # Check for embedded thought tags if any
            embedded_thoughts, clean_response = parse_embedded_thoughts(raw_output)
            if show_thoughts and embedded_thoughts:
                for ethought in embedded_thoughts:
                    console.print(Panel(
                        ethought,
                        title="[bold magenta]🤔 Pensamento do Agente[/bold magenta]",
                        border_style="magenta"
                    ))

            final_text = clean_response.strip() if clean_response.strip() else raw_output.strip()
            if final_text:
                console.print(Panel(final_text, title="Agent Response", border_style="green"))
            else:
                if not embedded_thoughts:
                    console.print("[dim yellow]O agente concluiu a execução sem gerar resposta de texto.[/dim yellow]")

        except Exception as e:
            active_interaction_id = None
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    run_tui()

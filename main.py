import argparse
import os
from storage import SandboxStorage
from rich.console import Console
from rich.panel import Panel

console = Console()

def main(args=None):
    parser = argparse.ArgumentParser(description="Coderagy CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a project sandbox")
    init_parser.add_argument("project_name", help="Name of the project")

    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup project sandbox")
    cleanup_parser.add_argument("project_name", help="Name of the project")

    download_parser = subparsers.add_parser("download", help="Download project sandbox")
    download_parser.add_argument("project_name", help="Name of the project")

    desktop_parser = subparsers.add_parser("desktop", help="Interface with DesktopCommander")
    desktop_parser.add_argument("action", help="Action to perform (e.g., list, run)")

    conductor_parser = subparsers.add_parser("conductor", help="Interface with Conductor SDD extension")
    conductor_parser.add_argument("action", nargs="?", default="status", choices=["status", "tracks", "new-track", "context", "setup"], help="Conductor action to perform")
    conductor_parser.add_argument("--name", help="Track name (for new-track)")
    conductor_parser.add_argument("--desc", help="Track description (for new-track)")

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("--no-interactive", action="store_false", dest="interactive", help="Disable interactive TUI mode")
    parser.set_defaults(interactive=True)
    
    parsed_args = parser.parse_args(args)
    storage = SandboxStorage()

    # If a specific command was given, execute it non-interactively
    if parsed_args.command:
        if parsed_args.command == "init":
            state = {"project_name": parsed_args.project_name}
            storage.save_state(parsed_args.project_name, state)
            print(f"Project '{parsed_args.project_name}' sandbox initialized.")
            return

        elif parsed_args.command == "cleanup":
            path = os.path.join(".sandbox", f"{parsed_args.project_name}.json")
            if os.path.exists(path):
                os.remove(path)
                print(f"Project '{parsed_args.project_name}' sandbox cleaned.")
            else:
                console.print(Panel(f"[bold red]No sandbox found for '{parsed_args.project_name}'.[/bold red]", title="Error"))
            return

        elif parsed_args.command == "download":
            from agent_client import AntigravityClient
            dest = input("Enter destination path for download: ").strip('\"').strip("'")
            if os.path.exists(dest):
                confirm = input(f"File {dest} exists. Overwrite? (y/n): ")
                if confirm.lower() != 'y':
                    console.print("[bold yellow]Download cancelled.[/bold yellow]")
                    return
            
            state = storage.load_state(parsed_args.project_name)
            if not state or not state.get("environment_id"):
                console.print(Panel(f"[bold red]No active sandbox found for '{parsed_args.project_name}'. Please initialize it first.[/bold red]", title="Error"))
                return
                
            environment_id = state.get("environment_id")
            console.print(f"[dim]Initiating download for environment: {environment_id}[/dim]")
            client = AntigravityClient(project_name=parsed_args.project_name)
            try:
                client.download_snapshot(environment_id, dest)
                console.print(Panel(f"[bold green]Snapshot successfully downloaded and extracted to: {dest}[/bold green]", title="Download Complete"))
            except Exception as e:
                console.print(Panel(f"[bold red]Download failed: {e}[/bold red]", title="Error"))
            return

        elif parsed_args.command == "desktop":
            console.print(f"DesktopCommander action '[bold cyan]{parsed_args.action}[/bold cyan]' requested.")
            return

        elif parsed_args.command == "conductor":
            from conductor_manager import ConductorManager
            mgr = ConductorManager()

            if parsed_args.action == "status":
                console.print(mgr.format_status_report())
            elif parsed_args.action == "tracks":
                tracks = mgr.list_tracks()
                if not tracks:
                    console.print("[yellow]No tracks registered in conductor/tracks.md.[/yellow]")
                else:
                    console.print("[bold cyan]Registered Conductor Tracks:[/bold cyan]")
                    for t in tracks:
                        badge = "[green][x][/green]" if t["status"] == "completed" else ("[yellow][~][/yellow]" if t["status"] == "in_progress" else "[dim][ ][/dim]")
                        console.print(f"  {badge} {t['name']} [dim]({t['id']})[/dim]")
            elif parsed_args.action == "new-track":
                track_name = parsed_args.name or input("Enter track name: ").strip()
                if not track_name:
                    console.print("[red]Track name cannot be empty.[/red]")
                    return
                desc = parsed_args.desc or ""
                track = mgr.create_track(track_name, description=desc)
                console.print(Panel(f"[green]Track created successfully![/green]\nID: {track['track_id']}\nPath: {track['path']}", title="Conductor"))
            elif parsed_args.action == "context":
                ctx = mgr.get_agent_context()
                if ctx:
                    console.print(Panel(ctx, title="Conductor Agent Context"))
                else:
                    console.print("[yellow]Conductor context is empty or not initialized.[/yellow]")
            elif parsed_args.action == "setup":
                mgr.setup()
                console.print(Panel("[green]Conductor initialized successfully.[/green]", title="Conductor Setup"))
            return

    # If no command and interactive is enabled, run the interactive TUI
    if parsed_args.interactive:
        selected_env_id = None
        if os.path.exists(".sandbox"):
            sandboxes = [f for f in os.listdir(".sandbox") if f.endswith(".json")]
            if sandboxes:
                console.print("[bold cyan]Existing sandboxes found:[/bold cyan]")
                for i, sb in enumerate(sandboxes):
                    console.print(f"[{i+1}] {sb.replace('.json', '')}")
                console.print("[0] Create new sandbox")
                
                try:
                    choice = input("Select an option: ")
                    if choice.isdigit() and 0 < int(choice) <= len(sandboxes):
                        sb_name = sandboxes[int(choice)-1]
                        state = storage.load_state(sb_name.replace('.json', ''))
                        selected_env_id = state.get("environment_id") if state else None
                        console.print(f"[green]Using existing sandbox: {sb_name.replace('.json', '')}[/green]")
                    else:
                        console.print("[dim]Creating a new sandbox...[/dim]")
                except (EOFError, KeyboardInterrupt):
                    pass

        from prototype_tui import run_tui
        run_tui(initial_environment_id=selected_env_id)
        return

    console.print(Panel("[bold]Coderagy CLI initialized.[/bold]", title="Status"))

if __name__ == "__main__":
    main()

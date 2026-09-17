import argparse
import os
from storage import SandboxStorage
from agent_client import AntigravityClient
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

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    # Make interactive the default workflow
    parser.add_argument("--no-interactive", action="store_false", dest="interactive", help="Disable interactive TUI mode")
    parser.set_defaults(interactive=True)
    
    args = parser.parse_args(args)
    
    # 1. Initialization/Sandbox Selection Phase
    storage = SandboxStorage()
    sandboxes = [f for f in os.listdir(".sandbox") if f.endswith(".json")]
    
    selected_env_id = None
    
    if sandboxes:
        console.print("[bold cyan]Existing sandboxes found:[/bold cyan]")
        for i, sb in enumerate(sandboxes):
            console.print(f"[{i+1}] {sb.replace('.json', '')}")
        console.print("[0] Create new sandbox")
        
        choice = input("Select an option: ")
        if choice.isdigit() and 0 < int(choice) <= len(sandboxes):
            sb_name = sandboxes[int(choice)-1]
            state = storage.load_state(sb_name.replace('.json', ''))
            selected_env_id = state.get("environment_id")
            console.print(f"[green]Using existing sandbox: {sb_name.replace('.json', '')}[/green]")
            console.print(f"[dim]DEBUG: Loaded environment_id from storage: {selected_env_id}[/dim]")
        else:
            console.print("[dim]Creating a new sandbox...[/dim]")
    
    # 2. Interactive Mode Phase
    if args.interactive:
        from prototype_tui import run_tui
        # Pass the selected_env_id to the TUI if one was chosen
        run_tui(initial_environment_id=selected_env_id)
        return
    
    # Initialize client for non-interactive commands
    client = AntigravityClient(project_name=args.project_name if hasattr(args, 'project_name') else "default")
    
    # 3. Command Execution Phase
    if args.command == "cleanup":
        # Simplified cleanup logic for now
        path = os.path.join(".sandbox", f"{args.project_name}.json")
        if os.path.exists(path):
            os.remove(path)
            console.print(Panel(f"[bold yellow]Project '{args.project_name}' sandbox cleaned.[/bold yellow]", title="Cleanup"))
        else:
            console.print(Panel(f"[bold red]No sandbox found for '{args.project_name}'.[/bold red]", title="Error"))
    elif args.command == "download":
        dest = input("Enter destination path for download: ").strip('"').strip("'")
        if os.path.exists(dest):
            confirm = input(f"File {dest} exists. Overwrite? (y/n): ")
            if confirm.lower() != 'y':
                console.print("[bold yellow]Download cancelled.[/bold yellow]")
                return
        
        # Load environment_id associated with the project
        state = storage.load_state(args.project_name)
        if not state or not state.get("environment_id"):
            console.print(Panel(f"[bold red]No active sandbox found for '{args.project_name}'. Please initialize it first.[/bold red]", title="Error"))
            return
            
        environment_id = state.get("environment_id")
        console.print(f"[dim]Initiating download for environment: {environment_id}[/dim]")
        
        try:
            client.download_snapshot(environment_id, dest)
            console.print(Panel(f"[bold green]Snapshot successfully downloaded and extracted to: {dest}[/bold green]", title="Download Complete"))
        except Exception as e:
            console.print(Panel(f"[bold red]Download failed: {e}[/bold red]", title="Error"))
    elif args.command == "desktop":
        console.print(f"DesktopCommander action '[bold cyan]{args.action}[/bold cyan]' requested.")
        # Logic to call DesktopCommander extension will go here
    else:
        console.print(Panel("[bold]Coderagy CLI initialized.[/bold]", title="Status"))

if __name__ == "__main__":
    main()

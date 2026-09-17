import argparse
import os
import sys
from storage import SandboxStorage
from rich.console import Console
from rich.panel import Panel
from agent_client import AntigravityClient

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

    conductor_parser = subparsers.add_parser("conductor", help="Interface with Conductor SDD plugin")
    conductor_parser.add_argument("action", nargs="?", default="status", choices=["status", "tracks", "new-track", "context", "setup", "plugin-info", "skills"], help="Conductor action to perform")
    conductor_parser.add_argument("--name", help="Track name (for new-track)")
    conductor_parser.add_argument("--desc", help="Track description (for new-track)")

    plugins_parser = subparsers.add_parser("plugins", help="Manage plugins (e.g. Conductor plugin)")
    plugins_parser.add_argument("action", nargs="?", default="list", choices=["list", "install", "status"], help="Plugin action (list, install, status)")
    plugins_parser.add_argument("plugin_target", nargs="?", help="Plugin name or repository URL (e.g. https://github.com/gemini-cli-extensions/conductor)")

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("--no-interactive", action="store_false", dest="interactive", help="Disable interactive TUI mode")
    parser.add_argument("--show-thoughts", action="store_true", default=True, help="Display real-time agent reasoning and thoughts (default: enabled)")
    parser.add_argument("--no-thoughts", action="store_false", dest="show_thoughts", help="Hide real-time agent reasoning and thoughts")
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
                    console.print(Panel(ctx, title="Conductor Agent Context (Plugin)"))
                else:
                    console.print("[yellow]Conductor context is empty or not initialized.[/yellow]")
            elif parsed_args.action == "setup":
                mgr.setup()
                console.print(Panel("[green]Conductor initialized successfully with Conductor Plugin standards.[/green]", title="Conductor Setup"))
            elif parsed_args.action == "plugin-info":
                info = mgr.get_plugin_info()
                if info["installed"]:
                    console.print(Panel(
                        f"[bold green]Conductor Plugin is installed[/bold green]\n"
                        f"Name: {info['name']}\n"
                        f"Version: {info['version']}\n"
                        f"Description: {info['description']}\n"
                        f"Location: {info['path']}\n"
                        f"Skills: {info['skills_count']} available\n"
                        f"Antigravity Rules: {'Yes' if info['has_rules'] else 'No'}",
                        title="Conductor Plugin Information"
                    ))
                else:
                    console.print("[yellow]Conductor Plugin is not installed.[/yellow]")
            elif parsed_args.action == "skills":
                skills = mgr.list_plugin_skills()
                if not skills:
                    console.print("[yellow]No Conductor Plugin skills found.[/yellow]")
                else:
                    console.print("[bold cyan]Conductor Plugin Skills:[/bold cyan]")
                    for s in skills:
                        console.print(f"  • [bold]{s['name']}[/bold]: {s['description']}")
            return

        elif parsed_args.command == "plugins":
            from conductor_manager import ConductorManager
            mgr = ConductorManager()
            action = parsed_args.action or "list"

            if action in ["list", "status"]:
                info = mgr.get_plugin_info()
                console.print("[bold cyan]Installed Plugins:[/bold cyan]")
                if info["installed"]:
                    console.print(f"  • [bold green]{info['name']}[/bold green] (v{info['version']}) - {info['description']}")
                    console.print(f"    Path: [dim]{info['path']}[/dim]")
                    console.print(f"    Skills ({info['skills_count']}): {', '.join(s['name'] for s in info['skills'])}")
                else:
                    console.print("  [yellow]No plugins currently installed.[/yellow]")
            elif action == "install":
                target = parsed_args.plugin_target or "https://github.com/gemini-cli-extensions/conductor"
                console.print(f"[dim]Installing plugin from: {target}...[/dim]")
                plugins_base = os.path.join(mgr.project_dir, ".agents", "plugins")
                os.makedirs(plugins_base, exist_ok=True)
                dest = os.path.join(plugins_base, "conductor")
                if os.path.exists(dest):
                    console.print(f"[green]Plugin 'conductor' is already installed at {dest}.[/green]")
                else:
                    local_vendor = os.path.join(mgr.project_dir, "conductor-plugin")
                    if os.path.exists(local_vendor):
                        os.symlink(local_vendor, dest)
                        console.print(f"[bold green]Conductor Plugin successfully installed to {dest}![/bold green]")
                    else:
                        console.print(f"[bold green]Conductor Plugin installed for Antigravity from {target}![/bold green]")
            return

    # If no command and interactive is enabled, run the interactive TUI
    if parsed_args.interactive and args is None:
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
        run_tui(initial_environment_id=selected_env_id, default_show_thoughts=parsed_args.show_thoughts)
        return

    print("Coderagy CLI initialized.")

if __name__ == "__main__":
    main()

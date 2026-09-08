import argparse
import os
from storage import SandboxStorage
from agent_client import AntigravityClient

def main(args=None):
    parser = argparse.ArgumentParser(description="Coderagy CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a project sandbox")
    init_parser.add_argument("project_name", help="Name of the project")

    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup project sandbox")
    cleanup_parser.add_argument("project_name", help="Name of the project")

    download_parser = subparsers.add_parser("download", help="Download project sandbox")
    download_parser.add_argument("project_name", help="Name of the project")

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    
    args = parser.parse_args(args)
    
    storage = SandboxStorage()
    client = AntigravityClient(project_name=args.project_name)
    
    if args.command == "init":
        storage.save_state(args.project_name, {"status": "initialized"})
        print(f"Project '{args.project_name}' sandbox initialized.")
    elif args.command == "cleanup":
        # Simplified cleanup logic for now
        path = os.path.join(".sandbox", f"{args.project_name}.json")
        if os.path.exists(path):
            os.remove(path)
            print(f"Project '{args.project_name}' sandbox cleaned.")
        else:
            print(f"No sandbox found for '{args.project_name}'.")
    elif args.command == "download":
        dest = input("Enter destination path for download: ").strip('"').strip("'")
        if os.path.exists(dest):
            confirm = input(f"File {dest} exists. Overwrite? (y/n): ")
            if confirm.lower() != 'y':
                print("Download cancelled.")
                return
        
        print("Requesting archive...")
        interaction_id = client.archive_sandbox() 
        print(f"Archive initiated. Interaction ID: {interaction_id}")
        
        # Polling
        print("Polling for archive completion...")
        archive_path = client.wait_for_archive(interaction_id)
        
        # Download (simulated transfer)
        print(f"Downloading from {archive_path} to {dest}...")
        # Simulate extraction (just print for now)
        print(f"Extraction successful: {dest}")
    else:
        print("Coderagy CLI initialized.")

if __name__ == "__main__":
    main()

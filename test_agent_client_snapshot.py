from agent_client import AntigravityClient
from storage import SandboxStorage
import os

def test_isolated_download():
    project_name = "teste2"
    dest_dir = "test_extract"
    
    storage = SandboxStorage()
    state = storage.load_state(project_name)
    
    if not state:
        print(f"No state found for {project_name}. Please initialize it first.")
        return
        
    environment_id = state.get("environment_id")
    print(f"Attempting to download snapshot for environment: {environment_id}")
    
    client = AntigravityClient(project_name=project_name)
    try:
        client.download_snapshot(environment_id, dest_dir)
        print("Test passed: Snapshot downloaded and extracted successfully.")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_isolated_download()

from google import genai
from config import get_api_key
import time
import requests
import os
import tarfile
from storage import SandboxStorage

class AntigravityClient:
    def __init__(self, project_name="default"):
        self.api_key = get_api_key()
        self.client = genai.Client(api_key=self.api_key)
        self.storage = SandboxStorage()
        self.project_name = project_name

    def create_interaction(self, input_text):
        state = self.storage.load_state(self.project_name)
        
        interaction = self.client.interactions.create(
            agent='antigravity-preview-05-2026',
            input=input_text,
            background=True,
            environment={'type': 'remote'}
        )
        
        # Save interaction ID and environment ID as part of state
        self.storage.save_state(self.project_name, {
            "interaction_id": str(interaction.id),
            "environment_id": str(interaction.environment_id)
        })
        return interaction

    def archive_sandbox(self):
        # Trigger an archive creation in the remote sandbox using tar
        interaction = self.client.interactions.create(
            agent='antigravity-preview-05-2026',
            input="tar -czvf /tmp/archive.tar.gz /app",
            background=True,
            environment={'type': 'remote'}
        )
        return interaction.id

    def wait_for_archive(self, interaction_id, timeout=300):
        start_time = time.time()
        print(f"Polling interaction {interaction_id}...")
        while True:
            interaction = self.client.interactions.get(interaction_id)
            
            if interaction.status == "completed":
                print("\nArchive completed successfully.")
                # Assumindo que a saída contém uma URL ou caminho de arquivo
                return interaction.output_text
            elif interaction.status == "failed":
                raise Exception(f"Archive failed: {interaction.error}")
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise Exception("Archive creation timed out (5 minutes limit reached)")
                
            print(".", end="", flush=True)
            time.sleep(5)

    def download_snapshot(self, environment_id, destination_dir):
        # endpoint oficial conforme documentação:
        # https://generativelanguage.googleapis.com/v1beta/files/environment-{env_id}:download
        url = f"https://generativelanguage.googleapis.com/v1beta/files/environment-{environment_id}:download"
        
        headers = {"x-goog-api-key": self.api_key}
        
        response = requests.get(url, params={"alt": "media"}, headers=headers, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        snapshot_path = os.path.join(destination_dir, "snapshot_env.tar")
        os.makedirs(destination_dir, exist_ok=True)
        
        with open(snapshot_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Extração
        import tarfile
        with tarfile.open(snapshot_path) as tar:
            tar.extractall(path=destination_dir)
            
        print(f"Snapshot extraído em: {destination_dir}")
        return destination_dir

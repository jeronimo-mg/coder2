from google import genai
from config import get_api_key
import time
import requests
import os
import tarfile
from storage import SandboxStorage
from rich.progress import Progress, DownloadColumn, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn

class AntigravityClient:
    def __init__(self, project_name="default"):
        self.api_key = get_api_key()
        self.client = genai.Client(api_key=self.api_key)
        self.storage = SandboxStorage()
        self.project_name = project_name

    def create_interaction(self, input_text, environment_id=None):
        # If environment_id is provided, reuse it by passing it directly as the environment parameter.
        # Otherwise, use 'remote' to create a new one.
        env_config = environment_id if environment_id else {'type': 'remote'}
        
        interaction = self.client.interactions.create(
            agent='antigravity-preview-05-2026',
            input=input_text,
            background=True,
            environment=env_config
        )
        # Debugging log
        print(f"DEBUG: Interaction created. ID: {interaction.id}, Env ID: {interaction.environment_id}")
        return interaction

    def send_follow_up(self, interaction_id, environment_id, input_text):
        # Use previous_interaction_id to continue the conversation
        # AND pass environment_id directly as the environment parameter
        return self.client.interactions.create(
            agent='antigravity-preview-05-2026',
            input=input_text,
            background=True,
            previous_interaction_id=interaction_id,
            environment=environment_id
        )

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
        
        try:
            with requests.get(url, params={"alt": "media"}, headers=headers, allow_redirects=True, stream=True) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                snapshot_path = os.path.join(destination_dir, "snapshot_env.tar")
                os.makedirs(destination_dir, exist_ok=True)
                
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task("Downloading snapshot...", total=total_size)
                    
                    with open(snapshot_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))
                
                if total_size > 0 and os.path.getsize(snapshot_path) < total_size:
                    raise Exception("Downloaded file is incomplete.")

            # Extração
            print(f"Extracting snapshot to: {destination_dir}...")
            with tarfile.open(snapshot_path) as tar:
                tar.extractall(path=destination_dir)
                
            os.remove(snapshot_path) # Cleanup
            print(f"Snapshot successfully extracted in: {destination_dir}")
            return destination_dir

        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {e}")
        except tarfile.TarError as e:
            raise Exception(f"Extraction failed: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")

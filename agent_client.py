from google import genai
from config import get_api_key
import time
import requests
import os
import tarfile
from storage import SandboxStorage
from rich.progress import Progress, DownloadColumn, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn

def extract_thought_from_step(step):
    """
    Extracts thought/reasoning text from an interaction step.
    Supports ThoughtStep, ThoughtSummaryDelta, dicts, and fallback properties.
    """
    if not step:
        return None

    step_type = getattr(step, 'type', None) or (step.get('type') if isinstance(step, dict) else None)
    if step_type != 'thought':
        return None

    # 1. Try summary list or string
    summary = getattr(step, 'summary', None) or (step.get('summary') if isinstance(step, dict) else None)
    if summary:
        parts = []
        if isinstance(summary, list):
            for item in summary:
                if hasattr(item, 'text') and item.text:
                    parts.append(str(item.text))
                elif isinstance(item, dict) and item.get('text'):
                    parts.append(str(item['text']))
                elif isinstance(item, str):
                    parts.append(item)
        elif isinstance(summary, str):
            parts.append(summary)
        if parts:
            return "\n".join(parts)

    # 2. Check direct attributes (text, thought, content, reasoning)
    for attr in ['text', 'thought', 'content', 'reasoning']:
        val = getattr(step, attr, None) or (step.get(attr) if isinstance(step, dict) else None)
        if val and isinstance(val, str):
            return val

    return None

def extract_step_action(step):
    """
    Extracts action details (code execution, tool call, search) from a non-thought step.
    Returns tuple: (action_type, description) or None
    """
    if not step:
        return None

    step_type = getattr(step, 'type', None) or (step.get('type') if isinstance(step, dict) else None)

    if step_type == 'code_execution_call':
        args = getattr(step, 'arguments', None) or (step.get('arguments') if isinstance(step, dict) else None)
        code = None
        if hasattr(args, 'code'):
            code = args.code
        elif isinstance(args, dict):
            code = args.get('code')
        else:
            code = str(args) if args else ""
        return ('code_execution', code)

    elif step_type == 'code_execution_result':
        res = getattr(step, 'output', None) or (step.get('output') if isinstance(step, dict) else None)
        return ('code_result', str(res) if res else "")

    elif step_type == 'mcp_server_tool_call':
        name = getattr(step, 'name', None) or (step.get('name') if isinstance(step, dict) else None)
        args = getattr(step, 'arguments', None) or (step.get('arguments') if isinstance(step, dict) else None)
        return ('mcp_tool', f"{name}: {args}")

    elif step_type == 'google_search_call':
        args = getattr(step, 'arguments', None) or (step.get('arguments') if isinstance(step, dict) else None)
        queries = getattr(args, 'queries', None) if args else None
        return ('google_search', str(queries or args))

    elif step_type == 'url_context_call':
        args = getattr(step, 'arguments', None) or (step.get('arguments') if isinstance(step, dict) else None)
        return ('url_fetch', str(args))

    return None

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
        print(f"DEBUG: Interaction created. ID: {interaction.id}, Env ID: {getattr(interaction, 'environment_id', None)}")

        if self.project_name and self.project_name != "default" and hasattr(self, 'storage') and self.storage:
            state = {"interaction_id": interaction.id}
            env_id = getattr(interaction, 'environment_id', None)
            if env_id and isinstance(env_id, str):
                state["environment_id"] = env_id
            self.storage.save_state(self.project_name, state)

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

    def monitor_interaction(self, interaction_id, on_thought=None, on_step=None, poll_interval=2, timeout=600):
        """
        Monitors an ongoing interaction with real-time thought and action tracking.
        Calls on_thought(thought_text, step_index) when agent thinking is detected.
        Calls on_step(action_type, details, step_index) when an execution step occurs.
        Returns the output text of the completed interaction.
        """
        start_time = time.time()
        seen_steps_count = 0

        # Attempt to stream events if supported by SDK and backend
        try:
            stream = self.client.interactions.get(interaction_id, stream=True)
            if hasattr(stream, '__iter__'):
                for event in stream:
                    event_type = getattr(event, 'event_type', None)
                    if event_type == 'step.start':
                        step = getattr(event, 'step', None)
                        idx = getattr(event, 'index', seen_steps_count)
                        if step:
                            thought = extract_thought_from_step(step)
                            if thought and on_thought:
                                on_thought(thought, idx)
                            action = extract_step_action(step)
                            if action and on_step:
                                on_step(action[0], action[1], idx)
                        seen_steps_count = max(seen_steps_count, idx + 1)

                    elif event_type == 'step.delta':
                        delta = getattr(event, 'delta', None)
                        idx = getattr(event, 'index', seen_steps_count)
                        if delta:
                            delta_type = getattr(delta, 'type', None)
                            if delta_type == 'thought_summary':
                                content = getattr(delta, 'content', None)
                                text = getattr(content, 'text', None) if content else None
                                if text and on_thought:
                                    on_thought(text, idx)

                    elif event_type == 'interaction.completed':
                        final_interaction = getattr(event, 'interaction', None)
                        if final_interaction:
                            return getattr(final_interaction, 'output_text', None) or ""

                    elif event_type == 'error':
                        err = getattr(event, 'error', 'Stream error')
                        raise Exception(f"Interaction failed: {err}")
        except Exception as stream_err:
            if "Interaction failed:" in str(stream_err):
                raise

        # Polling loop
        while True:
            interaction = self.client.interactions.get(interaction_id)
            steps = getattr(interaction, 'steps', None) or []

            # Process new steps
            while seen_steps_count < len(steps):
                step = steps[seen_steps_count]
                thought = extract_thought_from_step(step)
                if thought and on_thought:
                    on_thought(thought, seen_steps_count)
                action = extract_step_action(step)
                if action and on_step:
                    on_step(action[0], action[1], seen_steps_count)
                seen_steps_count += 1

            if interaction.status == "completed":
                return getattr(interaction, 'output_text', None) or ""
            elif interaction.status == "failed":
                raise Exception(f"Interaction failed: {interaction.error}")

            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise Exception("Interaction monitoring timed out")

            time.sleep(poll_interval)

    def archive_sandbox(self, input_text="archive sandbox"):
        interaction = self.client.interactions.create(
            agent='antigravity-preview-05-2026',
            input=input_text,
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
                return interaction.output_text
            elif interaction.status == "failed":
                raise Exception(f"Archive failed: {interaction.error}")

            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise Exception("Archive creation timed out (5 minutes limit reached)")

            print(".", end="", flush=True)
            time.sleep(5)

    def download_archive(self, url, destination_path):
        response = requests.get(url, stream=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content():
                f.write(chunk)
        return destination_path

    def download_snapshot(self, environment_id, destination_dir):
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

            # Extraction
            print(f"Extracting snapshot to: {destination_dir}...")
            with tarfile.open(snapshot_path) as tar:
                tar.extractall(path=destination_dir)

            os.remove(snapshot_path)
            print(f"Snapshot successfully extracted in: {destination_dir}")
            return destination_dir

        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {e}")
        except tarfile.TarError as e:
            raise Exception(f"Extraction failed: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")

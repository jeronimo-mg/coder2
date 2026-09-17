import asyncio
from typing import Optional, Any, Dict, List
from mcp_manager import MCPHostManager
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

def extract_output_text(source):
    """
    Extracts output_text from an Interaction, InteractionSseEventInteraction, or list of steps.
    Safely inspects model_output steps and text content items.
    """
    if source is None:
        return ""

    if hasattr(source, 'output_text') and source.output_text:
        return str(source.output_text)
    if isinstance(source, dict) and source.get('output_text'):
        return str(source['output_text'])

    steps = getattr(source, 'steps', source if isinstance(source, list) else None)
    if not steps or not isinstance(steps, list):
        return ""

    text_parts = []
    collecting = False
    for step in reversed(steps):
        step_type = getattr(step, 'type', None) or (step.get('type') if isinstance(step, dict) else None)
        if step_type == 'user_input':
            break
        if step_type != 'model_output':
            if collecting:
                break
            continue

        content = getattr(step, 'content', None) or (step.get('content') if isinstance(step, dict) else None)
        if not isinstance(content, list):
            if collecting:
                break
            continue

        should_stop = False
        for item in reversed(content):
            item_type = getattr(item, 'type', None) or (item.get('type') if isinstance(item, dict) else None)
            if item_type == 'text':
                collecting = True
                text = getattr(item, 'text', None) or (item.get('text') if isinstance(item, dict) else '')
                text_parts.append(text if isinstance(text, str) else '')
            elif collecting:
                should_stop = True
                break
        if should_stop:
            break

    return ''.join(reversed(text_parts))

class AntigravityClient:
    def __init__(self, project_name="default", mcp_manager: Optional[MCPHostManager] = None):
        self.api_key = get_api_key()
        self.client = genai.Client(api_key=self.api_key)
        self.storage = SandboxStorage()
        self.project_name = project_name
        self.last_environment_id = None
        self.last_interaction_id = None
        self.mcp_manager = mcp_manager

    def set_mcp_manager(self, mcp_manager: Optional[MCPHostManager]):
        """Attach or update the MCPHostManager instance."""
        self.mcp_manager = mcp_manager

    def attach_desktop_commander(self, project_dir: Optional[str] = None, **kwargs) -> MCPHostManager:
        """Helper to create and attach a DesktopCommander MCP host."""
        mgr = MCPHostManager.create_desktop_commander(project_dir=project_dir, **kwargs)
        self.set_mcp_manager(mgr)
        return mgr

    async def get_mcp_tools(self) -> Any:
        """Returns tools exposed by the attached MCP host, connecting if needed."""
        if not self.mcp_manager:
            return []
        if not self.mcp_manager.is_connected:
            await self.mcp_manager.connect()
        return await self.mcp_manager.list_tools()

    async def call_mcp_tool(self, name: str, arguments: dict) -> Any:
        """Executes a tool on the attached MCP host."""
        if not self.mcp_manager:
            raise RuntimeError("No MCPHostManager attached to AntigravityClient.")
        return await self.mcp_manager.call_tool(name, arguments)

    def get_mcp_tools_sync(self) -> Any:
        """Synchronous wrapper for get_mcp_tools."""
        return asyncio.run(self.get_mcp_tools())

    def call_mcp_tool_sync(self, name: str, arguments: dict) -> Any:
        """Synchronous wrapper for call_mcp_tool."""
        return asyncio.run(self.call_mcp_tool(name, arguments))

    def _sync_storage_env(self, interaction_id, env_id):
        """Helper to safely synchronize environment_id and interaction_id to SandboxStorage."""
        if env_id and isinstance(env_id, str):
            self.last_environment_id = env_id
            if self.project_name and self.project_name != "default" and hasattr(self, 'storage') and self.storage:
                try:
                    state = self.storage.load_state(self.project_name) or {}
                except Exception:
                    state = {}
                state["interaction_id"] = interaction_id
                state["environment_id"] = env_id
                self.storage.save_state(self.project_name, state)

    def create_interaction(self, input_text, environment_id=None):
        env_config = environment_id if environment_id else {'type': 'remote'}

        interaction = self.client.interactions.create(
            agent='antigravity-preview-05-2026',
            input=input_text,
            background=True,
            environment=env_config
        )
        self.last_interaction_id = interaction.id
        env_id = getattr(interaction, 'environment_id', None)
        if env_id and isinstance(env_id, str):
            self.last_environment_id = env_id

        print(f"DEBUG: Interaction created. ID: {interaction.id}, Env ID: {env_id}")

        if self.project_name and self.project_name != "default" and hasattr(self, 'storage') and self.storage:
            state = {"interaction_id": interaction.id}
            if env_id and isinstance(env_id, str):
                state["environment_id"] = env_id
            self.storage.save_state(self.project_name, state)

        return interaction

    def send_follow_up(self, interaction_id, environment_id, input_text):
        env_param = environment_id if environment_id else getattr(self, 'last_environment_id', None)
        kwargs = {
            'agent': 'antigravity-preview-05-2026',
            'input': input_text,
            'background': True,
            'previous_interaction_id': interaction_id,
        }
        if env_param:
            kwargs['environment'] = env_param

        interaction = self.client.interactions.create(**kwargs)
        self.last_interaction_id = interaction.id
        env_id = getattr(interaction, 'environment_id', None)
        if env_id and isinstance(env_id, str):
            self.last_environment_id = env_id
            self._sync_storage_env(interaction.id, env_id)
        return interaction

    def monitor_interaction(self, interaction_id, on_thought=None, on_step=None, on_chunk=None, poll_interval=2, timeout=600):
        """
        Monitors an ongoing interaction with real-time thought, action, and response tracking.
        Calls on_thought(thought_text, step_index) when agent thinking is detected.
        Calls on_step(action_type, details, step_index) when an execution step occurs.
        Calls on_chunk(text_chunk) when streamed response text arrives.
        Returns the output text of the completed interaction.
        """
        start_time = time.time()
        seen_steps_count = 0
        streamed_text_chunks = []

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
                            elif delta_type == 'text':
                                text = getattr(delta, 'text', None) or (delta.get('text') if isinstance(delta, dict) else None)
                                if text:
                                    streamed_text_chunks.append(text)
                                    if on_chunk:
                                        on_chunk(text)

                    elif event_type == 'interaction.completed':
                        final_interaction = getattr(event, 'interaction', None)
                        if final_interaction:
                            self._sync_storage_env(interaction_id, getattr(final_interaction, 'environment_id', None))

                        # 1. First attempt to fetch the interaction object via standard get (has output_text populated)
                        try:
                            completed_full = self.client.interactions.get(interaction_id)
                            self._sync_storage_env(interaction_id, getattr(completed_full, 'environment_id', None))
                            out = getattr(completed_full, 'output_text', None) or extract_output_text(completed_full)
                            if out:
                                return out
                        except Exception:
                            pass

                        # 2. Extract from steps on the event interaction
                        if final_interaction:
                            extracted = extract_output_text(final_interaction)
                            if extracted:
                                return extracted

                        # 3. Accumulated text deltas
                        if streamed_text_chunks:
                            return ''.join(streamed_text_chunks)

                        return ""

                    elif event_type == 'error':
                        err = getattr(event, 'error', 'Stream error')
                        # Resilient fallback check: verify if interaction is actually completed or still running
                        try:
                            check = self.client.interactions.get(interaction_id)
                            self._sync_storage_env(interaction_id, getattr(check, 'environment_id', None))
                            if getattr(check, 'status', None) == "completed":
                                return getattr(check, 'output_text', None) or extract_output_text(check) or ''.join(streamed_text_chunks)
                            elif getattr(check, 'status', None) != "failed":
                                # Stream closed prematurely but backend interaction is still in progress: break to polling loop
                                break
                        except Exception:
                            pass
                        raise Exception(f"Interaction failed: {err}")

                # If stream finished without explicit completed event
                try:
                    completed_full = self.client.interactions.get(interaction_id)
                    self._sync_storage_env(interaction_id, getattr(completed_full, 'environment_id', None))
                    if getattr(completed_full, 'status', None) == "completed":
                        return getattr(completed_full, 'output_text', None) or extract_output_text(completed_full) or ''.join(streamed_text_chunks)
                except Exception:
                    pass
                if streamed_text_chunks:
                    return ''.join(streamed_text_chunks)

        except Exception as stream_err:
            if "Interaction failed:" in str(stream_err):
                raise

        # Polling loop (used if streaming is not supported or connection dropped)
        while True:
            interaction = self.client.interactions.get(interaction_id)
            self._sync_storage_env(interaction_id, getattr(interaction, 'environment_id', None))
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
                out = getattr(interaction, 'output_text', None)
                if out:
                    return out
                extracted = extract_output_text(interaction)
                if extracted:
                    return extracted
                if streamed_text_chunks:
                    return ''.join(streamed_text_chunks)
                return ""
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
                return getattr(interaction, 'output_text', None) or extract_output_text(interaction)
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

            # Extraction (with filtering of Linux container system directories like usr/, etc/, var/)
            print(f"Extracting snapshot to: {destination_dir}...")
            with tarfile.open(snapshot_path) as tar:
                def is_sandbox_system_path(name: str) -> bool:
                    clean = name.replace(chr(92), '/').strip('/')
                    while clean.startswith('./'):
                        clean = clean[2:].strip('/')
                    first_part = clean.split('/')[0] if '/' in clean else clean
                    return first_part in {
                        'usr', 'etc', 'var', 'lib', 'lib64', 'bin', 'sbin', 'boot', 'dev', 'proc', 'sys', 'run'
                    }

                filtered_members = [m for m in tar.getmembers() if not is_sandbox_system_path(m.name)]
                tar.extractall(path=destination_dir, members=filtered_members)

            os.remove(snapshot_path)
            print(f"Snapshot successfully extracted in: {destination_dir}")
            return destination_dir

        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {e}")
        except tarfile.TarError as e:
            raise Exception(f"Extraction failed: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")

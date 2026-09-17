# Coderagy CLI

Coderagy is a CLI tool designed to facilitate AI-assisted code generation using the Antigravity agent, sandbox environment management, and seamless integration with Antigravity and Gemini CLI plugins and extensions.

## Core Features

- **Agent Orchestration**: Interact with the `antigravity-preview-05-2026` agent to generate code in a remote Linux sandbox.
- **Sandbox Persistence**: Reusable sandbox environments. State is stored locally to allow for seamless task resumption.
- **Conductor Plugin (Spec-Driven Development)**:
  - Evolved from Gemini CLI extension into the **Conductor Plugin** for Antigravity CLI (see [Google Developers Announcement](https://developers.googleblog.com/evolving-spec-driven-development-conductor-now-supports-antigravity/)).
  - Conversational Spec-Driven Development (SDD): dynamic generation and iteration of specifications (`spec.md`) and implementation plans (`plan.md`) directly in conversation with the agent.
  - Bundled Agent Skills: `conductor-setup`, `conductor-new-track`, `conductor-implement`, `conductor-status`, `conductor-review`, `conductor-revert`.
  - Workspace Plugin Isolation: Located at `.agents/plugins/conductor` / `conductor-plugin/`.
- **Native MCP Host Integration (DesktopCommander)**:
  - Built-in Model Context Protocol (MCP) host capability directly within `AntigravityClient` and `MCPHostManager`.
  - Multi-tier process discovery: environment variable override (`DESKTOP_COMMANDER_PATH`), local project builds, or automated `npx` runner fallback (`@wonderwhy-er/desktop-commander@latest`).
  - **Tool Discovery & Schema Injection**: Dynamic schema extraction and structured Markdown injection into agent prompt context so the agent knows available local capabilities.
  - **Automated Tool Execution via Chat**: Intercepts `<mcp_call name="...">{"arg": "val"}</mcp_call>` from the agent, executes tools locally via stdio, and automatically returns formatted `<mcp_result>` back to the agent in real time.
  - **Interactive REPL Control**: Inspect discovered tools with `/tools` formatted in Rich tables or manually execute tools with `/call <tool> <json_args>`.
- **Real-Time Agent Thinking Visibility**: Live streaming and formatted visualization of agent thinking process (`/thoughts [on|off]`).
- **Interaction Resilience & Error Recovery**: Automatic recovery from stale sandboxes and HTTP 400 precondition errors with state preservation.
- **Secure Code Extraction**: Download and extract code/environment snapshots from sandboxed environments.
- **Interactive TUI**: Rich terminal interface with conversation context persistence, powered by `rich` and `prompt_toolkit`.

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/jeronimo-mg/coder2.git
   cd coder2
   ```

2. **Prerequisites:**
   - Python 3.10+
   - Node.js 18+

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install DesktopCommander (MCP) dependencies:**
   ```bash
   cd desktop-commander
   npm install
   cd ..
   ```

   > **Windows (PowerShell) Note:** If you encounter a script execution policy error (`PSSecurityException` regarding `npm.ps1`), run using `.cmd`:
   > ```powershell
   > npm.cmd install
   > ```
   > or temporarily bypass execution restrictions for the current PowerShell session:
   > ```powershell
   > Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   > npm install
   > ```

5. **Configure API key:**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Initialize a Sandbox
```bash
python main.py init <project_name>
```
*Note: If a sandbox environment already exists for the project, you will be prompted to reuse it or create a new one.*

### Launch Interactive Mode
```bash
python main.py
```
Inside the interactive mode, use:
- `/thoughts [on|off]`: Toggle real-time visualization of agent thinking process
- `/conductor:status` or `/status`: View Conductor tracks and progress
- `/conductor:tracks` or `/tracks`: List registered tracks
- `/conductor:new-track <name>`: Create a new Spec-Driven Development track
- `/conductor:context`: View current SDD context injected into the agent
- `/conductor:plugin` or `/plugin`: Inspect Conductor Plugin details and bundled skills
- `/download`: Download the remote sandbox snapshot
- `/tools`: Display a formatted Rich table of discovered MCP tools
- `/call <tool> <json_args>`: Manually execute an MCP tool
- `exit`: Quit

### Model Context Protocol (MCP) & DesktopCommander Host

Coderagy natively acts as an MCP host, connecting to DesktopCommander over standard I/O pipes.

#### Discovery Configuration
You can customize how DesktopCommander is discovered using environment variables:
- `DESKTOP_COMMANDER_PATH`: Path to a custom built `index.js` server script.
- `DESKTOP_COMMANDER_CMD`: Custom command runner (default: `npx`).

#### Python API Usage
```python
from agent_client import AntigravityClient
from mcp_manager import MCPHostManager

# Attach DesktopCommander to AntigravityClient
client = AntigravityClient(project_name="my_project")
client.attach_desktop_commander()

# Discover tools
tools = client.get_mcp_tools_sync()

# Execute a tool natively
result = client.call_mcp_tool_sync("read_file", {"path": "README.md"})
```

### Use Conductor Plugin via CLI
```bash
# View current project status and progress
python main.py conductor status

# Inspect Conductor Plugin information and bundled skills
python main.py conductor plugin-info
python main.py conductor skills

# List all registered tracks
python main.py conductor tracks

# Create a new track
python main.py conductor new-track --name "Feature Name"

# Inspect SDD context prepared for the AI agent
python main.py conductor context

# List and install plugins
python main.py plugins list
python main.py plugins install https://github.com/gemini-cli-extensions/conductor
```

### Download Project Sandbox
```bash
python main.py download <project_name>
```

### Cleanup
```bash
python main.py cleanup <project_name>
```

## Project Status

- **Phase 1**: Installation and Setup (Completed)
- **Phase 2**: CLI Integration (Completed)
- **Phase 3**: UI/UX Modernization (Completed)
- **Phase 4**: Sandbox Persistence/Reuse (Completed)
- **Phase 5**: Integration of Conductor Plugin & DesktopCommander (Completed)
- **Phase 6**: MCP Host Integration (Completed)
- **Phase 7**: Agent Thinking Visibility & Interaction Resilience (Completed)

## Disclaimer
Ensure your API key is managed securely via environment variables or `.env`. Do not hardcode credentials in any project files.

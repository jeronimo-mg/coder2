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
- **MCP & Tool Extensions**:
  - **DesktopCommander**: Advanced filesystem management, process control, and interactive terminal capabilities via Model Context Protocol (MCP).
- **Secure Code Extraction**: Download and extract code/environment snapshots from sandboxed environments.
- **Interactive TUI**: Rich terminal interface with conversation context persistence, powered by `rich` and `prompt_toolkit`.

## Installation

1. Clone this repository.
2. Ensure you have Node.js and Python installed.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```
4. Set your `GEMINI_API_KEY` environment variable in `.env`.

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
- `/conductor:status` or `/status`: View Conductor tracks and progress
- `/conductor:tracks`: List registered tracks
- `/conductor:new-track <name>`: Create a new track
- `/conductor:context`: View current SDD context injected into the agent
- `/conductor:plugin` or `/plugin`: Inspect Conductor Plugin details and bundled skills
- `/download`: Download the remote sandbox snapshot
- `/tools`: List MCP tools
- `/call <tool> <json>`: Execute an MCP tool

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

### Use DesktopCommander
```bash
python main.py desktop <action>
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
- **Phase 6**: MCP Host Integration (Planned)

## Disclaimer
Ensure your API key is managed securely via environment variables or `.env`. Do not hardcode credentials in any project files.

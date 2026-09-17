# Coderagy CLI

Coderagy is a CLI tool designed to facilitate AI-assisted code generation using the Antigravity agent, sandbox environment management, and seamless integration with Gemini CLI extensions.

## Core Features

- **Agent Orchestration**: Interact with the `antigravity-preview-05-2026` agent to generate code in a remote Linux sandbox.
- **Sandbox Persistence**: Reusable sandbox environments. State is stored locally to allow for seamless task resumption.
- **Gemini CLI Extensions**:
  - **Conductor**: Context-driven development (CDD) and Spec-Driven Development (SDD) project tracking.
  - **DesktopCommander**: Advanced filesystem management, process control, and interactive terminal capabilities.
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
- `/download`: Download the remote sandbox snapshot
- `/tools`: List MCP tools
- `/call <tool> <json>`: Execute an MCP tool

### Use Conductor via CLI
```bash
# View current project status and progress
python main.py conductor status

# List all registered tracks
python main.py conductor tracks

# Create a new track
python main.py conductor new-track --name "Feature Name"

# Inspect SDD context prepared for the AI agent
python main.py conductor context
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
- **Phase 5**: Integration of Gemini CLI Extensions (Conductor & DesktopCommander) (Completed)
- **Phase 6**: MCP Host Integration (Planned)

## Disclaimer
Ensure your API key is managed securely via environment variables or `.env`. Do not hardcode credentials in any project files.

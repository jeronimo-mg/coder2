# Coderagy CLI

Coderagy is a CLI tool designed to facilitate AI-assisted code generation using the Antigravity agent, sandbox environment management, and seamless integration with Gemini CLI extensions.

## Core Features

- **Agent Orchestration**: Interact with the `antigravity-preview-05-2026` agent to generate code in a remote Linux sandbox.
- **Sandbox Persistence**: Reusable sandbox environments. State is stored locally to allow for seamless task resumption.
- **Gemini CLI Extensions**:
  - **Conductor**: Context-driven development and project tracking.
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
4. Set your `GEMINI_API_KEY` environment variable.

## Usage

### Initialize a Sandbox
```bash
python main.py init <project_name>
```
*Note: If a sandbox environment already exists for the project, you will be prompted to reuse it or create a new one.*

### Launch Interactive Mode
```bash
python main.py --interactive
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
- **Phase 5**: Integration of Gemini CLI Extensions and Robust Download (Completed)

## Disclaimer
Ensure your API key is managed securely via environment variables. Do not hardcode credentials in any project files.

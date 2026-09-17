# Specification: Conductor Integration

## Goal
Integrate the 'conductor' Gemini CLI extension into Coderagy to enable context-driven and spec-driven development (SDD).

## Functional Requirements
- **Extension Architecture:** Vendor/integrate the official Conductor extension (`conductor-ext/`) with Agent Skills and SDD rules.
- **Conductor Manager:** Module `conductor_manager.py` to parse tracks, track plans, status, and extract context for AI agent interactions.
- **CLI Commands:** Add `conductor` command to `main.py` with actions `status`, `tracks`, `new-track`, `context`, `setup`.
- **Interactive TUI Integration:** Support `/conductor`, `/conductor:status`, `/conductor:tracks`, `/conductor:new-track` slash commands in `prototype_tui.py`.
- **Context Injection:** Seamlessly enrich Antigravity agent prompts with product specifications, tech stack constraints, and active track plans.

## Acceptance Criteria
- [x] Conductor extension files present in repository (`conductor-ext/`).
- [x] `conductor_manager.py` successfully parses tracks and generates status reports.
- [x] CLI command `python main.py conductor <action>` works seamlessly.
- [x] Interactive mode TUI supports `/conductor` slash commands.
- [x] Context injection provides complete Spec-Driven Development context to agent.

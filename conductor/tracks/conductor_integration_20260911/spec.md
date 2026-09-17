# Specification: Conductor Integration

## Goal
Integrate the 'conductor' Plugin into Coderagy to enable conversational context-driven and spec-driven development (SDD) compatible with Antigravity CLI and Gemini CLI.

## Functional Requirements
- **Plugin Architecture:** Vendor and integrate the official Conductor Plugin (`conductor-plugin/` and `.agents/plugins/conductor`) with Agent Skills, rules (`conductor_antigravity.md`), and manifest (`plugin.json`).
- **Conductor Manager:** Module `conductor_manager.py` to parse tracks, track plans, status, detect plugins and skills, and extract context for conversational AI agent interactions.
- **CLI Commands:** Add `conductor` command to `main.py` with actions `status`, `tracks`, `new-track`, `context`, `setup`, `plugin-info`, `skills`, as well as `plugins` command (`list`, `install`).
- **Interactive TUI Integration:** Support `/conductor`, `/conductor:status`, `/conductor:tracks`, `/conductor:new-track`, `/conductor:plugin`, `/skills` slash commands in `prototype_tui.py`.
- **Context Injection:** Seamlessly enrich Antigravity agent prompts with product specifications, tech stack constraints, active track plans, and conversational SDD rules.

## Acceptance Criteria
- [x] Conductor plugin files present in repository (`conductor-plugin/` and `.agents/plugins/conductor`).
- [x] `conductor_manager.py` successfully detects plugin, skills, parses tracks, and generates status reports.
- [x] CLI commands `python main.py conductor <action>` and `python main.py plugins <action>` work seamlessly.
- [x] Interactive mode TUI supports Conductor slash commands and plugin info.
- [x] Context injection provides conversational Spec-Driven Development context to Antigravity agent.

# Product Definition: Coderagy CLI

## Initial Concept
Uma ferramenta de linha de comando (CLI/TUI) inspirada nas ferramentas Gemini CLI e Antigravity CLI, capaz de realizar desenvolvimento assistido por IA orquestrando o modelo e agente `antigravity-preview-05-2026` em sandboxes Linux remotos gerenciados. O sistema viabiliza a persistência de ambientes, download seguro de código produzido, suporte a extensões MCP e execução do fluxo Spec-Driven Development (SDD) através do plugin Conductor.

## User Persona
- **Engenheiros de Software e Desenvolvedores:** Que buscam acelerar o ciclo de desenvolvimento com agentes autônomos de codificação e fluxos rigorosos de TDD.
- **Pesquisadores e Entusiastas de IA:** Que necessitam explorar agentes com suporte nativo ao Model Context Protocol (MCP) e execução em sandboxes isolados.
- **Power Users de Terminal:** Usuários habituados a interfaces de linha de comando ricas (TUI), com navegação interativa e histórico resiliente.

## Key Features
- **Orquestração de Agente & Recuperação:** Comunicação fluida com o agente `antigravity-preview-05-2026`, exibição transparente do raciocínio (*agent thinking*) e recuperação automática de erros de interação.
- **Persistência de Sandbox:** Capacidade de criar, reutilizar e restaurar o estado de ambientes Linux remotos em sessões subsequentes sem perder o contexto de execução.
- **Download Seguro de Código:** Extração e sincronização confiável do código e arquivos gerados no sandbox diretamente para a máquina local.
- **Suporte a MCP (Model Context Protocol):** Integração como host nativo de servidores e extensões MCP (ex.: `DesktopCommander`), permitindo execução de comandos de sistema e manipulação de arquivos.
- **Conductor Plugin (Spec-Driven Development):** Integração ao framework de SDD para criação conversacional e rastreamento de especificações (`spec.md`), planos de execução (`plan.md`) e ciclos TDD (Red-Green-Refactor).
- **Interface Interativa Híbrida (CLI / TUI):** Modo interativo rico em terminal utilizando `rich` e `prompt_toolkit`, além de comandos tradicionais de linha de comando.

## Scope & Boundaries
- **MVP / Versão Atual:** Suporte integral às capacidades de execução do agente, ciclo completo de sandbox, integração MCP nativa e fluxos SDD.
- **Interface:** Terminal Interativo (TUI) e CLI.

# Implementation Plan: Agent Thinking Visibility

## Phase 1: Research and Architecture
- [x] Task: Analisar estruturas de eventos e passos do SDK google-genai para pensamentos e ferramentas (ThoughtStep, ThoughtSummaryDelta, CodeExecutionCallStep).
- [x] Task: Definir callbacks e assinatura de `monitor_interaction` e `stream_interaction` em `agent_client.py`.

## Phase 2: Implementation
- [x] Task: Implementar extração de pensamento e ferramentas em `agent_client.py` com callbacks (`on_thought`, `on_step`).
- [x] Task: Atualizar `prototype_tui.py` para exibir pensamentos e passos em tempo real de forma elegante via Rich.
- [x] Task: Adicionar comando `/thoughts` na TUI para alternar exibição de pensamento (ativado por padrão).
- [x] Task: Ajustar compatibilidade e CLI em `main.py`.

## Phase 3: Verification & Tests
- [x] Task: Criar testes unitários para verificação de extração de pensamentos e passos em `test_agent_thinking.py`.
- [x] Task: Rodar suíte completa de testes e verificar conformidade.

# Specification: Agent Thinking Visibility

## Goal
Permitir que o usuário visualize em tempo real o pensamento, raciocínio e passos de execução (tools, comandos, buscas) do agente enquanto ele trabalha em interações assíncronas e no modo interativo (TUI).

## Acceptance Criteria
- [x] O cliente `AntigravityClient` é capaz de monitorar uma interação e extrair pensamentos (`thought` steps, `thought_summary` deltas, tags `<thought>` e `<thinking>`) e chamadas de ferramentas (`code_execution_call`, `mcp_server_tool_call`, `google_search_call`).
- [x] O loop interativo no `prototype_tui.py` exibe o raciocínio do agente visualmente enquanto ele processa a resposta, em vez de apenas uma mensagem estática de espera.
- [x] Usuário pode ativar ou desativar a exibição de pensamentos através do comando `/thoughts [on|off]` na interface TUI.
- [x] A exibição de pensamentos vem habilitada por padrão para que o usuário veja imediatamente o raciocínio.
- [x] O CLI e a suíte de testes cobrem a extração de pensamentos e o ciclo de vida do agente sem quebras.

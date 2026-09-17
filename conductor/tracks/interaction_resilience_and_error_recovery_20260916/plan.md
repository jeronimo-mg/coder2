# Implementation Plan: Interaction Resilience and Error Recovery

## Phase 1: Client & TUI Robustness Implementation
- [x] Task: Atualizar `agent_client.py` para:
  - Capturar e expor o `environment_id` da interação concluída (ou retorná-lo em conjunto com o output ou através do cliente).
  - Melhorar resiliência no stream de `monitor_interaction`: antes de levantar exceção de `api_error`, verificar com `interactions.get` se a interação no backend ainda está em execução ou concluída.
- [x] Task: Atualizar `prototype_tui.py` para:
  - Resetar `active_interaction_id = None` em caso de erro na execução/monitoramento.
  - Atualizar `active_environment_id` com o ID resolvido da interação concluída e sincronizar no `.sandbox`.
  - Implementar fallback automático com aviso ao usuário quando `send_follow_up` falhar com HTTP 400 (`Precondition check failed` / `invalid_request`), criando uma nova interação transparente (`create_interaction`).

## Phase 2: Verification and Automated Tests
- [x] Task: Criar arquivo de testes `test_error_recovery.py` cobrindo:
  - Recuperação de falha e reset de `active_interaction_id`.
  - Fallback automático de `send_follow_up` em caso de erro 400 de pré-condição.
  - Atualização do `environment_id` a partir da interação concluída.
- [x] Task: Executar a suíte de testes do projeto e garantir 100% de aprovação sem regressões.

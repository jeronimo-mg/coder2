# Specification: Interaction Resilience and Error Recovery

## Goal
Implementar resiliência no ciclo interativo (TUI e cliente Antigravity) para lidar adequadamente com erros transitórios da Google API ("Internal error encountered") e erros HTTP 400 de pré-condição ("Precondition check failed"), prevenindo que o estado da sessão seja corrompido.

## Acceptance Criteria
- [x] **Critério A (Limpeza de estado pós-falha):** Se `monitor_interaction` falhar com qualquer erro (ex: `api_error`, stream error, falha de timeout), `active_interaction_id` é resetado para `None` no loop do TUI, evitando tentativas subsequentes de continuar uma interação falhada.
- [x] **Critério B (Captura e atualização do `active_environment_id`):** Ao concluir uma interação com sucesso, o `environment_id` real retornado ou associado à interação concluída é capturado e atualizado em `active_environment_id` e no armazenamento de persistência (.sandbox).
- [x] **Critério C (Fallback automático no `send_follow_up`):** Se `send_follow_up` falhar com erro 400 ("Precondition check failed" ou "invalid_request"), o sistema captura a falha, invalida a continuação anterior corrompida e faz o fallback criando uma nova interação (`create_interaction`) preservando o contexto do usuário/Conductor.
- [x] **Critério D (Resiliência de stream em `agent_client.py`):** Em `monitor_interaction`, se o stream SSE receber um erro transitório mas a interação ainda estiver em andamento no backend, o cliente faz fallback para polling em vez de abortar prematuramente, e extrai o `environment_id` da interação concluída.
- [x] **Critério E (Testes e verificação):** Testes unitários novos comprovando o comportamento de recuperação de erro, fallback de pré-condição e preservação do estado.

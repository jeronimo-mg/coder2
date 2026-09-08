import os
from agent_client import AntigravityClient

# Certifique-se de definir a API Key
os.environ["GEMINI_API_KEY"] = "AIzaSyAVsJY7K2_R-egBHCxnXv27u8wXmPP9kw8"

try:
    client = AntigravityClient(project_name="meu_projeto")

    # 1. Inicia o arquivamento
    interaction_id = client.archive_sandbox()
    print(f"Arquivamento solicitado. ID: {interaction_id}")

    # 2. Aguarda a conclusão (Polling)
    print("Aguardando conclusão...")
    result = client.wait_for_archive(interaction_id)

    # 3. Verifica a saída
    print(f"Arquivamento concluído. Resultado: {result}")

except Exception as e:
    print(f"Erro na verificação: {e}")
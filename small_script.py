import os
from agent_client import AntigravityClient

# Configure sua API Key
os.environ["GEMINI_API_KEY"] = "AIzaSyAVsJY7K2_R-egBHCxnXv27u8wXmPP9kw8"

try:
    client = AntigravityClient(project_name="meu_projeto")
    print("Cliente inicializado.")

    # Inicia o arquivamento
    interaction_id = client.archive_sandbox()
    print(f"Arquivamento solicitado. Interaction ID: {interaction_id}")

except Exception as e:
    print(f"Erro: {e}")
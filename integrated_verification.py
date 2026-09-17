import os
from agent_client import AntigravityClient

os.environ["GEMINI_API_KEY"] = "AIzaSyAVsJY7K2_R-egBHCxnXv27u8wXmPP9kw8"

try:
    client = AntigravityClient(project_name="meu_projeto")

    # 1. Arquivar
    interaction_id = client.archive_sandbox()

    # 2. Polling
    print("Aguardando archive...")
    archive_url = client.wait_for_archive(interaction_id)

    # 3. Download
    print(f"URL recebida: {archive_url}")
    client.download_archive(archive_url, "sandbox_teste.zip")
    print("Download concluído.")

except Exception as e:
    print(f"Erro: {e}")
import os
from agent_client import AntigravityClient

# Configure sua API Key
os.environ["GEMINI_API_KEY"] = "AIzaSyAVsJY7K2_R-egBHCxnXv27u8wXmPP9kw8"

try:
    client = AntigravityClient(project_name="teste_env_id")
    print("Cliente inicializado.")

    # Inicia uma interação
    interaction = client.create_interaction("Olá, teste de env_id.")
    print(f"Interação criada. ID: {interaction.id}")

    # Verifica o arquivo de estado
    import json
    with open(".sandbox/teste_env_id.json", "r") as f:
        state = json.load(f)
        print(f"Estado salvo: {state}")
        if "environment_id" in state:
            print("SUCESSO: environment_id encontrado!")
        else:
            print("FALHA: environment_id não encontrado.")

except Exception as e:
    print(f"Erro na verificação: {e}")
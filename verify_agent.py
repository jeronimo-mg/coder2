import os
from agent_client import AntigravityClient

# Ensure API Key is set in your environment
os.environ["GEMINI_API_KEY"] = "AIzaSyAVsJY7K2_R-egBHCxnXv27u8wXmPP9kw8"

try:
    # Initialize for project 'my_test_proj'
    client = AntigravityClient(project_name="my_test_proj")
    print("Client initialized successfully.")

    # Try creating an interaction
    interaction = client.create_interaction("Hello, are you working?")
    print(f"Interaction created with ID: {interaction.id}")

    # Check if state was saved
    import os
    if os.path.exists(os.path.join(".sandbox", "my_test_proj.json")):
        print("Sandbox state saved successfully.")
    else:
        print("Sandbox state file not found.")
except Exception as e:
    print(f"Verification failed: {e}")
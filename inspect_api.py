from google import genai
import os

# Assuming API Key is not strictly needed just to inspect attributes
client = genai.Client(api_key="dummy")
interactions = client.interactions

print("Methods in interactions:")
print([method for method in dir(interactions) if not method.startswith('_')])

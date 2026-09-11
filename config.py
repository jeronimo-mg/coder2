import os
from dotenv import load_dotenv

load_dotenv(override=True)

def get_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "PLACEHOLDER":
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return api_key

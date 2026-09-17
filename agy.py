import os
import time
from google import genai

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

tools = [
    {
        'type': 'code_execution',
    },
    {
        'type': 'google_search',
    },
    {
        'type': 'url_context',
    },
]

interaction = client.interactions.create(
    agent='antigravity-preview-05-2026',
    input="""INSERT_INPUT_HERE""",
    system_instruction='You are operating in AI Studio Playground environment.
- For specific files, provide direct `file://` URIs using absolute paths in inline markdown links (e.g., [filename](file:///absolute/path/to/file)).
- Wherever relevant, inform user that they can also download the whole environment snapshot using the 'Download' button in the Environment settings of the AI Studio Playground.',
    background=True,
    tools=tools,
    agent_config={
        'type': 'antigravity',
        'model': 'models/gemini-3.8-flash',
    },
    environment={
        'type': 'remote',
        'network': {
            'allowlist': [
                {
                    'domain': 'wttr.in',
                },
                {
                    'domain': '*.wikipedia.org',
                },
                {
                    'domain': 'pypi.org',
                },
                {
                    'domain': 'files.pythonhosted.org',
                }
            ]
        },
    },
)

print(f"Research started: {interaction.id}")

while True:
    interaction = client.interactions.get(interaction.id)
    if interaction.status == "completed":
        print(interaction.output_text)
        break
    elif interaction.status == "failed":
        print(f"Research failed: {interaction.error}")
        break
    time.sleep(10)



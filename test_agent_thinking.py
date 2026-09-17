import unittest
from unittest.mock import MagicMock, patch
from agent_client import (
    AntigravityClient,
    extract_thought_from_step,
    extract_step_action,
    extract_output_text
)
from prototype_tui import parse_embedded_thoughts
from google.genai._gaos.types.interactions import (
    ModelOutputStep, TextContent, InteractionSseEventInteraction
)

class TestAgentThinking(unittest.TestCase):
    def test_extract_thought_from_object(self):
        mock_step = MagicMock()
        mock_step.type = 'thought'
        item1 = MagicMock()
        item1.text = "Planning the implementation"
        item2 = MagicMock()
        item2.text = "Checking file structure"
        mock_step.summary = [item1, item2]

        thought = extract_thought_from_step(mock_step)
        self.assertIn("Planning the implementation", thought)
        self.assertIn("Checking file structure", thought)

    def test_extract_thought_from_dict(self):
        dict_step = {
            'type': 'thought',
            'summary': [{'text': 'Step 1: Parse requirements'}]
        }
        thought = extract_thought_from_step(dict_step)
        self.assertEqual(thought, "Step 1: Parse requirements")

    def test_extract_thought_non_thought_step(self):
        step = {'type': 'model_output', 'content': [{'text': 'Hello'}]}
        self.assertIsNone(extract_thought_from_step(step))

    def test_extract_step_action_code_execution(self):
        mock_step = MagicMock()
        mock_step.type = 'code_execution_call'
        mock_step.arguments = MagicMock()
        mock_step.arguments.code = "ls -la /app"

        action = extract_step_action(mock_step)
        self.assertIsNotNone(action)
        self.assertEqual(action[0], 'code_execution')
        self.assertEqual(action[1], 'ls -la /app')

    def test_extract_step_action_mcp_tool(self):
        mock_step = MagicMock()
        mock_step.type = 'mcp_server_tool_call'
        mock_step.name = 'read_file'
        mock_step.arguments = {'path': 'test.txt'}

        action = extract_step_action(mock_step)
        self.assertIsNotNone(action)
        self.assertEqual(action[0], 'mcp_tool')
        self.assertIn('read_file', action[1])

    def test_extract_step_action_google_search(self):
        mock_step = MagicMock()
        mock_step.type = 'google_search_call'
        mock_step.arguments = MagicMock()
        mock_step.arguments.queries = ['python google genai api']

        action = extract_step_action(mock_step)
        self.assertIsNotNone(action)
        self.assertEqual(action[0], 'google_search')
        self.assertIn('python google genai api', action[1])

    def test_parse_embedded_thoughts(self):
        raw_text = "<thought>Thinking about solution...</thought>Here is the final response."
        thoughts, cleaned = parse_embedded_thoughts(raw_text)
        self.assertEqual(thoughts, ["Thinking about solution..."])
        self.assertEqual(cleaned, "Here is the final response.")

    def test_parse_embedded_thinking_tag(self):
        raw_text = "<thinking>Analyzing AST...</thinking>Code looks valid."
        thoughts, cleaned = parse_embedded_thoughts(raw_text)
        self.assertEqual(thoughts, ["Analyzing AST..."])
        self.assertEqual(cleaned, "Code looks valid.")

    def test_extract_output_text_from_sse_event_interaction(self):
        step = ModelOutputStep(type='model_output', content=[TextContent(type='text', text='Resposta correta!')])
        event_int = InteractionSseEventInteraction(id='123', status='completed', steps=[step])
        # Event interaction does not have output_text property
        self.assertFalse(hasattr(event_int, 'output_text'))
        # extract_output_text should successfully extract it from steps
        extracted = extract_output_text(event_int)
        self.assertEqual(extracted, "Resposta correta!")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_streaming_with_thought_and_response(self, mock_sleep, mock_get_api_key, mock_genai):
        mock_client = MagicMock()
        mock_genai.return_value = mock_client

        # Mock SSE stream with thought delta, text delta, and completion event
        event1 = MagicMock()
        event1.event_type = 'step.delta'
        event1.index = 0
        delta1 = MagicMock()
        delta1.type = 'thought_summary'
        delta1.content.text = "Pensando sobre o código..."
        event1.delta = delta1

        event2 = MagicMock()
        event2.event_type = 'step.delta'
        event2.index = 1
        delta2 = MagicMock()
        delta2.type = 'text'
        delta2.text = "Esta é a resposta final do agente."
        event2.delta = delta2

        event3 = MagicMock()
        event3.event_type = 'interaction.completed'
        step = ModelOutputStep(type='model_output', content=[TextContent(type='text', text='Esta é a resposta final do agente.')])
        event3.interaction = InteractionSseEventInteraction(id='123', status='completed', steps=[step])

        mock_stream = [event1, event2, event3]
        mock_client.interactions.get.return_value = mock_stream

        captured_thoughts = []
        client = AntigravityClient()
        result = client.monitor_interaction(
            "test_id",
            on_thought=lambda t, idx: captured_thoughts.append(t)
        )

        self.assertEqual(captured_thoughts, ["Pensando sobre o código..."])
        self.assertEqual(result, "Esta é a resposta final do agente.")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_polling_with_thoughts(self, mock_sleep, mock_get_api_key, mock_genai):
        mock_client = MagicMock()
        mock_genai.return_value = mock_client

        # Step 1: in_progress with a thought step and a code step
        mock_thought_step = MagicMock()
        mock_thought_step.type = 'thought'
        item = MagicMock()
        item.text = "Deciding next steps"
        mock_thought_step.summary = [item]

        mock_code_step = MagicMock()
        mock_code_step.type = 'code_execution_call'
        mock_code_step.arguments.code = "cat spec.md"

        interaction1 = MagicMock()
        interaction1.status = 'in_progress'
        interaction1.steps = [mock_thought_step, mock_code_step]

        # Step 2: completed
        interaction2 = MagicMock()
        interaction2.status = 'completed'
        interaction2.steps = [mock_thought_step, mock_code_step]
        interaction2.output_text = "Task finished successfully."

        # stream=True raises exception so it falls back to polling
        mock_client.interactions.get.side_effect = [Exception("Stream not available"), interaction1, interaction2]

        captured_thoughts = []
        captured_steps = []

        client = AntigravityClient()
        result = client.monitor_interaction(
            "test_id",
            on_thought=lambda t, idx: captured_thoughts.append((t, idx)),
            on_step=lambda act, det, idx: captured_steps.append((act, det, idx))
        )

        self.assertEqual(result, "Task finished successfully.")
        self.assertEqual(len(captured_thoughts), 1)
        self.assertEqual(captured_thoughts[0][0], "Deciding next steps")
        self.assertEqual(len(captured_steps), 1)
        self.assertEqual(captured_steps[0][0], "code_execution")
        self.assertEqual(captured_steps[0][1], "cat spec.md")

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from agent_client import (
    AntigravityClient,
    extract_thought_from_step,
    extract_step_action
)
from prototype_tui import parse_embedded_thoughts

class TestAgentThinking(unittest.TestCase):
    def test_extract_thought_from_object(self):
        # Mock ThoughtStep with summary containing TextContent-like items
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

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_with_thoughts(self, mock_sleep, mock_get_api_key, mock_genai):
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

        mock_client.interactions.get.side_effect = [interaction1, interaction2]

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

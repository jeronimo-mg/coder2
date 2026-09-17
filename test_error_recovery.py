import unittest
from unittest.mock import MagicMock, patch, call
from agent_client import AntigravityClient
from google.genai._gaos.types.interactions import (
    ModelOutputStep, TextContent, InteractionSseEventInteraction
)
import prototype_tui

class TestErrorRecoveryAndResilience(unittest.TestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    def test_environment_id_tracking_on_create(self, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_interaction = MagicMock()
        mock_interaction.id = "int_123"
        mock_interaction.environment_id = "env_abc_999"
        mock_client.interactions.create.return_value = mock_interaction

        client = AntigravityClient(project_name="default")
        interaction = client.create_interaction("Test prompt")

        self.assertEqual(client.last_interaction_id, "int_123")
        self.assertEqual(client.last_environment_id, "env_abc_999")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    def test_send_follow_up_uses_tracked_environment(self, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_int1 = MagicMock()
        mock_int1.id = "int_1"
        mock_int1.environment_id = "env_track_1"
        mock_client.interactions.create.return_value = mock_int1

        client = AntigravityClient()
        client.create_interaction("Step 1")

        mock_int2 = MagicMock()
        mock_int2.id = "int_2"
        mock_int2.environment_id = "env_track_1"
        mock_client.interactions.create.return_value = mock_int2

        # When environment_id is passed as None, send_follow_up uses tracked last_environment_id
        client.send_follow_up("int_1", None, "Step 2")

        mock_client.interactions.create.assert_called_with(
            agent='antigravity-preview-05-2026',
            input='Step 2',
            background=True,
            previous_interaction_id='int_1',
            environment='env_track_1'
        )

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_updates_environment_on_completion(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        # Interaction polled has environment_id and status completed
        mock_interaction = MagicMock()
        mock_interaction.status = "completed"
        mock_interaction.environment_id = "env_completed_456"
        mock_interaction.output_text = "All done!"

        # stream=True fails, falling back to polling
        mock_client.interactions.get.side_effect = [
            Exception("Stream not supported"),
            mock_interaction
        ]

        client = AntigravityClient()
        out = client.monitor_interaction("int_test")

        self.assertEqual(out, "All done!")
        self.assertEqual(client.last_environment_id, "env_completed_456")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_stream_error_falls_back_to_polling_if_backend_in_progress(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        # Stream event error occurs
        event_error = MagicMock()
        event_error.event_type = 'error'
        event_error.error = "Internal error encountered."

        # Backend check indicates it is actually still in_progress
        backend_in_progress = MagicMock()
        backend_in_progress.status = "in_progress"
        backend_in_progress.steps = []

        # Subsequent poll completed
        backend_completed = MagicMock()
        backend_completed.status = "completed"
        backend_completed.output_text = "Recovered after stream error!"
        backend_completed.environment_id = "env_recovered"

        # Call order:
        # 1. interactions.get(..., stream=True) -> yields [event_error]
        # 2. backend status check in stream error handler -> backend_in_progress
        # 3. polling loop -> backend_completed
        mock_client.interactions.get.side_effect = [
            [event_error],
            backend_in_progress,
            backend_completed
        ]

        client = AntigravityClient()
        out = client.monitor_interaction("int_stream_fail")

        self.assertEqual(out, "Recovered after stream error!")
        self.assertEqual(client.last_environment_id, "env_recovered")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_raises_when_backend_actually_failed(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_failed = MagicMock()
        mock_failed.status = "failed"
        mock_failed.error = "Internal error encountered."

        mock_client.interactions.get.side_effect = [
            Exception("Stream not available"),
            mock_failed
        ]

        client = AntigravityClient()
        with self.assertRaises(Exception) as ctx:
            client.monitor_interaction("int_failed")

        self.assertIn("Interaction failed: Internal error encountered.", str(ctx.exception))

    @patch('prototype_tui.AntigravityClient')
    @patch('prototype_tui.PromptSession')
    @patch('prototype_tui.get_mcp_manager', return_value=None)
    def test_tui_precondition_failed_fallback(self, mock_get_mcp, mock_prompt_session_cls, mock_antigravity_cls):
        # Test TUI loop:
        # Turn 1: normal create_interaction and completed output
        # Turn 2: send_follow_up throws 400 Precondition check failed -> should fallback to create_interaction
        # Turn 3: exit
        mock_client_inst = MagicMock()
        mock_antigravity_cls.return_value = mock_client_inst

        mock_session_inst = MagicMock()
        mock_session_inst.prompt.side_effect = ["Turn 1 message", "Turn 2 message", "exit"]
        mock_prompt_session_cls.return_value = mock_session_inst

        mock_int_turn1 = MagicMock()
        mock_int_turn1.id = "int_1"
        mock_int_turn1.environment_id = "env_1"

        mock_int_turn2 = MagicMock()
        mock_int_turn2.id = "int_2"
        mock_int_turn2.environment_id = "env_1"

        mock_client_inst.create_interaction.side_effect = [mock_int_turn1, mock_int_turn2]
        # send_follow_up raises 400 Precondition check failed error
        mock_client_inst.send_follow_up.side_effect = Exception("Error code: 400 - {'error': {'message': 'Precondition check failed.', 'code': 'invalid_request'}}")
        mock_client_inst.monitor_interaction.return_value = "Response OK"

        prototype_tui.run_tui()

        # Check that create_interaction was called twice: once for turn 1, and once as fallback for turn 2
        self.assertEqual(mock_client_inst.create_interaction.call_count, 2)
        # Check that send_follow_up was attempted once for turn 2
        self.assertEqual(mock_client_inst.send_follow_up.call_count, 1)

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient

class TestAgentClientLifecycle(unittest.TestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_completed(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_interaction = MagicMock()
        mock_interaction.status = "completed"
        mock_interaction.output_text = "result"
        
        mock_client.interactions.get.return_value = mock_interaction
        
        client = AntigravityClient()
        result = client.monitor_interaction("id_123")
        
        self.assertEqual(result, "result")
        mock_client.interactions.get.assert_called_with("id_123")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_monitor_interaction_failed(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_interaction = MagicMock()
        mock_interaction.status = "failed"
        mock_interaction.error = "something went wrong"
        
        mock_client.interactions.get.return_value = mock_interaction
        
        client = AntigravityClient()
        with self.assertRaises(Exception) as cm:
            client.monitor_interaction("id_123")
        self.assertEqual(str(cm.exception), "Interaction failed: something went wrong")

if __name__ == "__main__":
    unittest.main()

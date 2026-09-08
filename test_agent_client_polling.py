import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient
import time

class TestAgentClientPolling(unittest.TestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_wait_for_archive_success(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_interaction = MagicMock()
        mock_interaction.status = "completed"
        mock_interaction.output_text = "download_url"
        
        mock_client.interactions.get.return_value = mock_interaction
        
        client = AntigravityClient()
        result = client.wait_for_archive("id_123")
        
        self.assertEqual(result, "download_url")

    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('time.sleep', return_value=None)
    def test_wait_for_archive_timeout(self, mock_sleep, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_interaction = MagicMock()
        mock_interaction.status = "in_progress"
        
        mock_client.interactions.get.return_value = mock_interaction
        
        client = AntigravityClient()
        with patch('time.time', side_effect=[0, 1000]): # Fast forward time
            with self.assertRaises(Exception) as cm:
                client.wait_for_archive("id_123", timeout=10)
            self.assertEqual(str(cm.exception), "Archive creation timed out (5 minutes limit reached)")

if __name__ == "__main__":
    unittest.main()

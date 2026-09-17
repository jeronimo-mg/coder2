import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient

class TestAgentClient(unittest.TestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    def test_create_interaction(self, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        client = AntigravityClient()
        # Mocking the interaction directly with a concrete ID string
        mock_interaction = MagicMock()
        mock_interaction.id = "id_456"
        mock_client.interactions.create.return_value = mock_interaction
        
        client.create_interaction("test input")
        
        mock_client.interactions.create.assert_called_once_with(
            agent='antigravity-preview-05-2026',
            input='test input',
            background=True,
            environment={'type': 'remote'}
        )

if __name__ == "__main__":
    unittest.main()

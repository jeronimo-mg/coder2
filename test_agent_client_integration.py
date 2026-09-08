import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient

class TestAgentClientIntegration(unittest.TestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    @patch('agent_client.SandboxStorage')
    def test_create_interaction_saves_state(self, mock_storage_class, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        mock_interaction = MagicMock()
        mock_interaction.id = "id_456"
        mock_client.interactions.create.return_value = mock_interaction
        
        client = AntigravityClient(project_name="test_proj")
        client.create_interaction("test input")
        
        mock_storage.save_state.assert_called_with("test_proj", {"interaction_id": "id_456"})

if __name__ == "__main__":
    unittest.main()

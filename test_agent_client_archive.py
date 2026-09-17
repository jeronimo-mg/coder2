import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient

class TestAgentClientArchive(unittest.TestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    def test_archive_sandbox(self, mock_get_api_key, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_interaction = MagicMock()
        mock_interaction.id = "arch_123"
        mock_client.interactions.create.return_value = mock_interaction
        
        client = AntigravityClient(project_name="test_proj")
        interaction_id = client.archive_sandbox()
        
        self.assertEqual(interaction_id, "arch_123")
        mock_client.interactions.create.assert_called_with(
            agent='antigravity-preview-05-2026',
            input="archive sandbox",
            background=True,
            environment={'type': 'remote'}
        )

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient
import os

class TestAgentClientSnapshot(unittest.TestCase):
    @patch('agent_client.requests.get')
    @patch('agent_client.get_api_key', return_value='test_key')
    def test_download_snapshot(self, mock_get_api_key, mock_requests_get):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"tar_content"]
        mock_requests_get.return_value = mock_response
        
        client = AntigravityClient(project_name="test_proj")
        dest_dir = "test_extract"
        
        with patch("tarfile.open") as mock_tar:
            mock_tar_obj = MagicMock()
            mock_tar.return_value.__enter__.return_value = mock_tar_obj
            
            result = client.download_snapshot("env_123", dest_dir)
            
            self.assertEqual(result, dest_dir)
            mock_requests_get.assert_called_with(
                "https://generativelanguage.googleapis.com/v1beta/files/environment-env_123:download",
                params={"alt": "media"},
                headers={"x-goog-api-key": "test_key"},
                allow_redirects=True,
                stream=True
            )
            mock_tar_obj.extractall.assert_called_with(path=dest_dir)

if __name__ == "__main__":
    unittest.main()

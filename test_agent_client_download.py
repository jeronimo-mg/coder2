import unittest
from unittest.mock import MagicMock, patch
from agent_client import AntigravityClient

class TestAgentClientDownload(unittest.TestCase):
    @patch('agent_client.requests.get')
    @patch('agent_client.get_api_key', return_value='test_key')
    def test_download_archive(self, mock_get_api_key, mock_requests_get):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_requests_get.return_value = mock_response
        
        client = AntigravityClient(project_name="test_proj")
        dest = "test.zip"
        
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = client.download_archive("http://test.url", dest)
            
            self.assertEqual(result, dest)
            mock_requests_get.assert_called_with("http://test.url", stream=True)
            mock_file.write.assert_any_call(b"chunk1")
            mock_file.write.assert_any_call(b"chunk2")

if __name__ == "__main__":
    unittest.main()

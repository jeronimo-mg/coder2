import os
import tarfile
import tempfile
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

    @patch('agent_client.get_api_key', return_value='test_key')
    def test_download_snapshot_filters_system_dirs(self, mock_get_api_key):
        client = AntigravityClient(project_name="test_proj")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock tar archive containing system dirs and user code
            tar_path = os.path.join(tmpdir, "test_snapshot.tar")
            with tarfile.open(tar_path, "w") as tar:
                # Add a user file
                user_file = os.path.join(tmpdir, "main.py")
                with open(user_file, "w") as f:
                    f.write("print('hello world')")
                tar.add(user_file, arcname="main.py")

                # Add a system file that should be filtered out
                usr_dir = os.path.join(tmpdir, "usr_local_bin")
                os.makedirs(usr_dir, exist_ok=True)
                sys_file = os.path.join(usr_dir, "python")
                with open(sys_file, "w") as f:
                    f.write("# binary")
                tar.add(sys_file, arcname="usr/local/bin/python")

            # Mock requests.get returning the tar
            mock_resp = MagicMock()
            mock_resp.headers = {"content-length": str(os.path.getsize(tar_path))}
            with open(tar_path, "rb") as f:
                tar_bytes = f.read()
            mock_resp.iter_content.return_value = [tar_bytes]
            mock_resp.__enter__.return_value = mock_resp

            dest_dir = os.path.join(tmpdir, "extracted")
            with patch('agent_client.requests.get', return_value=mock_resp):
                client.download_snapshot("env_123", dest_dir)

            # Check that user file was extracted
            self.assertTrue(os.path.exists(os.path.join(dest_dir, "main.py")))
            # Check that usr/ system directory was NOT extracted
            self.assertFalse(os.path.exists(os.path.join(dest_dir, "usr")))

if __name__ == "__main__":
    unittest.main()

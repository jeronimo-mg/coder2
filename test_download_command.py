import unittest
from unittest.mock import MagicMock, patch
import io
import contextlib
from main import main

class TestDownloadCommand(unittest.TestCase):
    @patch('main.AntigravityClient')
    @patch('builtins.input', side_effect=['test_dest', 'n'])
    def test_download_command_cancelled(self, mock_input, mock_client_class):
        # Create dummy file to simulate conflict
        with open('test_dest', 'w') as f:
            f.write('dummy')
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["download", "test_proj"])
        
        self.assertIn("Download cancelled.", f.getvalue())
        import os
        os.remove('test_dest')

if __name__ == "__main__":
    unittest.main()

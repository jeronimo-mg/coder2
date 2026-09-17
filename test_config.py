import unittest
import os
from config import get_api_key

class TestConfig(unittest.TestCase):
    def test_get_api_key_success(self):
        os.environ["GEMINI_API_KEY"] = "test_key"
        self.assertEqual(get_api_key(), "test_key")
        del os.environ["GEMINI_API_KEY"]

    def test_get_api_key_failure(self):
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        with self.assertRaises(ValueError):
            get_api_key()

if __name__ == "__main__":
    unittest.main()

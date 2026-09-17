import unittest
import os
import json
from storage import SandboxStorage

class TestSandboxStorage(unittest.TestCase):
    def setUp(self):
        self.storage = SandboxStorage(base_dir=".test_sandbox")
        self.project = "test_project"

    def tearDown(self):
        path = os.path.join(".test_sandbox", f"{self.project}.json")
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(".test_sandbox"):
            os.rmdir(".test_sandbox")

    def test_save_load_state(self):
        state = {"env_id": "v1_123"}
        self.storage.save_state(self.project, state)
        loaded = self.storage.load_state(self.project)
        self.assertEqual(loaded, state)

    def test_load_nonexistent(self):
        loaded = self.storage.load_state("nonexistent")
        self.assertIsNone(loaded)

if __name__ == "__main__":
    unittest.main()

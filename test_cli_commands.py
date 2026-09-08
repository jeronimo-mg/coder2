import unittest
import io
import contextlib
import os
from main import main

class TestCLICommands(unittest.TestCase):
    def test_init_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["init", "test_project"])
        self.assertEqual(f.getvalue(), "Project 'test_project' sandbox initialized.\n")
        self.assertTrue(os.path.exists(os.path.join(".sandbox", "test_project.json")))

    def test_cleanup_command(self):
        # First init to ensure cleanup works
        main(["init", "test_cleanup"])
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["cleanup", "test_cleanup"])
        self.assertEqual(f.getvalue(), "Project 'test_cleanup' sandbox cleaned.\n")
        self.assertFalse(os.path.exists(os.path.join(".sandbox", "test_cleanup.json")))

    def tearDown(self):
        # Clean up files created during test
        for name in ["test_project", "test_cleanup"]:
            path = os.path.join(".sandbox", f"{name}.json")
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    unittest.main()

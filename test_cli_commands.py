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

    def test_conductor_status_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["conductor", "status"])
        output = f.getvalue()
        self.assertIn("CONDUCTOR STATUS OVERVIEW", output)
        self.assertIn("Conductor Plugin", output)

    def test_conductor_plugin_info_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["conductor", "plugin-info"])
        output = f.getvalue()
        self.assertIn("Conductor Plugin", output)

    def test_conductor_skills_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["conductor", "skills"])
        output = f.getvalue()
        self.assertIn("conductor-setup", output)
        self.assertIn("conductor-new-track", output)

    def test_plugins_list_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main(["plugins", "list"])
        output = f.getvalue()
        self.assertIn("conductor", output)

    def tearDown(self):
        # Clean up files created during test
        for name in ["test_project", "test_cleanup"]:
            path = os.path.join(".sandbox", f"{name}.json")
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    unittest.main()

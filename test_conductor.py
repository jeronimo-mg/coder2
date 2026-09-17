import unittest
import os
import tempfile
import shutil
from conductor_manager import ConductorManager

class TestConductorManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = ConductorManager(project_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_uninitialized(self):
        self.assertFalse(self.manager.is_initialized())
        status = self.manager.get_status()
        self.assertFalse(status["initialized"])
        self.assertIn("not initialized", self.manager.format_status_report().lower())

    def test_setup_and_status(self):
        self.manager.setup(
            project_name="TestProject",
            description="Testing Conductor",
            tech_stack="Python, unittest"
        )
        self.assertTrue(self.manager.is_initialized())
        self.assertTrue(os.path.exists(self.manager.index_file))
        self.assertTrue(os.path.exists(self.manager.tracks_file))

        status = self.manager.get_status()
        self.assertTrue(status["initialized"])
        self.assertEqual(status["total_tracks"], 0)

    def test_create_track(self):
        self.manager.setup()
        track = self.manager.create_track(
            name="Feature X",
            description="Testing track creation",
            track_type="feature"
        )
        self.assertIn("track_id", track)
        self.assertTrue(os.path.exists(track["path"]))
        self.assertTrue(os.path.exists(os.path.join(track["path"], "plan.md")))
        self.assertTrue(os.path.exists(os.path.join(track["path"], "spec.md")))

        tracks = self.manager.list_tracks()
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["name"], "Feature X")
        self.assertEqual(tracks[0]["status"], "pending")

        status = self.manager.get_status()
        self.assertEqual(status["total_tracks"], 1)
        self.assertEqual(status["pending_tracks"], 1)
        self.assertGreater(status["total_tasks"], 0)

    def test_get_agent_context(self):
        self.manager.setup(
            project_name="TestProject",
            description="A test product description",
            tech_stack="Python, google-genai"
        )
        context = self.manager.get_agent_context()
        self.assertIn("TestProject", context)
        self.assertIn("Python, google-genai", context)
        self.assertIn("Conductor Plugin", context)

    def test_plugin_detection_and_skills(self):
        # Real workspace plugin checks
        real_mgr = ConductorManager()
        self.assertTrue(real_mgr.is_plugin_installed())
        info = real_mgr.get_plugin_info()
        self.assertTrue(info["installed"])
        self.assertEqual(info["name"], "conductor")
        self.assertEqual(info["type"], "plugin")
        self.assertGreater(info["skills_count"], 0)

        skills = real_mgr.list_plugin_skills()
        skill_ids = [s["id"] for s in skills]
        self.assertIn("conductor-setup", skill_ids)
        self.assertIn("conductor-new-track", skill_ids)
        self.assertIn("conductor-implement", skill_ids)

        rules = real_mgr.get_plugin_rules()
        self.assertIn("Native Modal Prompts", rules)

    def test_real_workspace_conductor(self):
        # Test against current coder2 directory
        real_mgr = ConductorManager()
        self.assertTrue(real_mgr.is_initialized())
        status = real_mgr.get_status()
        self.assertTrue(status["initialized"])
        self.assertGreater(status["total_tracks"], 0)
        self.assertIn("Conductor Integration", [t["name"] for t in status["tracks"]])

if __name__ == "__main__":
    unittest.main()

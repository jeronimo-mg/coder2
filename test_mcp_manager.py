import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import os
from mcp_manager import MCPHostManager

class TestMCPHostManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = MCPHostManager("dummy_server.js")

    def test_initial_state(self):
        self.assertFalse(self.manager.is_connected)
        self.assertIsNone(self.manager.session)
        self.assertIsNone(self.manager.env)
        self.assertIsNone(self.manager.cwd)

    @patch("mcp_manager.stdio_client")
    @patch("mcp_manager.ClientSession")
    async def test_connect_success(self, mock_client_session_cls, mock_stdio_client):
        # Mock stdio transport
        mock_transport = (MagicMock(), MagicMock())
        mock_stdio_ctx = AsyncMock()
        mock_stdio_ctx.__aenter__.return_value = mock_transport
        mock_stdio_client.return_value = mock_stdio_ctx

        # Mock ClientSession
        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_client_session_cls.return_value = mock_session_ctx

        await self.manager.connect()

        self.assertTrue(self.manager.is_connected)
        mock_session.initialize.assert_awaited_once()

        # Connect again should be a no-op
        await self.manager.connect()
        mock_session.initialize.assert_awaited_once()

    @patch("mcp_manager.stdio_client")
    async def test_connect_failure_cleanup(self, mock_stdio_client):
        mock_stdio_client.side_effect = RuntimeError("Failed to start process")

        with self.assertRaises(RuntimeError):
            await self.manager.connect()

        self.assertFalse(self.manager.is_connected)
        self.assertIsNone(self.manager.session)

    @patch("mcp_manager.stdio_client")
    @patch("mcp_manager.ClientSession")
    async def test_disconnect(self, mock_client_session_cls, mock_stdio_client):
        mock_transport = (MagicMock(), MagicMock())
        mock_stdio_ctx = AsyncMock()
        mock_stdio_ctx.__aenter__.return_value = mock_transport
        mock_stdio_client.return_value = mock_stdio_ctx

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_client_session_cls.return_value = mock_session_ctx

        await self.manager.connect()
        self.assertTrue(self.manager.is_connected)

        await self.manager.disconnect()
        self.assertFalse(self.manager.is_connected)
        self.assertIsNone(self.manager.session)

    async def test_list_tools_not_connected(self):
        with self.assertRaises(RuntimeError):
            await self.manager.list_tools()

    async def test_call_tool_not_connected(self):
        with self.assertRaises(RuntimeError):
            await self.manager.call_tool("some_tool", {})

    @patch("mcp_manager.stdio_client")
    @patch("mcp_manager.ClientSession")
    async def test_list_tools_connected(self, mock_client_session_cls, mock_stdio_client):
        mock_transport = (MagicMock(), MagicMock())
        mock_stdio_ctx = AsyncMock()
        mock_stdio_ctx.__aenter__.return_value = mock_transport
        mock_stdio_client.return_value = mock_stdio_ctx

        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=["tool1", "tool2"])
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_client_session_cls.return_value = mock_session_ctx

        await self.manager.connect()
        tools = await self.manager.list_tools()
        self.assertEqual(tools, ["tool1", "tool2"])

    @patch("mcp_manager.stdio_client")
    @patch("mcp_manager.ClientSession")
    async def test_call_tool_connected(self, mock_client_session_cls, mock_stdio_client):
        mock_transport = (MagicMock(), MagicMock())
        mock_stdio_ctx = AsyncMock()
        mock_stdio_ctx.__aenter__.return_value = mock_transport
        mock_stdio_client.return_value = mock_stdio_ctx

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value={"result": "success"})
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_client_session_cls.return_value = mock_session_ctx

        await self.manager.connect()
        res = await self.manager.call_tool("my_tool", {"arg": 1})
        self.assertEqual(res, {"result": "success"})
        mock_session.call_tool.assert_awaited_once_with("my_tool", {"arg": 1})

    def test_custom_command_and_args(self):
        mgr = MCPHostManager("script.py", command="python3", args=["--flag"])
        self.assertEqual(mgr.command, "python3")
        self.assertEqual(mgr.args, ["script.py", "--flag"])

        mgr_no_script = MCPHostManager(command="npx", args=["-y", "pkg"])
        self.assertEqual(mgr_no_script.args, ["-y", "pkg"])

    @patch("os.path.exists")
    def test_create_desktop_commander_custom_path(self, mock_exists):
        mock_exists.return_value = True
        mgr = MCPHostManager.create_desktop_commander(custom_path="/path/to/dist/index.js", env={"CUSTOM_VAR": "1"})
        self.assertEqual(mgr.command, "node")
        self.assertIn("/path/to/dist/index.js", mgr.args)
        self.assertIn("--no-onboarding", mgr.args)
        self.assertEqual(mgr.env["MCP_DXT"], "true")
        self.assertEqual(mgr.env["NODE_ENV"], "production")
        self.assertEqual(mgr.env["CUSTOM_VAR"], "1")

    @patch("os.path.exists")
    def test_create_desktop_commander_local_discovery(self, mock_exists):
        def exists_side_effect(path):
            return "desktop-commander/dist/index.js" in path
        mock_exists.side_effect = exists_side_effect

        mgr = MCPHostManager.create_desktop_commander(project_dir="/my/project", command="custom-node")
        self.assertEqual(mgr.command, "custom-node")
        self.assertTrue(any("dist/index.js" in arg for arg in mgr.args))
        self.assertIn("--no-onboarding", mgr.args)

    @patch("os.path.exists", return_value=False)
    def test_create_desktop_commander_npx_fallback(self, mock_exists):
        mgr = MCPHostManager.create_desktop_commander()
        self.assertEqual(mgr.command, "npx")
        self.assertEqual(mgr.args, ["-y", "@wonderwhy-er/desktop-commander@latest", "--no-onboarding"])
        self.assertEqual(mgr.env["MCP_DXT"], "true")

    @patch("os.path.exists", return_value=False)
    def test_create_desktop_commander_npx_disabled_raises(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            MCPHostManager.create_desktop_commander(use_npx=False)

if __name__ == "__main__":
    unittest.main()

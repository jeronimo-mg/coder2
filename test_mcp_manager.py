import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from mcp_manager import MCPHostManager

class TestMCPHostManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = MCPHostManager("dummy_server.js")

    def test_initial_state(self):
        self.assertFalse(self.manager.is_connected)
        self.assertIsNone(self.manager.session)

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

    def test_custom_command_and_args(self):
        mgr = MCPHostManager("script.py", command="python3", args=["--flag"])
        self.assertEqual(mgr.command, "python3")
        self.assertEqual(mgr.args, ["script.py", "--flag"])

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from agent_client import AntigravityClient
from mcp_manager import MCPHostManager

class TestAgentClientMCP(unittest.IsolatedAsyncioTestCase):
    @patch('agent_client.genai.Client')
    @patch('agent_client.get_api_key', return_value='test_key')
    def setUp(self, mock_get_api_key, mock_genai):
        self.client = AntigravityClient(project_name="test_mcp")

    def test_default_mcp_manager_is_none(self):
        self.assertIsNone(self.client.mcp_manager)

    def test_set_mcp_manager(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        self.client.set_mcp_manager(mock_mgr)
        self.assertEqual(self.client.mcp_manager, mock_mgr)

    @patch('mcp_manager.MCPHostManager.create_desktop_commander')
    def test_attach_desktop_commander(self, mock_create):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_create.return_value = mock_mgr

        res = self.client.attach_desktop_commander(project_dir="/tmp/test")
        mock_create.assert_called_once_with(project_dir="/tmp/test")
        self.assertEqual(res, mock_mgr)
        self.assertEqual(self.client.mcp_manager, mock_mgr)

    async def test_get_mcp_tools_without_manager(self):
        tools = await self.client.get_mcp_tools()
        self.assertEqual(tools, [])

    async def test_get_mcp_tools_with_manager_not_connected(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.is_connected = False
        mock_mgr.connect = AsyncMock()
        mock_mgr.list_tools = AsyncMock(return_value=MagicMock(tools=["tool1", "tool2"]))
        self.client.set_mcp_manager(mock_mgr)

        tools_resp = await self.client.get_mcp_tools()
        mock_mgr.connect.assert_awaited_once()
        mock_mgr.list_tools.assert_awaited_once()
        self.assertEqual(tools_resp.tools, ["tool1", "tool2"])

    async def test_get_mcp_tools_with_manager_already_connected(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.is_connected = True
        mock_mgr.connect = AsyncMock()
        mock_mgr.list_tools = AsyncMock(return_value=MagicMock(tools=["t1"]))
        self.client.set_mcp_manager(mock_mgr)

        tools_resp = await self.client.get_mcp_tools()
        mock_mgr.connect.assert_not_awaited()
        mock_mgr.list_tools.assert_awaited_once()
        self.assertEqual(tools_resp.tools, ["t1"])

    async def test_call_mcp_tool_without_manager(self):
        with self.assertRaises(RuntimeError):
            await self.client.call_mcp_tool("test_tool", {"arg": "val"})

    async def test_call_mcp_tool_with_manager(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.is_connected = True
        mock_mgr.call_tool = AsyncMock(return_value={"status": "ok"})
        self.client.set_mcp_manager(mock_mgr)

        res = await self.client.call_mcp_tool("test_tool", {"arg": "val"})
        mock_mgr.call_tool.assert_awaited_once_with("test_tool", {"arg": "val"})
        self.assertEqual(res, {"status": "ok"})

    def test_sync_helpers(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.is_connected = True
        mock_mgr.list_tools = AsyncMock(return_value=MagicMock(tools=["sync_tool"]))
        mock_mgr.call_tool = AsyncMock(return_value="sync_result")
        self.client.set_mcp_manager(mock_mgr)

        tools = self.client.get_mcp_tools_sync()
        self.assertEqual(tools.tools, ["sync_tool"])

        res = self.client.call_mcp_tool_sync("sync_tool", {})
        self.assertEqual(res, "sync_result")

if __name__ == "__main__":
    unittest.main()

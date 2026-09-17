import unittest
from unittest.mock import MagicMock
from mcp_manager import format_mcp_tools_context, get_mcp_tools_table
from rich.table import Table

class MockTool:
    def __init__(self, name, description=None, input_schema=None):
        self.name = name
        self.description = description
        self.inputSchema = input_schema or {}

class TestMCPDiscovery(unittest.TestCase):
    def test_format_mcp_tools_context_empty(self):
        context = format_mcp_tools_context([])
        self.assertEqual(context, "")

        context_none = format_mcp_tools_context(None)
        self.assertEqual(context_none, "")

    def test_format_mcp_tools_context_with_tools(self):
        tools = [
            MockTool(
                name="read_file",
                description="Read contents from local filesystem",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to file"}
                    },
                    "required": ["path"]
                }
            ),
            MockTool(
                name="list_directory",
                description="List directory files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    }
                }
            ),
            # Also test dict-based tool
            {
                "name": "dict_tool",
                "description": "Dict-based tool description",
                "inputSchema": {"properties": {"key": {"type": "string"}}}
            }
        ]
        context = format_mcp_tools_context(tools)
        self.assertIn("## Local MCP Tools (DesktopCommander)", context)
        self.assertIn("read_file", context)
        self.assertIn("Read contents from local filesystem", context)
        self.assertIn("path", context)
        self.assertIn("list_directory", context)
        self.assertIn("dict_tool", context)

    def test_get_mcp_tools_table(self):
        tools = [
            MockTool(
                name="start_process",
                description="Start a new terminal process",
                input_schema={"properties": {"command": {"type": "string"}}}
            ),
            {
                "name": "raw_tool",
                "description": "",
                "inputSchema": {}
            }
        ]
        table = get_mcp_tools_table(tools)
        self.assertIsInstance(table, Table)
        self.assertEqual(table.title, "DesktopCommander MCP Tools")
        self.assertEqual(len(table.rows), 2)

    def test_get_mcp_tools_table_empty(self):
        table_empty = get_mcp_tools_table([])
        self.assertIsInstance(table_empty, Table)
        self.assertEqual(len(table_empty.rows), 1)

        table_none = get_mcp_tools_table(None)
        self.assertIsInstance(table_none, Table)
        self.assertEqual(len(table_none.rows), 1)

if __name__ == "__main__":
    unittest.main()

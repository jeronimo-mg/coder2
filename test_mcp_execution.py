import asyncio
from prototype_tui import handle_chat_mcp_execution
import unittest
from unittest.mock import AsyncMock, MagicMock
from mcp_manager import (
    parse_mcp_tool_calls,
    format_mcp_tool_result,
    execute_mcp_tool_calls,
    strip_mcp_tags,
    MCPHostManager
)

class TestMCPExecution(unittest.IsolatedAsyncioTestCase):
    def test_parse_mcp_tool_calls_empty(self):
        self.assertEqual(parse_mcp_tool_calls(""), [])
        self.assertEqual(parse_mcp_tool_calls(None), [])
        self.assertEqual(parse_mcp_tool_calls("Hello, I am standard text."), [])

    def test_parse_mcp_tool_calls_valid_xml(self):
        text = '''
        I will read the file for you:
        <mcp_call name="read_file">
        {"path": "hello.py"}
        </mcp_call>
        '''
        calls = parse_mcp_tool_calls(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "read_file")
        self.assertEqual(calls[0]["arguments"], {"path": "hello.py"})

    def test_parse_mcp_tool_calls_multiple(self):
        text = '''
        <mcp_call name="tool_one">{"a": 1}</mcp_call>
        Some explanation
        <mcp_call name="tool_two">{"b": "test"}</mcp_call>
        '''
        calls = parse_mcp_tool_calls(text)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["name"], "tool_one")
        self.assertEqual(calls[0]["arguments"], {"a": 1})
        self.assertEqual(calls[1]["name"], "tool_two")
        self.assertEqual(calls[1]["arguments"], {"b": "test"})

    def test_parse_mcp_tool_calls_invalid_json(self):
        text = '<mcp_call name="bad_tool">{invalid json}</mcp_call>'
        calls = parse_mcp_tool_calls(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "bad_tool")
        self.assertEqual(calls[0]["arguments"], {})
        self.assertIn("error", calls[0])

    def test_format_mcp_tool_result_success(self):
        res = format_mcp_tool_result("read_file", {"content": "print('hello')"})
        self.assertIn('name="read_file"', res)
        self.assertIn('status="success"', res)
        self.assertIn("print('hello')", res)
        self.assertIn("</mcp_result>", res)

    def test_format_mcp_tool_result_error(self):
        res = format_mcp_tool_result("read_file", None, error="File not found")
        self.assertIn('<mcp_result name="read_file" status="error">', res)
        self.assertIn("File not found", res)

    def test_strip_mcp_tags(self):
        text = 'Hello <mcp_call name="read_file">{"path": "x"}</mcp_call> world'
        self.assertEqual(strip_mcp_tags(text), "Hello  world")
        self.assertEqual(strip_mcp_tags(None), "")

    async def test_execute_mcp_tool_calls_success(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.call_tool = AsyncMock(return_value={"files": ["a.txt"]})

        calls = [{"name": "list_directory", "arguments": {"path": "."}}]
        results = await execute_mcp_tool_calls(mock_mgr, calls)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "list_directory")
        self.assertEqual(results[0]["result"], {"files": ["a.txt"]})
        self.assertIsNone(results[0]["error"])
        mock_mgr.call_tool.assert_awaited_once_with("list_directory", {"path": "."})

    async def test_execute_mcp_tool_calls_failure(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.call_tool = AsyncMock(side_effect=RuntimeError("Permission denied"))

        calls = [{"name": "delete_file", "arguments": {"path": "/etc/passwd"}}]
        results = await execute_mcp_tool_calls(mock_mgr, calls)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "delete_file")
        self.assertIsNone(results[0]["result"])
        self.assertEqual(results[0]["error"], "Permission denied")


    async def test_handle_chat_mcp_execution_loop(self):
        mock_mgr = MagicMock(spec=MCPHostManager)
        mock_mgr.call_tool = AsyncMock(return_value={"status": "healthy"})

        mock_client = MagicMock()
        mock_followup = MagicMock()
        mock_followup.id = "new_int_123"
        mock_client.send_follow_up.return_value = mock_followup
        mock_client.monitor_interaction.return_value = "All operations completed successfully."

        raw_output = '<mcp_call name="check_health">{}</mcp_call>'
        loop = asyncio.get_event_loop()

        final_raw, final_id, clean_resp = handle_chat_mcp_execution(
            raw_output=raw_output,
            mcp_mgr=mock_mgr,
            client=mock_client,
            active_interaction_id="orig_int_1",
            active_environment_id="env_1",
            loop=loop,
            handle_thought=lambda t, i: None,
            handle_step=lambda a, d, i: None,
            show_thoughts=False,
            max_tool_turns=2
        )

        mock_mgr.call_tool.assert_awaited_once_with("check_health", {})
        mock_client.send_follow_up.assert_called_once()
        self.assertEqual(final_id, "new_int_123")
        self.assertEqual(clean_resp, "All operations completed successfully.")

if __name__ == "__main__":
    unittest.main()

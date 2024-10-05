import unittest
from unittest.mock import patch, MagicMock
import json
from prompt_doctor.debug_tool import DebugTool


class TestDebugTool(unittest.TestCase):
    def setUp(self):
        self.debug_tool = DebugTool()

    def test_initialization(self):
        self.assertIsNotNone(self.debug_tool.app)
        self.assertIsNotNone(self.debug_tool.prompt_manager)

    @patch("prompt_doctor.debug_tool.threading.Thread")
    @patch("prompt_doctor.debug_tool.webbrowser.open")
    @patch("builtins.input")
    def test_run(self, mock_input, mock_webbrowser, mock_thread):
        mock_input.return_value = ""
        self.debug_tool.prompt_manager.list_versions = MagicMock(return_value=[1])
        self.debug_tool.prompt_manager.get_prompt = MagicMock(
            return_value=MagicMock(render=lambda x: "Rendered prompt")
        )

        result = self.debug_tool.run("test_prompt", "Initial prompt", {"key": "value"})

        mock_thread.assert_called_once()
        mock_webbrowser.assert_called_once_with("http://127.0.0.1:5000")
        self.assertEqual(result, "Rendered prompt")

    def test_debug_prompt_get(self):
        with self.debug_tool.app.test_client() as client:
            response = client.get("/")
            self.assertEqual(response.status_code, 200)

    @patch("prompt_doctor.debug_tool.call_llm_api")
    def test_debug_prompt_post(self, mock_call_llm_api):
        mock_call_llm_api.return_value = "API response"
        self.debug_tool.prompt_manager.save_prompt = MagicMock(return_value=2)
        self.debug_tool.prompt_manager.render_prompt = MagicMock(
            return_value="Rendered prompt"
        )

        with self.debug_tool.app.test_client() as client:
            response = client.post(
                "/",
                data={
                    "prompt_id": "test_prompt",
                    "prompt_text": "Test prompt",
                    "context": json.dumps({"key": "value"}),
                },
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["rendered_prompt"], "Rendered prompt")
            self.assertEqual(data["version"], 2)
            self.assertEqual(data["api_response"], "API response")


if __name__ == "__main__":
    unittest.main()
